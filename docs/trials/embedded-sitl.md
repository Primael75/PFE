# Embedded trial: an agent reads a simulated drone through MCP, read-only

Embedded axis. Sprint 2, task MD3, due 3 December.

The chain agent -> MCP -> MAVLink -> drone is tried on a simulated PX4
quadcopter before any hardware is bought. The MCP server is
`hieutachi/mavlink-mcp`, retained by the benchmark
(`docs/embedded/benchmark.md`), run in read-only mode.

**Done when:** an agent gets the state of the simulated drone (position,
battery, flight mode), with no action command enabled.

**Verdict (27 November 2026): passed.** The state is read in 2.0 s at p95,
under the 3-second limit of ENF-01; the 8 tools able to move the drone are
all rejected, and the drone stays disarmed on the ground.

## Setup

```text
Windows 11                                        WSL2, Debian 13
+------------------------+  stdio  +-------------+  MAVLink  +----------------------+
| agent (MCP client)     | <-----> | mavlink-mcp | <-------- | PX4 SITL v1.18.0     |
| measure_embedded_sitl  |  (MCP)  | read-only   |  UDP      | x500 in Gazebo 8.10  |
+------------------------+         +-------------+  14540    | default world, no UI |
                                                             +----------------------+
```

| Part | Version | Licence | Where it runs |
| --- | --- | --- | --- |
| PX4 Autopilot, SITL | v1.18.0, built from source | BSD-3-Clause | WSL2 |
| Gazebo Harmonic (gz-sim) | 8.10.0, conda-forge | Apache-2.0 | WSL2, headless |
| `hieutachi/mavlink-mcp` | commit `fb0324d` (0.1.0) | MIT | Windows, own virtual environment |
| MAVSDK-Python (inside mavlink-mcp) | 3.17.4 | BSD-3-Clause | same |
| fastmcp (inside mavlink-mcp) | 2.14.7 | Apache-2.0 | same |
| MCP client (`scripts/measure_embedded_sitl.py`) | fastmcp 4.2.4, mcp 2.3.0 | Apache-2.0, MIT | Windows, project environment |

mavlink-mcp needs fastmcp 2, the project pins fastmcp 4 (aligned with
Fred): the server runs as a separate service in its own environment and
adds no dependency to `pyproject.toml`.

## Run it again

