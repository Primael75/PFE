"""Embedded trial: read a simulated drone through mavlink-mcp, read-only.

Starts the mavlink-mcp server over stdio with MAVLINK_MCP_READONLY=true,
reads the drone state, times the read tools, then checks that every tool
able to move the drone is rejected. See docs/trials/embedded-sitl.md.

Usage, with PX4 SITL running (scripts/embedded_sitl.sh):
    uv run python scripts/measure_embedded_sitl.py --server /path/to/mavlink-mcp
"""

import argparse
import asyncio
import json
import logging
import statistics
import time
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

logger = logging.getLogger("measure_embedded_sitl")

READ_TOOLS = ("get_telemetry", "get_flight_mode")
# One call per tool that can move the drone, with arguments that would pass every
# other check: only the read-only guard should stop them.
ACTION_CALLS = {
    "arm": {"confirm": True},
    "disarm": {},
    "takeoff": {"altitude_m": 10.0, "confirm": True},
    "land": {},
    "hold": {},
    "return_to_launch": {},
    "goto_location": {
        "latitude_deg": 47.3977,
        "longitude_deg": 8.5456,
        "relative_altitude_m": 10.0,
    },
    "fly_mission": {
        "waypoints": [
            {
                "latitude_deg": 47.3977,
                "longitude_deg": 8.5456,
                "relative_altitude_m": 10.0,
            }
        ]
    },
}


def payload(result) -> dict:
    if result.structured_content is not None:
        return result.structured_content
    return json.loads(result.content[0].text)


async def timed_call(client: Client, tool: str, arguments: dict) -> tuple[float, dict]:
    started = time.perf_counter()
    result = await client.call_tool(tool, arguments, raise_on_error=False)
    return (time.perf_counter() - started) * 1000, payload(result)


def summary(durations: list[float]) -> str:
    ordered = sorted(durations)
    p95 = ordered[max(0, round(0.95 * len(ordered)) - 1)]
    return (
        f"min {ordered[0]:.0f} ms, median {statistics.median(ordered):.0f} ms, "
        f"p95 {p95:.0f} ms, max {ordered[-1]:.0f} ms"
    )


async def run_trial(server: str, url: str, runs: int, server_log: str | None) -> bool:
    env = {"MAVLINK_MCP_READONLY": "true", "MAVLINK_MCP_URL": url}
    transport = StdioTransport(
        command=server,
        args=[],
        env=env,
        log_file=Path(server_log) if server_log else None,
    )
    async with Client(transport) as client:
        tools = sorted(tool.name for tool in await client.list_tools())
        logger.info("Tools listed by the server (%d): %s", len(tools), ", ".join(tools))

        first_ms, telemetry = await timed_call(client, "get_telemetry", {})
        logger.info(
            "First get_telemetry (includes the MAVLink connection): %.0f ms", first_ms
        )
        logger.info("Drone state: %s", json.dumps(telemetry))
        _, status = await timed_call(client, "get_connection_status", {})
        logger.info("Connection status: %s", json.dumps(status))

        for tool in READ_TOOLS:
            durations = [(await timed_call(client, tool, {}))[0] for _ in range(runs)]
            logger.info("%s, %d calls: %s", tool, runs, summary(durations))

        all_rejected = True
        for tool, arguments in ACTION_CALLS.items():
            _, answer = await timed_call(client, tool, arguments)
            rejected = answer.get("guardrail") is True and "readonly" in answer.get(
                "error", ""
            )
            all_rejected = all_rejected and rejected
            logger.info(
                "%s: %s",
                tool,
                "rejected (read-only)" if rejected else f"NOT REJECTED {answer}",
            )

        # The drone itself must not have moved: still disarmed and on the ground.
        _, after = await timed_call(client, "get_telemetry", {})
        is_untouched = after.get("armed") is False and after.get("in_air") is False
        logger.info(
            "After the action calls: armed %s, in_air %s, flight mode %s",
            after.get("armed"),
            after.get("in_air"),
            after.get("flight_mode"),
        )
        return all_rejected and is_untouched


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--server", default="mavlink-mcp", help="mavlink-mcp executable"
    )
    parser.add_argument(
        "--url", default="udpin://0.0.0.0:14540", help="MAVLink endpoint"
    )
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument(
        "--server-log", help="file for the server's own log (default: stderr)"
    )
    args = parser.parse_args()

    if not asyncio.run(run_trial(args.server, args.url, args.runs, args.server_log)):
        raise SystemExit("An action tool was not rejected: read-only mode failed")
    logger.info("Verdict: drone state read, every action tool rejected")


if __name__ == "__main__":
    main()
