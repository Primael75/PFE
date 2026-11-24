"""Train MobileNetV3-Large in two stages (fine-tuning).

Stage 1: everything is frozen except the last layer (fast).
Stage 2: the last N blocks are unfrozen, with a small learning rate.

Example (quick trial on CPU), from the repository root:
    uv run python -m agritech.diagnosis.train --data data_ccmt --out runs/trial \\
        --epochs-head 2 --epochs-ft 0 --subset 100

The test split is NEVER read here: only train.csv and val.csv.
"""

import argparse
import csv
import json
import logging
import random
import time
from collections import Counter, defaultdict
from pathlib import Path

import torch
from torch import nn
from torch.utils.data import DataLoader

from agritech.core.logging_config import configure_logging
from agritech.data.common import load_meta, read_manifest, seed_everything
from agritech.diagnosis.model import (
    ARCH,
    IMAGENET_MEAN,
    IMAGENET_STD,
    ManifestDataset,
    build_model,
    eval_transform,
    pick_device,
    train_transform,
)

logger = logging.getLogger(__name__)


def subset_rows(rows: list[dict], per_class: int, seed: int) -> list[dict]:
    """At most per_class rows of each class, drawn at random (quick trials)."""
    rng = random.Random(seed)
    by = defaultdict(list)
    for r in rows:
        by[r["label"]].append(r)
    out = []
    for v in by.values():
        rng.shuffle(v)
        out += v[:per_class]
    return out


def set_mode(model: nn.Module, stage: int, n_unfreeze: int) -> None:
    """Choose which layers learn, and which keep their normalisation statistics frozen."""
    for p in model.parameters():
        p.requires_grad = False
    for p in model.classifier[3].parameters():
        p.requires_grad = True
    model.eval()
    model.classifier[3].train()
    if stage == 2 and n_unfreeze > 0:
        for blk in model.features[-n_unfreeze:]:
            for p in blk.parameters():
                p.requires_grad = True
            blk.train()
        model.classifier.train()
        for p in model.classifier.parameters():
            p.requires_grad = True


