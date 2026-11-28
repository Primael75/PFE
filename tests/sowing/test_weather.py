"""weather_forecast without the network: a recorded response and fake transports."""

import json
from datetime import date, timedelta
from pathlib import Path

import httpx2
import pytest
from fastmcp import Client

from agritech.sowing import weather_mcp_server
from agritech.sowing.weather import (
    CACHE_SECONDS,
    ForecastError,
    OpenMeteoClient,
    check_point,
    parse_forecast,
)

RECORDED = Path(__file__).parent / "data" / "open_meteo_parakou.json"
PARAKOU = (9.34, 2.63)


def two_days(**changes) -> dict:
    """A small Open-Meteo response, values chosen by hand."""
    daily = {
        "time": ["2026-11-28", "2026-11-29"],
        "precipitation_sum": [0.0, 4.2],
        "temperature_2m_max": [34.6, 31.0],
        "temperature_2m_min": [20.3, 21.5],
    }
    daily.update(changes)
    return {"daily": daily}


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def fake_api(payload: dict, requests: list) -> httpx2.MockTransport:
    def handler(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(200, json=payload)

    return httpx2.MockTransport(handler)


# Parsing, cases computed by hand


def test_two_days_give_six_values_in_order() -> None:
    values = parse_forecast(two_days(), days=2)
    assert [(v.variable, v.as_of, v.value, v.unit) for v in values] == [
        ("precipitation_sum", date(2026, 11, 28), 0.0, "mm"),
        ("precipitation_sum", date(2026, 11, 29), 4.2, "mm"),
        ("temperature_2m_max", date(2026, 11, 28), 34.6, "°C"),
        ("temperature_2m_max", date(2026, 11, 29), 31.0, "°C"),
        ("temperature_2m_min", date(2026, 11, 28), 20.3, "°C"),
        ("temperature_2m_min", date(2026, 11, 29), 21.5, "°C"),
    ]
    assert {v.source.name for v in values} == {"Open-Meteo, CC BY 4.0"}


def test_fewer_days_asked_keeps_the_first_ones() -> None:
    values = parse_forecast(two_days(), days=1)
    assert len(values) == 3
    assert {v.as_of for v in values} == {date(2026, 11, 28)}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        two_days(time=["2026-11-28"]),
        two_days(precipitation_sum=None),
        two_days(temperature_2m_min=[20.3]),
        two_days(temperature_2m_max=[34.6, None]),
    ],
)
def test_missing_data_raises_instead_of_inventing(payload: dict) -> None:
    with pytest.raises(ForecastError):
        parse_forecast(payload, days=2)


@pytest.mark.parametrize(
    ("latitude", "longitude", "days"),
    [(91, 2.6, 14), (9.3, -181, 14), (9.3, 2.6, 0), (9.3, 2.6, 15)],
)
def test_bad_request_is_refused(latitude: float, longitude: float, days: int) -> None:
    with pytest.raises(ForecastError):
        check_point(latitude, longitude, days)


# Recorded response


def test_recorded_response_gives_14_consecutive_days() -> None:
    values = parse_forecast(json.loads(RECORDED.read_text(encoding="utf-8")), days=14)
    assert len(values) == 3 * 14
    rain = [v for v in values if v.variable == "precipitation_sum"]
    first = rain[0].as_of
    assert [v.as_of for v in rain] == [first + timedelta(days=i) for i in range(14)]
    assert all(v.value >= 0 for v in rain)
    by_day = {}
    for v in values:
        by_day.setdefault(v.as_of, {})[v.variable] = v.value
    assert all(
        d["temperature_2m_min"] <= d["temperature_2m_max"] for d in by_day.values()
    )


# HTTP call and cache


def test_request_asks_rain_and_temperature_in_local_time() -> None:
    requests: list = []
    client = OpenMeteoClient(transport=fake_api(two_days(), requests))
    client.forecast(*PARAKOU, days=2)
    params = requests[0].url.params
    assert params["daily"] == "precipitation_sum,temperature_2m_max,temperature_2m_min"
    assert params["forecast_days"] == "2"
    assert params["timezone"] == "auto"


def test_two_close_calls_ask_open_meteo_once() -> None:
    requests: list = []
    clock = FakeClock()
    client = OpenMeteoClient(transport=fake_api(two_days(), requests), clock=clock)
    first = client.forecast(*PARAKOU, days=2)
    clock.now = 60  # one minute later, a point 300 m away
    second = client.forecast(9.342, 2.632, days=2)
    assert client.api_calls == 1
    assert second == first


def test_cache_expires_after_three_hours() -> None:
    requests: list = []
    clock = FakeClock()
    client = OpenMeteoClient(transport=fake_api(two_days(), requests), clock=clock)
    client.forecast(*PARAKOU, days=2)
    clock.now = CACHE_SECONDS + 1
    client.forecast(*PARAKOU, days=2)
    assert client.api_calls == 2


def test_http_error_is_explicit() -> None:
    transport = httpx2.MockTransport(lambda request: httpx2.Response(503, text="busy"))
    with pytest.raises(ForecastError, match="503"):
        OpenMeteoClient(transport=transport).forecast(*PARAKOU)


def test_unreachable_source_is_explicit() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("no network")

    with pytest.raises(ForecastError, match="unreachable"):
        OpenMeteoClient(transport=httpx2.MockTransport(handler)).forecast(*PARAKOU)


# MCP tool


@pytest.fixture
def recorded_client(monkeypatch: pytest.MonkeyPatch) -> OpenMeteoClient:
    payload = json.loads(RECORDED.read_text(encoding="utf-8"))
    client = OpenMeteoClient(transport=fake_api(payload, []))
    monkeypatch.setattr(weather_mcp_server, "client", client)
    return client


@pytest.mark.anyio
async def test_tool_returns_sourced_values(recorded_client: OpenMeteoClient) -> None:
    async with Client(weather_mcp_server.mcp) as mcp_client:
        result = await mcp_client.call_tool(
            "weather_forecast",
            {"latitude": PARAKOU[0], "longitude": PARAKOU[1], "days": 3},
        )
    values = result.structured_content["values"]
    assert len(values) == 9
    assert values[0]["source"]["name"] == "Open-Meteo, CC BY 4.0"
    assert {"variable", "value", "unit", "source", "as_of"} <= set(values[0])
    assert "Weather data by Open-Meteo.com" in result.content[0].text


@pytest.mark.anyio
async def test_tool_reports_a_bad_request(recorded_client: OpenMeteoClient) -> None:
    async with Client(weather_mcp_server.mcp) as mcp_client:
        result = await mcp_client.call_tool(
            "weather_forecast",
            {"latitude": PARAKOU[0], "longitude": PARAKOU[1], "days": 30},
            raise_on_error=False,
        )
    assert result.is_error
    assert "between 1 and 14" in result.content[0].text
