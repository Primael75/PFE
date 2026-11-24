"""CHIRPS v3 daily rainfall per commune, with missing days and impossible values.

Usage, from the repository root (needs `uv sync --group rainfall`):
    uv run python scripts/chirps_by_commune.py --tif-dir <GeoTIFFs> \
        --boundaries <geoBoundaries-BEN-ADM2.geojson> --out <folder> \
        --from 1981 --to 2025 --communes Banikoara Gogounou ...

The GeoTIFFs are the yearly Earth Engine exports chirps_v3_benin_<year>.tif.
Writes rainfall_by_commune.csv (one row per commune and day) and
quality_by_commune.csv (one row per commune and year) into --out, outside
Git, and logs the per-commune summary used in docs/data/chirps.md.
"""

import argparse
import csv
import logging
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from agritech.core.logging_config import configure_logging
from agritech.data.chirps import MAX_PLAUSIBLE_MM, read_communes, read_year

logger = logging.getLogger("chirps_by_commune")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tif-dir", type=Path, required=True)
    parser.add_argument("--boundaries", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--from", dest="first", type=int, default=1981)
    parser.add_argument("--to", dest="last", type=int, default=2025)
    parser.add_argument("--max-mm", type=float, default=MAX_PLAUSIBLE_MM)
    parser.add_argument("--communes", nargs="+", required=True)
    args = parser.parse_args()

    geometries = read_communes(args.boundaries, args.communes)
    args.out.mkdir(parents=True, exist_ok=True)
    quality, absent_years, wettest = [], [], 0.0
    with open(args.out / "rainfall_by_commune.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["commune", "date", "rain_mm", "valid_pixels"])
        for year in range(args.first, args.last + 1):
            path = args.tif_dir / f"chirps_v3_benin_{year}.tif"
            if not path.exists():
                absent_years.append(year)
                continue
            days, year_quality = read_year(path, year, geometries, args.max_mm)
            quality += year_quality
            for d in days:
                rain = "" if d.rain_mm is None else f"{d.rain_mm:.3f}"
                writer.writerow([d.commune, d.day.isoformat(), rain, d.valid_pixels])
                wettest = max(wettest, d.rain_mm or 0.0)

    with open(args.out / "quality_by_commune.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(quality[0])))
        writer.writeheader()
        writer.writerows(asdict(q) for q in quality)

    per_commune = defaultdict(list)
    for q in quality:
        per_commune[q.commune].append(q)
    logger.info("Years without a file: %s", absent_years or "none")
    logger.info("Wettest commune-day: %.1f mm", wettest)
    logger.info(
        "| Commune | Pixels | Mean annual total (mm) | Missing days | Impossible values |"
    )
    for name, rows in sorted(per_commune.items()):
        mean_total = sum(r.total_mm for r in rows) / len(rows)
        logger.info(
            "| %s | %d | %.0f | %d | %d |",
            name,
            rows[0].pixels,
            mean_total,
            sum(r.missing_days for r in rows),
            sum(r.impossible_values for r in rows),
        )


if __name__ == "__main__":
    main()
