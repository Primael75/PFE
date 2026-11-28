"""Call weather_forecast twice through MCP, as an agent would, and time it.

The second call must come from the cache: Open-Meteo is asked once.

    uv run python scripts/call_weather.py --latitude 9.34 --longitude 2.63 --days 3
"""

import argparse
import asyncio
import logging
import time

from fastmcp import Client

from agritech.sowing import weather_mcp_server

logger = logging.getLogger("call_weather")


async def call(latitude: float, longitude: float, days: int) -> None:
    arguments = {"latitude": latitude, "longitude": longitude, "days": days}
    async with Client(weather_mcp_server.mcp) as client:
        for attempt in ("first call", "second call"):
            started = time.perf_counter()
            result = await client.call_tool(
                "weather_forecast", arguments, raise_on_error=False
            )
            elapsed = time.perf_counter() - started
            logger.info("%s: %.3f s", attempt, elapsed)
            if result.is_error:
                raise SystemExit(result.content[0].text)
        logger.info("%s", result.content[0].text)
    logger.info("Open-Meteo asked %d time(s)", weather_mcp_server.client.api_calls)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for noisy in ("httpx", "httpx2", "mcp", "fastmcp"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, default=9.34)
    parser.add_argument("--longitude", type=float, default=2.63)
    parser.add_argument("--days", type=int, default=3)
    args = parser.parse_args()
    asyncio.run(call(args.latitude, args.longitude, args.days))


if __name__ == "__main__":
    main()
