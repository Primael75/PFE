"""Measure the response time of the model with PyTorch, on photos of the validation split.

This is a reference for H-T2, not its test: H-T2 is about a modest phone,
in a browser.

The time of one photo covers what a request does: read the file, decode it,
resize and normalise it, run the model, pick the class. Loading the model is
measured apart, since a server does it once.

Example, from the repository root:
    uv run python -m agritech.diagnosis.latency --data data_ccmt \\
        --model runs/run1/best.pt --photos 20 --out runs/run1/latency.json
"""

import argparse
import io
import json
import logging
import os
import platform
import random
import statistics
import time
from pathlib import Path

import torch

from agritech.core.logging_config import configure_logging
from agritech.data.common import load_meta, read_manifest, sha256_file
from agritech.diagnosis.model import eval_transform, load_checkpoint, load_rgb

logger = logging.getLogger(__name__)


def cpu_name() -> str:
    """Processor model, read from /proc/cpuinfo on Linux; platform's guess otherwise."""
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def summarize(times_ms: list[float]) -> dict:
    """Median, 90th percentile, mean and max of per-photo times, in milliseconds."""
    ordered = sorted(times_ms)
    p90 = ordered[min(len(ordered) - 1, round(0.9 * (len(ordered) - 1)))]
    return {
        "photos": len(ordered),
        "median_ms": round(statistics.median(ordered), 1),
        "p90_ms": round(p90, 1),
        "mean_ms": round(statistics.fmean(ordered), 1),
        "max_ms": round(ordered[-1], 1),
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
    ap.add_argument("--photos", type=int, default=20)
    ap.add_argument(
        "--threads", type=int, default=0, help="CPU threads (0: PyTorch default)"
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, help="JSON file for the measures")
    args = ap.parse_args(argv)

    if args.threads:
        torch.set_num_threads(args.threads)
    _, root, _ = load_meta(args.data, args.root)
    rows = read_manifest(args.data / "val.csv")
    # One extra photo warms the model up; it is reported apart from the measured ones.
    sample = random.Random(args.seed).sample(rows, min(args.photos + 1, len(rows)))

    t0 = time.perf_counter()
    model, ck = load_checkpoint(args.model, torch.device("cpu"))
    transform = eval_transform(ck["img_size"])
    load_ms = (time.perf_counter() - t0) * 1000

    times, first_ms = [], None
    with torch.inference_mode():
        for r in sample:
            t0 = time.perf_counter()
            data = (root / r["path"]).read_bytes()
            x = transform(load_rgb(io.BytesIO(data))).unsqueeze(0)
            _label = ck["classes"][int(model(x)[0].argmax())]
            elapsed = (time.perf_counter() - t0) * 1000
            if first_ms is None:
                first_ms = elapsed
            else:
                times.append(elapsed)

    result = {
        "model_load_ms": round(load_ms, 1),
        "first_photo_ms": round(first_ms, 1),
        "per_photo": summarize(times),
        "device": "cpu",
        "cpu": cpu_name(),
        "cpu_count": os.cpu_count(),
        "torch_threads": torch.get_num_threads(),
        "torch_version": torch.__version__,
        "model_sha256": sha256_file(args.model),
        "warm_up_photo": sample[0]["path"],
        "photos": [r["path"] for r in sample[1:]],
    }
    logger.info(
        "Model load %.0f ms | first photo %.0f ms | next %d photos: median %.1f ms, "
        "p90 %.1f ms, max %.1f ms",
        load_ms,
        first_ms,
        result["per_photo"]["photos"],
        result["per_photo"]["median_ms"],
        result["per_photo"]["p90_ms"],
        result["per_photo"]["max_ms"],
    )
    if args.out:
        args.out.write_text(json.dumps(result, indent=1), encoding="utf-8")
        logger.info("Measures written to %s", args.out)
    return result


if __name__ == "__main__":
    configure_logging()
    main()
