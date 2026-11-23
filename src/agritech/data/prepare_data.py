"""Prepare the photo splits: filtering, duplicates, leak-free split.

Example, from the repository root:
    uv run python -m agritech.data.prepare_data --root ~/pfe/raw_data --out data_ccmt

Steps:
 1. Find the photos under --root. Folders whose name contains "augment" are
    SKIPPED (edited copies: they would inflate the test score).
 2. Keep the requested crop (the crop name must appear in the path).
    The label of a photo is the name of its parent folder, prefixed by the crop.
 3. Remove exact duplicates (file hash).
 4. Group near-duplicates (dHash visual fingerprint): a group is NEVER split
    between training, validation and test.
 5. Write train.csv / val.csv / test.csv, classes.json, meta.json, and lock test.csv.
"""

import argparse
import hashlib
import json
import logging
import os
import random
import stat
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from agritech.core.logging_config import configure_logging
from agritech.data.common import OOD_LABEL, seed_everything, sha256_file, write_manifest

logger = logging.getLogger(__name__)

CROPS = ["cashew", "cassava", "maize", "tomato"]
EXT = {".jpg", ".jpeg", ".png", ".bmp"}
FIELDS = ["path", "label", "cluster"]
POPCOUNT = np.array([i.bit_count() for i in range(256)], dtype=np.uint8)


def find_images(root: Path, include_augmented: bool) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in EXT:
            continue
        rel = p.relative_to(root)
        parts = [x.lower() for x in rel.parts[:-1]]
        if not include_augmented and any("augment" in x for x in parts):
            continue
        out.append(rel)
    return out


def crop_of(rel: Path) -> str | None:
    for part in rel.parts[:-1]:
        for c in CROPS:
            if c in part.lower():
                return c
    return None


def norm_label(s: str) -> str:
    return s.strip().lower().replace(" ", "_").replace("-", "_")


def make_label(crop: str, folder: str) -> str:
    """Prefix the crop: "healthy" exists for all 4 crops, "leaf blight" for 2."""
    lab = norm_label(folder)
    return lab if lab.startswith(crop + "_") else f"{crop}_{lab}"


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dhash(path: Path) -> int:
    """64-bit visual fingerprint: two nearly identical photos have close fingerprints."""
    # Full decode, so that a damaged photo fails here rather than during training.
    img = Image.open(path)
    img = (
        ImageOps.exif_transpose(img)
        .convert("L")
        .resize((9, 8), Image.Resampling.LANCZOS)
    )
    a = np.asarray(img, dtype=np.int16)
    bits = (a[:, 1:] > a[:, :-1]).flatten()
    h = 0
    for b in bits:
        h = (h << 1) | int(b)
    return h


def near_duplicate_clusters(hashes: list[int], thr: int) -> list[int]:
    """Union-find over fingerprints at Hamming distance <= thr; returns a root per photo."""
    n = len(hashes)
    h = np.array(hashes, dtype=np.uint64)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    block = 64
    for i in range(0, n, block):
        x = (h[i : i + block, None] ^ h[None, :]).view(np.uint8).reshape(-1, n, 8)
        d = POPCOUNT[x].sum(axis=2)
        ii, jj = np.nonzero(d <= thr)
        for a, b in zip(ii + i, jj, strict=True):
            if a < b:
                ra, rb = find(int(a)), find(int(b))
                if ra != rb:
                    parent[ra] = rb
    return [find(i) for i in range(n)]


