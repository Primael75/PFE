"""Score a model per class on the validation split.

Example, from the repository root:
    uv run python -m agritech.diagnosis.evaluate --data data_ccmt \\
        --model runs/run1/best.pt --out runs/run1/val_scores.json

Only val.csv is read: the test split is kept for the final score.
"""

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

from torch.utils.data import DataLoader

from agritech.core.logging_config import configure_logging
from agritech.data.common import load_meta, read_manifest, sha256_file
from agritech.diagnosis.model import (
    ManifestDataset,
    eval_transform,
    load_checkpoint,
    pick_device,
    predict_logits,
)

logger = logging.getLogger(__name__)


def per_class_scores(y_true: list[int], y_pred: list[int], classes: list[str]) -> dict:
    """Precision, recall and F1 per class, plus accuracy, macro F1 and main confusions."""
    pairs = Counter(zip(y_true, y_pred, strict=True))
    rows = []
    for i, c in enumerate(classes):
        tp = pairs[(i, i)]
        support = sum(v for (t, _), v in pairs.items() if t == i)
        predicted = sum(v for (_, p), v in pairs.items() if p == i)
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = (
            2 * precision * recall / (precision + recall) if precision + recall else 0.0
        )
        errors = sorted(
            ((v, classes[p]) for (t, p), v in pairs.items() if t == i and p != i),
            reverse=True,
        )
        rows.append(
            {
                "class": c,
                "support": support,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "most_confused_with": errors[0][1] if errors else None,
                "most_confused_count": errors[0][0] if errors else 0,
            }
        )
    n = len(y_true)
    return {
        "photos": n,
        "accuracy": round(sum(pairs[(i, i)] for i in range(len(classes))) / n, 4)
        if n
        else 0.0,
        "macro_f1": round(sum(r["f1"] for r in rows) / len(rows), 4) if rows else 0.0,
        "per_class": rows,
    }


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--data", required=True, type=Path, help="folder written by prepare_data"
    )
    ap.add_argument("--model", required=True, type=Path)
    ap.add_argument("--root", type=Path, help="override the photo folder")
    ap.add_argument("--out", type=Path, help="JSON file for the scores")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args(argv)

    device = pick_device(args.device)
    _, root, _ = load_meta(args.data, args.root)
    model, ck = load_checkpoint(args.model, device)
    classes = ck["classes"]
    rows = read_manifest(args.data / "val.csv")
    ds = ManifestDataset(rows, root, classes, eval_transform(ck["img_size"]))
    loader = DataLoader(
        ds, batch_size=args.batch, shuffle=False, num_workers=args.workers
    )
    logits, labels = predict_logits(model, loader, device)

    scores = per_class_scores(labels.tolist(), logits.argmax(1).tolist(), classes)
    scores["split"] = "val"
    scores["model_sha256"] = sha256_file(args.model)
    scores["val_csv_sha256"] = sha256_file(args.data / "val.csv")

    logger.info("%-28s%8s%10s%8s%8s", "class", "photos", "precision", "recall", "f1")
    for r in scores["per_class"]:
        logger.info(
            "%-28s%8d%10.3f%8.3f%8.3f",
            r["class"],
            r["support"],
            r["precision"],
            r["recall"],
            r["f1"],
        )
    logger.info("Accuracy %.4f | macro F1 %.4f", scores["accuracy"], scores["macro_f1"])
    if args.out:
        args.out.write_text(json.dumps(scores, indent=1), encoding="utf-8")
        logger.info("Scores written to %s", args.out)
    return scores


if __name__ == "__main__":
    configure_logging()
    main()
