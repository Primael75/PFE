import csv
import json
import random
from pathlib import Path

import pytest

np = pytest.importorskip(
    "numpy", reason="needs the diagnosis group: uv sync --group diagnosis"
)
Image = pytest.importorskip("PIL.Image", reason="needs the diagnosis group")

from agritech.data import check_split, prepare_data

RAW = "CCMT Dataset"


def save_noise(path: Path, seed: int, tweak: bool = False) -> None:
    """Random image; tweak changes one pixel, giving a near-duplicate with other bytes."""
    a = np.random.default_rng(seed).integers(0, 256, (32, 32, 3), dtype=np.uint8)
    if tweak:
        a[0, 0] = 255 - a[0, 0]
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(a).save(path)


@pytest.fixture
def raw(tmp_path):
    root = tmp_path / "raw"
    seed = 0
    for crop in ("Maize", "Tomato"):
        for folder in ("healthy", "leaf blight"):
            for i in range(20):
                seed += 1
                save_noise(root / RAW / crop / folder / f"{i}.png", seed)
    maize = root / RAW / "Maize" / "healthy"
    (maize / "copy.png").write_bytes((maize / "0.png").read_bytes())
    save_noise(maize / "near.png", 1, tweak=True)
    (maize / "broken.png").write_bytes(b"not an image")
    save_noise(root / "CCMT Dataset-Augmented" / "Maize" / "healthy" / "aug.png", 999)
    return root


def read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run(raw: Path, out: Path, *extra: str) -> None:
    prepare_data.main(["--root", str(raw), "--out", str(out), *extra])


def test_label_carries_the_crop():
    assert prepare_data.make_label("maize", "leaf blight") == "maize_leaf_blight"
    assert prepare_data.make_label("tomato", "Leaf-Blight ") == "tomato_leaf_blight"
    assert prepare_data.make_label("maize", "maize_healthy") == "maize_healthy"


def test_crop_is_read_from_the_folders():
    assert prepare_data.crop_of(Path("CCMT Dataset/Maize/healthy/1.jpg")) == "maize"
    assert prepare_data.crop_of(Path("Other/healthy/1.jpg")) is None


def test_augmented_folders_are_skipped(raw):
    found = prepare_data.find_images(raw, include_augmented=False)
    assert found
    assert not any("augment" in p.as_posix().lower() for p in found)
    assert len(prepare_data.find_images(raw, include_augmented=True)) == len(found) + 1


def test_near_duplicates_share_a_cluster():
    base = 0b1010 << 40
    roots = prepare_data.near_duplicate_clusters(
        [base, base ^ 1, ~base & (2**64 - 1)], thr=4
    )
    assert roots[0] == roots[1] != roots[2]


def test_a_cluster_is_never_split():
    items = [{"label": "a", "cluster": i // 3} for i in range(30)]
    assign = prepare_data.split_clusters(items, 0.2, 0.2, random.Random(0))
    assert set(assign) == set(range(10))
    assert set(assign.values()) == {"train", "val", "test"}


def test_prepare_writes_a_sound_split(raw, tmp_path):
    out = tmp_path / "split"
    run(raw, out)

    rows = {n: read(out / f"{n}.csv") for n in ("train", "val", "test")}
    paths = [r["path"] for v in rows.values() for r in v]
    assert len(paths) == 81  # 80 originals + the near-duplicate, kept but clustered
    assert not any(p.endswith(("copy.png", "broken.png", "aug.png")) for p in paths)
    assert "broken.png" in (out / "broken.csv").read_text(encoding="utf-8")
    assert "copy.png" in (out / "duplicates.csv").read_text(encoding="utf-8")

    by_path = {r["path"]: r["cluster"] for v in rows.values() for r in v}
    assert (
        by_path[f"{RAW}/Maize/healthy/near.png"]
        == by_path[f"{RAW}/Maize/healthy/0.png"]
    )

    classes = json.loads((out / "classes.json").read_text(encoding="utf-8"))
    assert classes == [
        "maize_healthy",
        "maize_leaf_blight",
        "tomato_healthy",
        "tomato_leaf_blight",
    ]
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    assert meta["test_lock_sha256"] == prepare_data.sha256_file(out / "test.csv")
    assert all(ok for ok, _ in check_split.check_split(out))


def test_same_seed_gives_the_same_test_split(raw, tmp_path):
    run(raw, tmp_path / "a")
    run(raw, tmp_path / "b")
    assert (tmp_path / "a" / "test.csv").read_bytes() == (
        tmp_path / "b" / "test.csv"
    ).read_bytes()


def test_crop_filter(raw, tmp_path):
    out = tmp_path / "maize"
    run(raw, out, "--crop", "maize")
    assert all(
        c.startswith("maize_") for c in json.loads((out / "classes.json").read_text())
    )
    assert all(ok for ok, _ in check_split.check_split(out, "maize"))


def test_check_split_detects_a_leak(raw, tmp_path):
    out = tmp_path / "split"
    run(raw, out)
    test_rows = read(out / "test.csv")
    with open(out / "train.csv", "a", encoding="utf-8", newline="") as f:
        csv.DictWriter(f, fieldnames=prepare_data.FIELDS).writerow(test_rows[0])

    failed = [msg for ok, msg in check_split.check_split(out) if not ok]
    assert "no near-duplicate group is shared by two splits" in failed
    assert "no photo appears twice" in failed
    assert check_split.main(["--data", str(out)]) == 1
