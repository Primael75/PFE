"""Time of the diagnosis tool alone, called over HTTP as Fred calls it.

Complement to H-T2 on the server side (docs/trials/ht2-diagnosis-time.md);
H-T2 itself is measured on the phone.

Two ways to name the photos:

- a folder, read by the server too (AGRITECH_PHOTO_DIR): the file name is
  the document uid. 20 photos are drawn at random (seed 42).
      uv run python scripts/measure_ht2.py --photo-dir /path/to/photos
- a file of Knowledge Flow document uids, one per line, the server reading
  from Knowledge Flow (AGRITECH_KF_BASE_URL). The bearer is read from
  AGRITECH_MEASURE_TOKEN and sent as Fred sends it; the delegation grant,
  if Knowledge Flow needs it, goes in the query string of --url.
      uv run python scripts/measure_ht2.py --uids uids.txt --url "http://host:8078/mcp?person=..."

Each photo is diagnosed once per round (--rounds, default 1), after two
warm-up calls that are not counted. --out writes every call and the summary
to a JSON file, to fill in the trial table.
"""

import argparse
import asyncio
import json
import logging
import os
import platform
import random
import statistics
import time
from collections import Counter
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

logger = logging.getLogger("measure_ht2")

THRESHOLD_S = 5.0  # same limit as H-T2 and ENF-01 for the diagnosis
WARM_UP = 2
SEED = 42
TOKEN_VARIABLE = "AGRITECH_MEASURE_TOKEN"


async def measure(
    transport: StreamableHttpTransport, uids: list[str], rounds: int
) -> list[dict]:
    calls = []
    async with Client(transport) as client:
        order = [uids[i % len(uids)] for i in range(WARM_UP)] + uids * rounds
        for i, uid in enumerate(order):
            started = time.perf_counter()
            result = await client.call_tool(
                "diagnose_photo", {"document_uid": uid}, raise_on_error=False
            )
            elapsed = time.perf_counter() - started
            if result.is_error:
                raise SystemExit(f"Tool error on {uid}: {result.content[0].text}")
            if i >= WARM_UP:
                answer = result.structured_content
                calls.append(
                    {
                        "uid": uid,
                        "seconds": round(elapsed, 4),
                        "value": answer["value"],
                        "uncertainty": answer.get("uncertainty"),
                    }
                )
    return calls


def pick_photos(photo_dir: Path, count: int) -> list[Path]:
    files = sorted(p for p in photo_dir.iterdir() if p.is_file())
    if not files:
        raise SystemExit(f"No photo in {photo_dir}")
    if count >= len(files):
        return files
    return sorted(random.Random(SEED).sample(files, count))


def summarise(calls: list[dict]) -> dict:
    durations = sorted(call["seconds"] for call in calls)
    p95 = durations[max(0, round(0.95 * len(durations)) - 1)]
    return {
        "calls": len(durations),
        "photos": len({call["uid"] for call in calls}),
        "min_s": durations[0],
        "median_s": round(statistics.median(durations), 4),
        "p95_s": p95,
        "max_s": durations[-1],
        "answers": dict(Counter(call["value"] for call in calls).most_common()),
        "p95_under_5_s": p95 < THRESHOLD_S,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for noisy in ("httpx", "httpx2"):  # one line per HTTP request otherwise
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    names = parser.add_mutually_exclusive_group(required=True)
    names.add_argument("--photo-dir", type=Path, help="folder also read by the server")
    names.add_argument("--uids", type=Path, help="file of Knowledge Flow uids")
    parser.add_argument(
        "--photos", type=int, default=20, help="photos drawn from --photo-dir"
    )
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--url", default="http://127.0.0.1:8078/mcp")
    parser.add_argument(
        "--out", type=Path, help="JSON file for every call and the summary"
    )
    args = parser.parse_args()

    if args.photo_dir:
        photos = pick_photos(args.photo_dir, args.photos)
        uids = [p.name for p in photos]
        sizes_kb = [round(p.stat().st_size / 1024) for p in photos]
    else:
        uids = [
            line.strip() for line in args.uids.read_text().splitlines() if line.strip()
        ]
        sizes_kb = []
    if not uids:
        raise SystemExit("No photo to measure")

    token = os.environ.get(TOKEN_VARIABLE)
    headers = {"Authorization": f"Bearer {token}"} if token else None
    transport = StreamableHttpTransport(args.url, headers=headers)
    calls = asyncio.run(measure(transport, uids, args.rounds))
    summary = summarise(calls)

    size = f"{min(sizes_kb)} to {max(sizes_kb)} KB" if sizes_kb else "sizes unknown"
    logger.info(
        "%d calls on %d photos (%s): min %.3f s, median %.3f s, p95 %.3f s, max %.3f s",
        summary["calls"],
        summary["photos"],
        size,
        summary["min_s"],
        summary["median_s"],
        summary["p95_s"],
        summary["max_s"],
    )
    logger.info("Answers: %s", summary["answers"])
    under = "yes" if summary["p95_under_5_s"] else "no"
    logger.info("p95 under %.0f s: %s (%.3f s)", THRESHOLD_S, under, summary["p95_s"])

    if args.out:
        record = {
            "client_machine": {
                "system": platform.platform(),
                "processor": platform.processor() or platform.machine(),
                "cpus": os.cpu_count(),
            },
            "url": args.url.split("?")[0],  # the grant may name a person
            "source": "photo folder" if args.photo_dir else "Knowledge Flow uids",
            "photo_sizes_kb": sizes_kb,
            "summary": summary,
            "calls": calls,
        }
        args.out.write_text(json.dumps(record, indent=2), encoding="utf-8")
        logger.info("Written to %s", args.out)


if __name__ == "__main__":
    main()
