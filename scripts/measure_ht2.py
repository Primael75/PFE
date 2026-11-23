"""H-T2: time of the diagnosis tool alone, called over HTTP as Fred calls it.

Usage, with the server reading photos from the same folder
(see src/agritech/diagnosis/README.md):
    uv run python scripts/measure_ht2.py /path/to/photos --runs 50

Each call diagnoses one photo of the folder (the file name is the document
uid), cycling through the folder. Two warm-up calls are not counted.
"""

import argparse
import asyncio
import logging
import statistics
import time
from collections import Counter
from pathlib import Path

from fastmcp import Client

logger = logging.getLogger("measure_ht2")

THRESHOLD_S = 5.0  # H-T2: answer in less than 5 seconds on the server
WARM_UP = 2


async def measure(url: str, uids: list[str], runs: int) -> tuple[list[float], Counter]:
    durations, labels = [], Counter()
    async with Client(url) as client:
        for i in range(WARM_UP + runs):
            uid = uids[i % len(uids)]
            started = time.perf_counter()
            result = await client.call_tool(
                "diagnose_photo", {"document_uid": uid}, raise_on_error=False
            )
            elapsed = time.perf_counter() - started
            if result.is_error:
                raise SystemExit(f"Tool error on {uid}: {result.content[0].text}")
            if i >= WARM_UP:
                durations.append(elapsed)
                labels[result.structured_content["value"]] += 1
    return durations, labels


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for noisy in ("httpx", "httpx2"):  # one line per HTTP request otherwise
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo_dir", type=Path)
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--runs", type=int, default=50)
    args = parser.parse_args()

    files = sorted(p for p in args.photo_dir.iterdir() if p.is_file())
    if not files:
        raise SystemExit(f"No photo in {args.photo_dir}")
    sizes = [p.stat().st_size / 1024 for p in files]
    durations, labels = asyncio.run(
        measure(args.url, [p.name for p in files], args.runs)
    )

    durations.sort()
    p95 = durations[max(0, round(0.95 * len(durations)) - 1)]
    logger.info(
        "%d calls on %d photos (%.0f to %.0f KB): "
        "min %.3f s, median %.3f s, p95 %.3f s, max %.3f s",
        len(durations),
        len(files),
        min(sizes),
        max(sizes),
        durations[0],
        statistics.median(durations),
        p95,
        durations[-1],
    )
    logger.info("Answers: %s", dict(labels.most_common()))
    verdict = "passed" if p95 < THRESHOLD_S else "failed"
    logger.info("H-T2 %s: p95 %.3f s against %.0f s", verdict, p95, THRESHOLD_S)


if __name__ == "__main__":
    main()
