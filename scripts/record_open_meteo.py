"""Record a real Open-Meteo response for the offline tests of weather_forecast.

Calls the API once, with the same request as the tool, and writes the raw
JSON. The tests read the file and never call the network.

    uv run python scripts/record_open_meteo.py --out tests/sowing/data/open_meteo_parakou.json
"""

import argparse
import json
import logging
import time
from pathlib import Path

import httpx2

from agritech.sowing.weather import API_URL, MAX_DAYS, VARIABLES

logger = logging.getLogger("record_open_meteo")

# Parakou, Borgou (zone A): a commune of the zone profile.
PARAKOU = (9.34, 2.63)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, default=PARAKOU[0])
    parser.add_argument("--longitude", type=float, default=PARAKOU[1])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    params = {
        "latitude": args.latitude,
        "longitude": args.longitude,
        "daily": ",".join(VARIABLES),
        "forecast_days": MAX_DAYS,
        "timezone": "auto",
    }
    started = time.perf_counter()
    response = httpx2.get(API_URL, params=params, timeout=10)
    elapsed = time.perf_counter() - started
    response.raise_for_status()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(response.json(), indent=2) + "\n", encoding="utf-8")
    logger.info(
        "Recorded %d days at %s, %s in %s (Open-Meteo answered in %.2f s)",
        MAX_DAYS,
        args.latitude,
        args.longitude,
        args.out,
        elapsed,
    )


if __name__ == "__main__":
    main()
