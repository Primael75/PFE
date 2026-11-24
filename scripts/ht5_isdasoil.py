"""H-T5, soil part: iSDAsoil properties at a few points, at both depths.

Usage, from the repository root, with AGRITECH_ISDASOIL_USERNAME and
AGRITECH_ISDASOIL_PASSWORD set (see .env.example):
    uv run python scripts/ht5_isdasoil.py --out <folder> \
        --point Kandi 11.279 2.940 --point Djougou 9.696 1.817 \
        --point Karimama 11.912 2.801

Writes isdasoil_points.csv (one row per point, depth and property) and
isdasoil_raw.json (every API response) into --out. One call per property:
3 points x 2 depths x 4 properties = 24 calls.
"""

import argparse
import csv
import json
import logging
import os
from dataclasses import asdict
from pathlib import Path

from agritech.core.logging_config import configure_logging
from agritech.data.isdasoil import DEPTHS, IsdaSoilClient, parse_property

logger = logging.getLogger("ht5_isdasoil")

# The four properties of EF-12: acidity, texture, organic matter, nitrogen.
PROPERTIES = ("ph", "clay_content", "carbon_organic", "nitrogen_total")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--point",
        nargs=3,
        action="append",
        required=True,
        metavar=("NAME", "LAT", "LON"),
    )
    args = parser.parse_args()

    client = IsdaSoilClient(
        os.environ["AGRITECH_ISDASOIL_USERNAME"],
        os.environ["AGRITECH_ISDASOIL_PASSWORD"],
    )
    rows, raw = [], {}
    try:
        for name, lat, lon in args.point:
            for depth in DEPTHS:
                for prop in PROPERTIES:
                    payload = client.fetch(float(lat), float(lon), depth, prop)
                    raw[f"{name}_{depth}_{prop}"] = payload
                    value = parse_property(payload, prop, depth)
                    rows.append(
                        {"point": name, "lat": lat, "lon": lon, **asdict(value)}
                    )
                    logger.info("%s %s cm %s: %s", name, depth, prop, value)
    finally:
        client.close()

    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / "isdasoil_points.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.out / "isdasoil_raw.json").write_text(
        json.dumps(raw, indent=2), encoding="utf-8"
    )
    received = sum(row["value"] is not None for row in rows)
    logger.info("%d values received out of %d", received, len(rows))


if __name__ == "__main__":
    main()
