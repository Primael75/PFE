# embedded

## Purpose
Embedded axis: a drone and field sensors driven by agents through MCP
tools. First goal: an agent reads the state of a simulated drone
(position, battery, flight mode) over MAVLink, without any action command.

## Owner
Embedded axis.

## Provides
No tool of its own yet. The sprint 2 trial uses the existing server
`hieutachi/mavlink-mcp` in read-only mode (see `docs/embedded/benchmark.md`).
The brick's own tools, and the teams they serve, follow ADR-0004.

## Status
Empty. This axis is outside the three axes of ADR-0001; it waits for
ADR-0004 (hardware, safety rules, licences). Sprint 2: read-only state of
a PX4 drone in simulation, see `docs/trials/embedded-sitl.md` (MD3).

## Rules decided by the team
To be recorded in ADR-0004 (`docs/adr/0004-axe-embarque.md`):
- water spraying only;
- indoor flight;
- explicit human authorisation before any physical action.
