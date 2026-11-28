# sowing

## Purpose
When to sow: season onset, sowing window and false-start risk per commune.
What to sow: suitability score for maize, sorghum, cassava and cowpea.

## Owner
Team 1 (Sowing).
# sowing

## Purpose
When to sow: season onset, sowing window and false-start risk per commune.
What to sow: suitability score for maize, sorghum, cassava and cowpea.

## Owner
Team 1 (Sowing).

## Provides
Commune maps and season onset dates, to team 3.

## Status
- `onset.py`: season onset date of a daily rainfall series, with the
  Sivakumar (1988) criterion family. Every parameter is a field of
  `OnsetCriterion`, read from the zone profile. Domain code, no I/O.
  Checked on ten hand-built series (H-T1), see `docs/trials/ht1-onset.md`.
- `weather.py`, `weather_mcp_server.py`: MCP tool `weather_forecast`
  (EF-14), see below.
- MCP tools, sowing window and false-start risk: sprint 2.

## Tool `weather_forecast` (EF-14)

Owner: Kelyan (team 2), reviewed by Aissata. Daily rain and temperature
forecast at a point, for the Sowing agent to adjust its advice to the coming
days (EF-13).

### Files

| File | Role |
| --- | --- |
| `weather.py` | `parse_forecast` (pure) and `OpenMeteoClient` (HTTP call and cache) |
| `weather_mcp_server.py` | The MCP tool, case A of the template |
| `tests/sowing/test_weather.py` | 19 tests, no network: a recorded response and fake transports |
| `tests/sowing/data/open_meteo_parakou.json` | Open-Meteo response recorded at Parakou on 28 November 2026, 14 days |
| `scripts/record_open_meteo.py` | Records that response again |
| `scripts/call_weather.py` | Calls the tool twice through MCP and times it |

### Inputs

| Parameter | Type | Meaning |
| --- | --- | --- |
| `latitude` | number | -90 to 90 |
| `longitude` | number | -180 to 180 |
| `days` | integer | 1 to 14, default 14 |

### Output

`structured_content.values`: one `ForecastValue` per day and variable, in
this order: all days of `precipitation_sum` (mm), then `temperature_2m_max`
(°C), then `temperature_2m_min` (°C). `as_of` is the forecast day, in local
time at the point. `source` is `Open-Meteo, CC BY 4.0`
(https://open-meteo.com/). The text read by the model gives one line per day
and the attribution "Weather data by Open-Meteo.com".

A bad request, an unreachable API or a missing value returns an explicit
error (`is_error`), never an invented value (ENF-03).

### Example

```bash
uv run python scripts/call_weather.py --latitude 9.34 --longitude 2.63 --days 3
```

Result on 28 November 2026, from Kelyan's laptop. The script asks
Open-Meteo live, so the values change every day; the times and the line
"Open-Meteo asked 1 time(s)" should stay close:

```text
first call: 0.432 s
second call: 0.007 s
2026-11-28: rain 0.0 mm, min 22.5 °C, max 35.1 °C
2026-11-29: rain 0.0 mm, min 21.8 °C, max 34.9 °C
2026-11-30: rain 0.0 mm, min 19.1 °C, max 34.1 °C
Source: Open-Meteo, CC BY 4.0 (https://open-meteo.com/). Weather data by Open-Meteo.com.
Open-Meteo asked 1 time(s)
```

As an MCP server, for Fred:

```bash
uv run uvicorn agritech.sowing.weather_mcp_server:create_app --factory --port 8079
```

### Cache

Each answer is kept **3 hours** in memory (`CACHE_SECONDS`): Open-Meteo
updates its models every few hours, and the free API allows fewer than
10,000 calls a day (`docs/legal/terms-of-use.md`). Two points closer than
0.01 degree (about 1 km) share an entry. The cache is lost when the server
restarts.

### Response time

Measured on 28 November 2026 on Kelyan's laptop (Intel Core i5-8365U,
16 GB, home connection), with `scripts/call_weather.py`:

| Call | Time |
| --- | --- |
| First call through MCP, Open-Meteo asked over the network | 0.432 s |
| Second call through MCP, from the cache | 0.007 s |
| Open-Meteo alone, 14 days (`scripts/record_open_meteo.py`) | 1.16 s |

Under the 3-second limit of ENF-01. The network time depends on the
connection; the cache removes it for 3 hours.

### Deviations from the template

- **One more field**: each value is a `ForecastValue`, the common
  `SourcedValue` plus `variable`, because rain and the two temperatures would
  otherwise be told apart only by their unit.
- **A list**: the tool returns a list of values in `structured_content`,
  not a single `SourcedValue`, as the sprint 2 plan allows.
- **Own server file**: `weather_mcp_server.py` rather than a shared
  `mcp_server.py`, so that it does not collide with the Sowing tools of
  team 1.

