import json

import pytest

np = pytest.importorskip(
    "numpy", reason="needs the diagnosis group: uv sync --group diagnosis"
)
Image = pytest.importorskip("PIL.Image", reason="needs the diagnosis group")
torch = pytest.importorskip("torch", reason="needs the diagnosis group")

from agritech.data import prepare_data
from agritech.diagnosis import evaluate, latency, train
from agritech.diagnosis.model import load_checkpoint

CLASSES = ["maize_healthy", "maize_leaf_spot"]


@pytest.fixture(scope="module")
def split(tmp_path_factory):
    """A tiny split of random images, prepared by the real data script."""
    tmp = tmp_path_factory.mktemp("photos")
    raw = tmp / "raw"
    seed = 0
    for folder in ("healthy", "leaf spot"):
        d = raw / "CCMT Dataset" / "Maize" / folder
        d.mkdir(parents=True)
        for i in range(12):
            seed += 1
            a = np.random.default_rng(seed).integers(
                0, 256, (40, 40, 3), dtype=np.uint8
            )
            Image.fromarray(a).save(d / f"{i}.png")
    out = tmp / "split"
    prepare_data.main(["--root", str(raw), "--out", str(out)])
    return out


@pytest.fixture(scope="module")
def model_path(split, tmp_path_factory):
    out = tmp_path_factory.mktemp("run")
    # Random weights and 32 px images: no download, a few seconds on CPU.
    train.main(
        [
            "--data", str(split), "--out", str(out), "--weights", "none",
            "--epochs-head", "1", "--epochs-ft", "1", "--img", "32",
            "--batch", "4", "--workers", "0", "--device", "cpu",
        ]
    )  # fmt: skip
    return out / "best.pt"


def test_per_class_scores():
    classes = ["a", "b", "c"]
    scores = evaluate.per_class_scores([0, 0, 0, 1, 1, 2], [0, 0, 1, 1, 1, 0], classes)
    a, b, c = scores["per_class"]
    assert scores["accuracy"] == round(4 / 6, 4)
    assert (a["support"], a["precision"], a["recall"]) == (
        3,
        round(2 / 3, 4),
        round(2 / 3, 4),
    )
    assert (b["precision"], b["recall"]) == (round(2 / 3, 4), 1.0)
    assert (c["precision"], c["recall"], c["f1"]) == (0.0, 0.0, 0.0)
    assert (a["most_confused_with"], a["most_confused_count"]) == ("b", 1)
    assert b["most_confused_with"] is None


def test_summarize_latency():
    s = latency.summarize([float(i) for i in range(1, 21)])
    assert s == {
        "photos": 20,
        "median_ms": 10.5,
        "p90_ms": 18.0,
        "mean_ms": 10.5,
        "max_ms": 20.0,
    }


def test_subset_keeps_at_most_n_per_class():
    rows = [{"label": lab} for lab in ["a"] * 5 + ["b"] * 2]
    picked = train.subset_rows(rows, 3, seed=0)
    assert sorted(r["label"] for r in picked) == ["a", "a", "a", "b", "b"]


def test_training_writes_a_loadable_model(model_path):
    model, ck = load_checkpoint(model_path, torch.device("cpu"))
    assert ck["classes"] == CLASSES
    assert ck["img_size"] == 32
    assert model(torch.zeros(1, 3, 32, 32)).shape == (1, len(CLASSES))
    config = json.loads((model_path.parent / "config.json").read_text())
    assert config["preprocessing"]["resize"] == "32x32 direct, no crop"
    assert (model_path.parent / "metrics.csv").read_text().count("\n") == 3


def test_training_never_reads_the_test_split(split, tmp_path):
    copy = tmp_path / "split"
    copy.mkdir()
    for name in ("train.csv", "val.csv", "meta.json", "classes.json"):
        (copy / name).write_bytes((split / name).read_bytes())
    train.main(
        [
            "--data", str(copy), "--out", str(tmp_path / "run"), "--weights", "none",
            "--epochs-head", "1", "--epochs-ft", "0", "--img", "32",
            "--batch", "4", "--workers", "0", "--device", "cpu",
        ]
    )  # fmt: skip
    assert (tmp_path / "run" / "best.pt").exists()


def test_evaluate_scores_every_class(split, model_path, tmp_path):
    out = tmp_path / "scores.json"
    scores = evaluate.main(
        [
            "--data",
            str(split),
            "--model",
            str(model_path),
            "--out",
            str(out),
            "--workers",
            "0",
        ]
    )
    assert [r["class"] for r in scores["per_class"]] == CLASSES
    assert scores["photos"] == sum(r["support"] for r in scores["per_class"])
    assert scores["split"] == "val"
    assert json.loads(out.read_text())["model_sha256"] == scores["model_sha256"]


def test_latency_measures_the_requested_photos(split, model_path):
    result = latency.main(
        ["--data", str(split), "--model", str(model_path), "--photos", "2"]
    )
    assert result["per_photo"]["photos"] == 2
    assert result["warm_up_photo"] not in result["photos"]
    assert result["per_photo"]["max_ms"] > 0