def run_epoch(model, loader, device, criterion, optimizer=None) -> tuple[float, float]:
    """One pass over loader; trains when an optimizer is given. Returns (loss, accuracy)."""
    total_loss = correct = n = 0
    train = optimizer is not None
    with torch.set_grad_enabled(train):
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            loss = criterion(out, y)
            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * len(y)
            correct += (out.argmax(1) == y).sum().item()
            n += len(y)
    return total_loss / n, correct / n


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--data", required=True, type=Path, help="folder written by prepare_data"
    )
    ap.add_argument(
        "--root", type=Path, help="override the photo folder (useful on Colab)"
    )
    ap.add_argument("--out", default=Path("runs/run1"), type=Path)
    ap.add_argument("--weights", default="imagenet", choices=["imagenet", "none"])
    ap.add_argument("--epochs-head", type=int, default=5)
    ap.add_argument("--epochs-ft", type=int, default=5)
    ap.add_argument(
        "--unfreeze-last", type=int, default=3, help="blocks unfrozen in stage 2"
    )
    ap.add_argument("--lr-head", type=float, default=1e-3)
    ap.add_argument("--lr-ft", type=float, default=1e-4)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--img", type=int, default=224)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument(
        "--subset", type=int, default=0, help="max photos per class (quick trial)"
    )
    ap.add_argument("--no-class-weights", action="store_true")
    ap.add_argument(
        "--bn-momentum",
        type=float,
        default=None,
        help="BatchNorm statistics update rate (trials from random weights: 0.1)",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--device", default="auto")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> float:
    """Train, save best.pt, metrics.csv and config.json; return the best validation accuracy."""
    args = parse_args(argv)
    seed_everything(args.seed)
    torch.manual_seed(args.seed)
    device = pick_device(args.device)
    _, root, classes = load_meta(args.data, args.root)
    train_rows = read_manifest(args.data / "train.csv")
    val_rows = read_manifest(args.data / "val.csv")
    if args.subset:
        train_rows = subset_rows(train_rows, args.subset, args.seed)
        val_rows = subset_rows(val_rows, args.subset, args.seed)
    logger.info(
        "Device: %s | classes: %d | train: %d | validation: %d",
        device,
        len(classes),
        len(train_rows),
        len(val_rows),
    )

    ds_tr = ManifestDataset(train_rows, root, classes, train_transform(args.img))
    ds_va = ManifestDataset(val_rows, root, classes, eval_transform(args.img))
    dl_tr = DataLoader(
        ds_tr,
        batch_size=args.batch,
        shuffle=True,
        num_workers=args.workers,
        drop_last=len(ds_tr) > args.batch,
    )
    dl_va = DataLoader(
        ds_va, batch_size=args.batch, shuffle=False, num_workers=args.workers
    )

    model = build_model(len(classes), args.weights).to(device)
    if args.bn_momentum is not None:
        for mod in model.modules():
            if isinstance(mod, nn.BatchNorm2d):
                mod.momentum = args.bn_momentum

    # Class weights compensate the imbalance (from 142 to 1,814 training photos per class).
    weights = None
    if not args.no_class_weights:
        cnt = Counter(r["label"] for r in train_rows)
        weights = torch.tensor(
            [len(train_rows) / (len(classes) * max(cnt[c], 1)) for c in classes],
            dtype=torch.float32,
        ).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)

    args.out.mkdir(parents=True, exist_ok=True)
    log_path = args.out / "metrics.csv"
    with open(log_path, "w", newline="") as f:
        csv.writer(f).writerow(
            [
                "epoch",
                "stage",
                "train_loss",
                "train_acc",
                "val_loss",
                "val_acc",
                "seconds",
            ]
        )

    best = -1.0
    epoch = 0
    for stage, n_ep, lr in [
        (1, args.epochs_head, args.lr_head),
        (2, args.epochs_ft, args.lr_ft),
    ]:
        if n_ep <= 0:
            continue
        set_mode(model, stage, args.unfreeze_last)
        params = [p for p in model.parameters() if p.requires_grad]
        logger.info(
            "Stage %d: %d trained parameters, %d epochs",
            stage,
            sum(p.numel() for p in params),
            n_ep,
        )
        opt = torch.optim.AdamW(params, lr=lr, weight_decay=1e-4)
        for _ in range(n_ep):
            epoch += 1
            t0 = time.time()
            set_mode(model, stage, args.unfreeze_last)
            tl, ta = run_epoch(model, dl_tr, device, criterion, opt)
            model.eval()
            vl, va = run_epoch(model, dl_va, device, criterion)
            sec = time.time() - t0
            logger.info(
                "epoch %2d | train %.3f / %.3f | validation %.3f / %.3f | %.0f s",
                epoch,
                tl,
                ta,
                vl,
                va,
                sec,
            )
            with open(log_path, "a", newline="") as f:
                csv.writer(f).writerow(
                    [
                        epoch,
                        stage,
                        f"{tl:.4f}",
                        f"{ta:.4f}",
                        f"{vl:.4f}",
                        f"{va:.4f}",
                        f"{sec:.1f}",
                    ]
                )
            if va > best:
                best = va
                torch.save(
                    {
                        "state_dict": model.state_dict(),
                        "classes": classes,
                        "img_size": args.img,
                        "mean": IMAGENET_MEAN,
                        "std": IMAGENET_STD,
                        "arch": ARCH,
                        "val_acc": va,
                        "epoch": epoch,
                    },
                    args.out / "best.pt",
                )

    config = {
        "arch": ARCH,
        "classes": classes,
        "preprocessing": {
            "colour_order": "RGB",
            "exif_rotation_applied": True,
            "resize": f"{args.img}x{args.img} direct, no crop",
            "scale": "values/255",
            "mean": IMAGENET_MEAN,
            "std": IMAGENET_STD,
            "tensor": "NCHW float32",
        },
        "weights_init": args.weights,
        "best_val_acc": best,
        "args": {k: str(v) for k, v in vars(args).items()},
    }
    (args.out / "config.json").write_text(
        json.dumps(config, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    logger.info("Best validation accuracy: %.3f. Model: %s", best, args.out / "best.pt")
    return best


if __name__ == "__main__":
    configure_logging()
    main()