### Limits

- Forecast, not observation: the further the day, the less reliable. No
  uncertainty is given, because Open-Meteo's free daily forecast gives none.
- Nothing in the tool depends on the zone (EF-01): the point is a parameter,
  and days are counted in the point's own time zone (`timezone=auto`).
- Free API for non-commercial use only; a deployment beyond the project
  needs a paid plan (`docs/legal/terms-of-use.md`).

## Provides
Commune maps and season onset dates, to team 3.

## Status
- `onset.py`: season onset date of a daily rainfall series, with the
  Sivakumar (1988) criterion family. Every parameter is a field of
  `OnsetCriterion`, read from the zone profile. Domain code, no I/O.
  Checked on ten hand-built series (H-T1), see `docs/trials/ht1-onset.md`.
- `weather.py`, `weather_mcp_server.py`: MCP tool `weather_forecast`
  (EF-14), see below.
- MCP tools, sowing window and false-start risk: sprint 2.

## Tool `weather_forecast` (EF-14)

Owner: Kelyan (team 2), reviewed by Aissata. Daily rain and temperature
forecast at a point, for the Sowing agent to adjust its advice to the coming
days (EF-13).

### Files

| File | Role |
| --- | --- |
| `weather.py` | `parse_forecast` (pure) and `OpenMeteoClient` (HTTP call and cache) |
| `weather_mcp_server.py` | The MCP tool, case A of the template |
| `tests/sowing/test_weather.py` | 19 tests, no network: a recorded response and fake transports |
| `tests/sowing/data/open_meteo_parakou.json` | Open-Meteo response recorded at Parakou |
| `scripts/record_open_meteo.py` | Records that response again |
| `scripts/call_weather.py` | Calls the tool twice through MCP and times it |

### Inputs

| Parameter | Type | Meaning |
| --- | --- | --- |
| `latitude` | number | -90 to 90 |
| `longitude` | number | -180 to 180 |
| `days` | integer | 1 to 14, default 14 |

### Output

`structured_content.values`: one `ForecastValue` per day and variable, in
this order: all days of `precipitation_sum` (mm), then `temperature_2m_max`
(°C), then `temperature_2m_min` (°C). `as_of` is the forecast day, in local
time at the point. `source` is `Open-Meteo, CC BY 4.0`
(https://open-meteo.com/). The text read by the model gives one line per day
and the attribution "Weather data by Open-Meteo.com".

A bad request, an unreachable API or a missing value returns an explicit
error (`is_error`), never an invented value (ENF-03).

### Example

```bash
uv run python scripts/call_weather.py --latitude 9.34 --longitude 2.63 --days 3
```

Result with the recorded response (values of the day the response was
recorded):

```text
first call: 0.008 s
second call: 0.002 s
2026-11-28: rain 0.0 mm, min 20.3 °C, max 34.6 °C
2026-11-29: rain 0.0 mm, min 20.8 °C, max 35.1 °C
2026-11-30: rain 0.0 mm, min 21.4 °C, max 35.4 °C
Source: Open-Meteo, CC BY 4.0 (https://open-meteo.com/). Weather data by Open-Meteo.com.
Open-Meteo asked 1 time(s)
```

As an MCP server, for Fred:

```bash
uv run uvicorn agritech.sowing.weather_mcp_server:create_app --factory --port 8079
```

### Cache

Each answer is kept **3 hours** in memory (`CACHE_SECONDS`): Open-Meteo
updates its models every few hours, and the free API allows fewer than
10,000 calls a day (`docs/legal/terms-of-use.md`). Two points closer than
0.01 degree (about 1 km) share an entry. The cache is lost when the server
restarts.

### Response time

| Call | Time | Where |
| --- | --- | --- |
| Through MCP, from the cache | 0.002 s | container, recorded response |
| Through MCP, parsing included, network excluded | 0.008 s | container, recorded response |

Under the 3-second limit of ENF-01.

### Deviations from the template

- **One more field**: each value is a `ForecastValue`, the common
  `SourcedValue` plus `variable`, because rain and the two temperatures would
  otherwise be told apart only by their unit.
- **A list**: the tool returns a list of values in `structured_content`,
  not a single `SourcedValue`, as the sprint 2 plan allows.
- **Own server file**: `weather_mcp_server.py` rather than a shared
  `mcp_server.py`, so that it does not collide with the Sowing tools of
  team 1.

### Limits

- Forecast, not observation: the further the day, the less reliable. No
  uncertainty is given, because Open-Meteo's free daily forecast gives none.
- Nothing in the tool depends on the zone (EF-01): the point is a parameter,
  and days are counted in the point's own time zone (`timezone=auto`).
- Free API for non-commercial use only; a deployment beyond the project
  needs a paid plan (`docs/legal/terms-of-use.md`).