def split_clusters(
    items: list[dict], val_frac: float, test_frac: float, rng: random.Random
) -> dict:
    """items: dicts with 'label' and 'cluster'. Returns cluster -> split name."""
    by_cluster = defaultdict(list)
    for it in items:
        by_cluster[it["cluster"]].append(it)
    dominant = {
        c: Counter(i["label"] for i in v).most_common(1)[0][0]
        for c, v in by_cluster.items()
    }
    by_class = defaultdict(list)
    for c, lab in dominant.items():
        by_class[lab].append(c)
    assign = {}
    for _lab, clusters in sorted(by_class.items()):
        rng.shuffle(clusters)
        total = sum(len(by_cluster[c]) for c in clusters)
        n_test, n_val = test_frac * total, val_frac * total
        got_test = got_val = 0
        for c in clusters:
            size = len(by_cluster[c])
            if got_test < n_test:
                assign[c] = "test"
                got_test += size
            elif got_val < n_val:
                assign[c] = "val"
                got_val += size
            else:
                assign[c] = "train"
    return assign


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--root", required=True, type=Path, help="root folder of the CCMT dataset"
    )
    ap.add_argument(
        "--crop", default="all", choices=[*CROPS, "all"], help="all = the 4 CCMT crops"
    )
    ap.add_argument("--out", default=Path("data_split"), type=Path)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--test", type=float, default=0.15)
    ap.add_argument(
        "--hamming",
        type=int,
        default=4,
        help="max distance (out of 64) for near-duplicates",
    )
    ap.add_argument(
        "--include-augmented", action="store_true", help="DO NOT USE (data leak)"
    )
    ap.add_argument(
        "--ood-dir", type=Path, help="off-topic photos for the hors_sujet class"
    )
    ap.add_argument(
        "--ood-holdout-dir",
        type=Path,
        help="separate off-topic photos kept for the final test",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    seed_everything(args.seed)
    rng = random.Random(args.seed)
    root = args.root.resolve()
    args.out.mkdir(parents=True, exist_ok=True)

    rels = find_images(root, args.include_augmented)
    logger.info("%d photos found (outside 'augment' folders)", len(rels))
    if args.include_augmented:
        logger.warning("Augmented photos included: the test score will be inflated.")

    logger.info("Photos per crop: %s", dict(Counter(crop_of(r) for r in rels)))
    items = []
    for r in rels:
        c = crop_of(r)
        if c is None or (args.crop != "all" and c != args.crop):
            continue
        items.append(
            {"path": r.as_posix(), "label": make_label(c, r.parent.name), "crop": c}
        )
    if not items:
        raise SystemExit(
            "No photo kept. Check --root and --crop. "
            f"Subfolders of the root: {sorted(p.name for p in root.iterdir())[:20]}"
        )
    logger.info("Classes kept: %s", dict(Counter(i["label"] for i in items)))

    if args.ood_dir:
        ood_root = args.ood_dir.resolve()
        ood = [
            p
            for p in sorted(ood_root.rglob("*"))
            if p.is_file() and p.suffix.lower() in EXT
        ]
        # Off-topic paths are stored as absolute paths: they are not under --root.
        items.extend({"path": str(p), "label": OOD_LABEL, "crop": "ood"} for p in ood)
        logger.info("%d off-topic photos added to class %s", len(ood), OOD_LABEL)

    def full(it):
        p = Path(it["path"])
        return p if p.is_absolute() else root / p

    # Exact duplicates.
    seen, kept, dups = {}, [], []
    for it in items:
        m = md5_file(full(it))
        if m in seen:
            dups.append((it["path"], seen[m]))
        else:
            seen[m] = it["path"]
            it["md5"] = m
            kept.append(it)
    logger.info("Exact duplicates removed: %d", len(dups))
    with open(args.out / "duplicates.csv", "w", encoding="utf-8") as f:
        f.write("retire,identique_a\n")
        f.writelines(f"{a},{b}\n" for a, b in dups)
    items = kept

    # Near-duplicates; computing the fingerprint also checks that each photo decodes.
    logger.info("Computing visual fingerprints...")
    hashes, readable, broken = [], [], []
    for n, it in enumerate(items, 1):
        try:
            hashes.append(dhash(full(it)))
            readable.append(it)
        # Any decoding error means the photo is unusable: set it aside and record why.
        except Exception as e:  # noqa: BLE001
            broken.append((it["path"], f"{type(e).__name__}: {e}"))
        if n % 2000 == 0:
            logger.info("  %d / %d photos processed", n, len(items))
    items = readable
    with open(args.out / "broken.csv", "w", encoding="utf-8") as f:
        f.write("photo_ecartee;erreur\n")
        f.writelines(f"{p};{e}\n" for p, e in broken)
    logger.info(
        "Unreadable photos set aside: %d (list in %s)",
        len(broken),
        args.out / "broken.csv",
    )
    for p, e in broken[:10]:
        logger.info("  - %s (%s)", p, e)
    roots = near_duplicate_clusters(hashes, args.hamming)
    for it, c in zip(items, roots, strict=True):
        it["cluster"] = c
    sizes = Counter(roots)
    multi = [s for s in sizes.values() if s > 1]
    logger.info(
        "Near-duplicate groups: %d (largest: %d photos)",
        len(multi),
        max(sizes.values()),
    )

    assign = split_clusters(items, args.val, args.test, rng)
    splits = {"train": [], "val": [], "test": []}
    for it in items:
        splits[assign[it["cluster"]]].append(it)

    classes = sorted({i["label"] for i in items})
    for name, rows in splits.items():
        write_manifest(args.out / f"{name}.csv", rows, FIELDS)
    (args.out / "classes.json").write_text(
        json.dumps(classes, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    holdout_n = 0
    if args.ood_holdout_dir:
        train_md5 = {i["md5"] for i in items}
        rows = [
            {"path": str(p), "label": OOD_LABEL, "cluster": ""}
            for p in sorted(args.ood_holdout_dir.resolve().rglob("*"))
            if p.is_file() and p.suffix.lower() in EXT and md5_file(p) not in train_md5
        ]
        write_manifest(args.out / "ood_holdout.csv", rows, FIELDS)
        holdout_n = len(rows)
        logger.info("%d off-topic photos kept for the final test only", holdout_n)

    # The test split is used once, for the final score: its hash detects any later change.
    test_csv = args.out / "test.csv"
    lock = sha256_file(test_csv)
    (args.out / "TEST_LOCK.txt").write_text(
        f"sha256 of test.csv: {lock}\nThe test split is locked: use it once, for the final score.\n",
        encoding="utf-8",
    )
    os.chmod(test_csv, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    meta = {
        "root": str(root),
        "crop": args.crop,
        "seed": args.seed,
        "val_frac": args.val,
        "test_frac": args.test,
        "hamming": args.hamming,
        "include_augmented": args.include_augmented,
        "counts": {k: len(v) for k, v in splits.items()},
        "ood_holdout": holdout_n,
        "test_lock_sha256": lock,
    }
    (args.out / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")

    logger.info("Photos per class and split:")
    logger.info("%-28s%8s%8s%8s", "class", "train", "val", "test")
    for c in classes:
        n = {k: sum(1 for r in v if r["label"] == c) for k, v in splits.items()}
        warn = "  <- very few photos" if min(n.values()) < 5 else ""
        logger.info("%-28s%8d%8d%8d%s", c, n["train"], n["val"], n["test"], warn)
    logger.info(
        "%-28s%8d%8d%8d", "TOTAL", *(len(splits[k]) for k in ("train", "val", "test"))
    )
    logger.info("Files written to %s; test.csv is read-only.", args.out)


if __name__ == "__main__":
    configure_logging()
    main()