PX4 must be built once in WSL2 or Linux (`make px4_sitl` in
`PX4-Autopilot`, see the [PX4 Gazebo guide](https://docs.px4.io/main/en/sim_gazebo_gz/)),
with Gazebo Harmonic installed.

1. Install mavlink-mcp in its own environment (Windows shown; same on Linux):

   ```bash
   git clone https://github.com/hieutachi/mavlink-mcp.git
   cd mavlink-mcp
   uv venv --python 3.12 .venv
   uv pip install -e .
   ```

2. Start PX4 SITL in WSL2. It sends MAVLink to the Windows host on UDP
   14540 (on a single Linux machine, pass `127.0.0.1`):

   ```bash
   GZ_BIN_DIR=/path/to/gz/bin bash scripts/embedded_sitl.sh
   ```

   Wait for `PX4 SITL running; MAVLink API link to ...:14540`.

3. From the repository root, run the agent's calls and the measures:

   ```bash
   uv run python scripts/measure_embedded_sitl.py \
     --server /path/to/mavlink-mcp/.venv/Scripts/mavlink-mcp.exe \
     --runs 50 --server-log mavlink-mcp.log
   ```

   On Linux the executable is `.venv/bin/mavlink-mcp`. The script forces
   `MAVLINK_MCP_READONLY=true` and exits with an error if any action tool
   is not rejected or if the drone moved.

Only one program can listen on UDP 14540: stop any other ground station or
MAVSDK client (QGroundControl listens on 14550 and does not conflict).

## MCP tools available

The server lists 12 tools. In read-only mode it rejects the 8 action tools
before anything is sent to the autopilot (`Drone._require_write` runs
before the connection is used).

| Tool | Reads or acts | Result in this trial |
| --- | --- | --- |
| `get_capabilities` | reads | capabilities and active guardrails |
| `get_connection_status` | reads | `connected: true`, `readonly: true` |
| `get_telemetry` | reads | position, attitude, battery, GPS, mode, armed, in air |
| `get_flight_mode` | reads | `HOLD` |
| `arm` | acts | rejected (read-only) |
| `disarm` | acts | rejected (read-only) |
| `takeoff` | acts | rejected (read-only) |
| `land` | acts | rejected (read-only) |
| `hold` | acts | rejected (read-only) |
| `return_to_launch` | acts | rejected (read-only) |
| `goto_location` | acts | rejected (read-only) |
| `fly_mission` | acts | rejected (read-only) |

`arm` and `takeoff` were called with `confirm=true` and `goto_location` and
`fly_mission` with a point 50 m from home at 10 m: only the read-only guard
could stop them. After these 8 calls, `get_telemetry` gives `armed: false`,
`in_air: false`, mode `HOLD`.

## Results

Run of 27 November 2026, 12:14 UTC, on the setup above (one laptop).

### Drone state read by the agent

| Field | Value |
| --- | --- |
| Position | 47.3979711 N, 8.5461639 E (PX4's default home, Zurich) |
| Height above home | 0.045 m |
| Battery | 16.2 V, 100 % |
| GPS | 3D fix, 10 satellites |
| Flight mode | `HOLD` |
| Armed / in air | no / no |

Asked "where is the drone and what state is it in?", the agent (Claude,
acting as the MCP client of this trial) called `get_telemetry` and
answered from it: on the ground at PX4's default home, disarmed, in
`HOLD`, battery full, GPS 3D fix with 10 satellites. Every figure in the
answer comes from the tool.

### Response times

50 calls of each read tool, measured from the client, MCP over stdio
included.

| Tool | Min | Median | p95 | Max |
| --- | ---: | ---: | ---: | ---: |
| `get_telemetry` | 867 ms | 2,025 ms | 2,027 ms | 2,028 ms |
| `get_flight_mode` | 1,011 ms | 1,013 ms | 1,014 ms | 1,015 ms |

The first `get_telemetry` of a session also opens the MAVLink connection:
5,982 ms, 2,091 ms and 1,450 ms on three runs.

**Why 1 and 2 seconds.** At each call the server subscribes again to each
MAVSDK stream and waits for its next message. Measured directly with
MAVSDK on the same PX4: position, attitude and GPS arrive within 30 ms,
flight mode and armed state about every 1 s (the heartbeat), the battery
state about every 2 s. `get_telemetry` waits for all seven, so for the
battery. The time is set by PX4's message rates, not by the agent or MCP.
A server that kept the streams open and returned the last values would
answer in milliseconds; not needed for ENF-01.

## Problems found

| Problem | Impact | Handling |
| --- | --- | --- |
| Client (mcp 2.3) and server (mcp 1.30) speak different MCP versions: the server logs 34 validation errors for the client's first `server/discover` request, then the session falls back to the older handshake | Noise only: every call works | Server log sent to a file (`--server-log`) |
| mavlink-mcp pins fastmcp 2, the project fastmcp 4 | Cannot share the project environment | Separate service, own environment |
| mavlink-mcp only speaks stdio | Fred calls MCP servers over streamable HTTP | Open point for sprint 3, below |
| One author, 2 stars, mock tests only before this trial | Risk of bugs on real hardware | Its 52 tests pass; this trial is its first run on a real PX4 SITL |

## Deviations from the task

| What | Why | Impact |
| --- | --- | --- |
| The agent is Claude driving an MCP client script, not a Fred agent | Agents are plugged into Fred in sprint 3 (sprint 2 plan); the script makes the trial repeatable | The same MCP calls a Fred agent will make; the Fred side is not tested |
| The MCP server is not the one of `drone-sim`, the axis prototype | The task asks for an existing server retained by the benchmark; drone-sim's own server can start missions | drone-sim stays a reference; nothing of it is needed here |

## Open points

- **Fred (sprint 3):** expose mavlink-mcp over streamable HTTP (fastmcp can
  serve the same tools over HTTP) and declare it in Fred; to try.
- **Hardware (ADR-0004):** the trial says nothing about the airframe; the
  same chain works for any PX4 vehicle speaking MAVLink.
- **Actions:** enabling `MAVLINK_MCP_READONLY=false` is a later step, under
  the rules decided by the team (explicit authorisation before any
  physical action).
