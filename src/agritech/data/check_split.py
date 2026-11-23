"""Check that a split is sound: no leak, no edited copy, right crops.

Example, from the repository root:
    uv run python -m agritech.data.check_split --data data_ccmt
"""

import argparse
import hashlib
import logging
import sys
from collections import Counter
from pathlib import Path

from agritech.core.logging_config import configure_logging
from agritech.data.common import OOD_LABEL, load_meta, read_manifest

logger = logging.getLogger(__name__)

SPLITS = ("train", "val", "test")
CROPS = ["cashew", "cassava", "maize", "tomato"]


def _disjoint(sets: dict[str, set]) -> bool:
    return not (
        sets["train"] & sets["val"]
        or sets["train"] & sets["test"]
        or sets["val"] & sets["test"]
    )


def check_split(data_dir: Path, expect_crop: str = "all") -> list[tuple[bool, str]]:
    """Run every check on the split in data_dir; returns (passed, description) pairs."""
    _, root, _ = load_meta(data_dir)
    sp = {n: read_manifest(data_dir / f"{n}.csv") for n in SPLITS}

    def md5(r):
        p = Path(r["path"])
        p = p if p.is_absolute() else root / p
        return hashlib.md5(p.read_bytes()).hexdigest()

    allp = [r["path"] for rows in sp.values() for r in rows]
    crops = CROPS if expect_crop == "all" else [expect_crop]
    labels = {r["label"] for rows in sp.values() for r in rows}
    return [
        (
            _disjoint({n: {r["cluster"] for r in rows} for n, rows in sp.items()}),
            "no near-duplicate group is shared by two splits",
        ),
        (
            _disjoint({n: {md5(r) for r in rows} for n, rows in sp.items()}),
            "no identical photo (byte for byte) in two splits",
        ),
        (
            not any("augment" in p.lower() for p in allp),
            "no photo from an 'augment' folder",
        ),
        (
            all(
                any(c in p.lower() for c in crops) or Path(p).is_absolute()
                for p in allp
            ),
            f"every photo comes from: {', '.join(crops)}",
        ),
        (
            all(
                lab == OOD_LABEL or any(lab.startswith(c + "_") for c in crops)
                for lab in labels
            ),
            "every class carries its crop name (no 'healthy' merged across crops)",
        ),
        (len(allp) == len(set(allp)), "no photo appears twice"),
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--expect-crop", default="all", choices=[*CROPS, "all"])
    args = ap.parse_args(argv)

    results = check_split(args.data, args.expect_crop)
    for passed, msg in results:
        logger.info("%s %s", "OK  " if passed else "FAIL", msg)
    for n in SPLITS:
        logger.info(
            "%s: %s",
            n,
            dict(Counter(r["label"] for r in read_manifest(args.data / f"{n}.csv"))),
        )
    return 0 if all(p for p, _ in results) else 1


if __name__ == "__main__":
    configure_logging()
    sys.exit(main())
