"""MCP server of the weather forecast tool (EF-14), case A of the template."""

import logging

from fastmcp import FastMCP
from fastmcp.tools import ToolResult

from agritech.core.logging_config import configure_logging
from agritech.core.tool_output import missing_data
from agritech.sowing.weather import (
    MAX_DAYS,
    ForecastError,
    ForecastValue,
    OpenMeteoClient,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(name="agritech-weather")
client: OpenMeteoClient | None = None  # created on first use, replaced in tests


def _get_client() -> OpenMeteoClient:
    global client
    if client is None:
        client = OpenMeteoClient()
    return client


def _describe(values: list[ForecastValue]) -> str:
    # The model reads this text: one line per day, with the source (EF-04).
    by_day: dict[str, dict[str, float]] = {}
    for item in values:
        by_day.setdefault(item.as_of.isoformat(), {})[item.variable] = item.value
    lines = [
        f"{day}: rain {v['precipitation_sum']} mm, "
        f"min {v['temperature_2m_min']} °C, max {v['temperature_2m_max']} °C"
        for day, v in by_day.items()
    ]
    source = values[0].source
    lines.append(
        f"Source: {source.name} ({source.url}). Weather data by Open-Meteo.com."
    )
    return "\n".join(lines)


@mcp.tool(name="weather_forecast")
def weather_forecast(
    latitude: float, longitude: float, days: int = MAX_DAYS
) -> ToolResult:
    """Daily rain (mm) and minimum and maximum temperature (°C) forecast at a point,
    for 1 to 14 days, from Open-Meteo. Use it to adjust sowing or crop advice to
    the coming days. Each value is dated with its forecast day."""
    try:
        values = _get_client().forecast(latitude, longitude, days)
    except ForecastError as error:
        logger.warning("weather_forecast %s, %s: %s", latitude, longitude, error)
        return missing_data(str(error))
    return ToolResult(
        content=_describe(values),
        structured_content={
            "values": [item.model_dump(mode="json") for item in values]
        },
    )


def create_app():
    """Build the HTTP application served by uvicorn, as Fred will call it."""
    configure_logging()
    return mcp.http_app(path="/mcp", stateless_http=True, json_response=True)


if __name__ == "__main__":
    configure_logging()
    mcp.run()
