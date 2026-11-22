"""H-T4: time of the photo tool alone, called over HTTP as Fred calls it.

Usage, with the server running (see src/agritech/example/README.md):
    uv run python scripts/measure_ht4.py doc-1 --runs 20

The time and cost of a whole agent turn are read in Fred (see docs/essais/ht4.md).
"""

import argparse
import asyncio
import logging
import statistics
import time

from fastmcp import Client

logger = logging.getLogger("measure_ht4")


async def measure(url: str, document_uid: str, runs: int) -> list[float]:
    durations = []
    async with Client(url) as client:
        for _ in range(runs):
            started = time.perf_counter()
            result = await client.call_tool(
                "inspect_photo", {"document_uid": document_uid}, raise_on_error=False
            )
            durations.append((time.perf_counter() - started) * 1000)
            if result.is_error:
                raise SystemExit(f"Tool error: {result.content[0].text}")
    return durations


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for noisy in ("httpx", "httpx2"):  # one line per HTTP request otherwise
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document_uid")
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args()

    durations = sorted(asyncio.run(measure(args.url, args.document_uid, args.runs)))
    p95 = durations[max(0, round(0.95 * len(durations)) - 1)]
    logger.info(
        "%d calls: min %.0f ms, median %.0f ms, p95 %.0f ms, max %.0f ms",
        len(durations),
        durations[0],
        statistics.median(durations),
        p95,
        durations[-1],
    )


if __name__ == "__main__":
    main()
