"""Helpers shared by the photo dataset scripts: manifests, hashes, metadata.

Model and training helpers live with the diagnosis brick, so that preparing
the data does not require PyTorch.
"""

import csv
import hashlib
import json
import random
from pathlib import Path

import numpy as np

OOD_LABEL = "hors_sujet"


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def read_manifest(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_manifest(path: Path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_meta(
    data_dir: Path, root_override: Path | None = None
) -> tuple[dict, Path, list[str]]:
    """Read meta.json and classes.json written by prepare_data."""
    meta = json.loads((Path(data_dir) / "meta.json").read_text(encoding="utf-8"))
    root = Path(root_override or meta["root"])
    classes = json.loads((Path(data_dir) / "classes.json").read_text(encoding="utf-8"))
    return meta, root, classes
