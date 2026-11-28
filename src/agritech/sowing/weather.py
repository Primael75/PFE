"""Daily weather forecast at a point, from Open-Meteo (EF-14).

Rain and temperature, day by day, for up to 14 days. Every value is a
`ForecastValue`: the common `SourcedValue` plus the name of the variable,
since rain and the two temperatures would otherwise be told apart only by
their unit. Responses are cached, so that two close calls ask Open-Meteo once.

`parse_forecast` is pure; `OpenMeteoClient` does the HTTP call and the cache.
"""

import logging
import time
from collections.abc import Callable
from datetime import date

import httpx2

from agritech.core.tool_output import Source, SourcedValue

logger = logging.getLogger(__name__)

API_URL = "https://api.open-meteo.com/v1/forecast"
SOURCE = Source(name="Open-Meteo, CC BY 4.0", url="https://open-meteo.com/")
MAX_DAYS = 14
# Open-Meteo updates its models every few hours: a 3-hour cache keeps the
# forecast fresh and spares the free API (fewer than 10,000 calls a day).
CACHE_SECONDS = 3 * 3600
TIMEOUT_SECONDS = 10.0

# Open-Meteo daily variable -> unit returned. All three are required.
VARIABLES = {
    "precipitation_sum": "mm",
    "temperature_2m_max": "°C",
    "temperature_2m_min": "°C",
}


class ForecastError(Exception):
    """Explicit error: bad request, source unreachable or data missing (ENF-03)."""


class ForecastValue(SourcedValue):
    """One variable on one day. `as_of` is the forecast day."""

    variable: str


def check_point(latitude: float, longitude: float, days: int) -> None:
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ForecastError(
            f"Invalid point: latitude {latitude}, longitude {longitude}."
        )
    if not 1 <= days <= MAX_DAYS:
        raise ForecastError(f"days must be between 1 and {MAX_DAYS}, not {days}.")


def parse_forecast(payload: dict, days: int) -> list[ForecastValue]:
    """Turn an Open-Meteo response into one value per day and variable.

    A missing variable or day raises `ForecastError`: no value is invented.
    """
    daily = payload.get("daily")
    if not isinstance(daily, dict) or not isinstance(daily.get("time"), list):
        raise ForecastError("Open-Meteo returned no daily forecast.")
    dates = daily["time"]
    if len(dates) < days:
        raise ForecastError(f"Open-Meteo returned {len(dates)} days, {days} asked.")

    values = []
    for variable, unit in VARIABLES.items():
        series = daily.get(variable)
        if not isinstance(series, list) or len(series) < days:
            raise ForecastError(f"Open-Meteo returned no {variable}.")
        for day, value in zip(dates[:days], series[:days], strict=True):
            if value is None:
                raise ForecastError(f"Open-Meteo has no {variable} for {day}.")
            values.append(
                ForecastValue(
                    variable=variable,
                    value=value,
                    unit=unit,
                    source=SOURCE,
                    as_of=date.fromisoformat(day),
                )
            )
    return values


class OpenMeteoClient:
    """Calls Open-Meteo and keeps each answer for `cache_seconds`.

    Two points closer than about 1 km (0.01 degree) share the cache entry.
    """

    def __init__(
        self,
        transport: httpx2.BaseTransport | None = None,
        cache_seconds: float = CACHE_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._client = httpx2.Client(transport=transport, timeout=TIMEOUT_SECONDS)
        self._cache_seconds = cache_seconds
        self._clock = clock
        self._cache: dict[
            tuple[float, float, int], tuple[float, list[ForecastValue]]
        ] = {}
        self.api_calls = 0  # read by the tests and the logs

    def close(self) -> None:
        self._client.close()

    def forecast(
        self, latitude: float, longitude: float, days: int = MAX_DAYS
    ) -> list[ForecastValue]:
        check_point(latitude, longitude, days)
        key = (round(latitude, 2), round(longitude, 2), days)
        cached = self._cache.get(key)
        if cached is not None and self._clock() < cached[0]:
            logger.info("weather_forecast %s: from cache", key)
            return cached[1]

        values = parse_forecast(self._fetch(*key), days)
        self._cache[key] = (self._clock() + self._cache_seconds, values)
        return values

    def _fetch(self, latitude: float, longitude: float, days: int) -> dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": ",".join(VARIABLES),
            "forecast_days": days,
            "timezone": "auto",  # days counted in local time at the point
        }
        self.api_calls += 1
        try:
            response = self._client.get(API_URL, params=params)
        except httpx2.HTTPError as error:
            raise ForecastError(
                f"Open-Meteo is unreachable: {error.__class__.__name__}."
            ) from error
        if response.status_code != 200:
            raise ForecastError(
                f"Open-Meteo answered HTTP {response.status_code}: {response.text[:200]}"
            )
        try:
            return response.json()
        except ValueError as error:
            raise ForecastError("Open-Meteo did not return JSON.") from error
