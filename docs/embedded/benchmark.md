# MD1: which drone, MCP server and vision model to start from

Owner: Mamadou (embedded axis). Sprint 2 plan, task MD1.

**Done when:** a comparison where every line has its source, and a
recommendation shared with the group.

**Verdict:** start from a PX4 quadcopter (the used F450 + Pixhawk 4 lot,
250 EUR) and the `hieutachi/mavlink-mcp` server: read-only first, then full
control of the drone by the agent on the same server. Run no model on the
drone: the drone takes the photos, the phone
does the computing. One point for the group: the sprint plan names the
Crazyflie, which cannot run PX4 (see "Decision for the group").

## What the drone must do: 11 must-haves

The drone works outdoors, over real parcels in northern Benin. Its main job
is a survey: a back-and-forth flight that photographs the whole parcel. Our
working figures, all estimates to confirm: 50 m of height, about 4 to 5 ha
per battery, a 90 m ceiling (the stricter of two Benin limits found, neither
confirmed by the ANAC text).

| # | Must-have | Why |
| --- | --- | --- |
| 1 | Our agents can fully control it | The goal: the agent starts the motors, takes off, flies the mission and lands, through MCP tools |
| 2 | Speaks MAVLink (PX4 or ArduPilot autopilot) | The standard drone protocol: simulation, QGroundControl and the MCP servers use it |
| 3 | The same software runs in simulation | Every flight is tested on a computer first |
| 4 | Its library has a permissive licence | AGENTS.md: we may only import MIT, BSD, Apache-2.0 or ISC code |
| 5 | Flies a GPS route over the parcel by itself | The survey |
| 6 | Holds its line in harmattan wind and gusts | Dry-season flights; our simulation uses 6 m/s with gusts |
| 7 | 90 m ceiling, returns home if the link is lost | Safety over farmland |
| 8 | Carries at least 50 g besides its battery | Pump, tubing and water, or the camera |
| 9 | The autopilot can switch a pump on | Water spraying, only after a person approves |
| 10 | A camera that records where each photo was taken | Parcel maps and stress zones |
| 11 | A radio link that covers the whole field | The MCP server and the safety pilot reach the drone |

Also wanted, not blocking: open firmware, room for a Raspberry Pi, 10 min or
more per battery, spare parts easy to find, a prototype around 300 EUR (to
confirm with the group).

## Drones compared

`OK` met, `X` missing, `~` partly or with an add-on, `?` not published.

| # | Tello EDU | Crazyflie 2.1 Brushless | F450 + Pixhawk 4 (used lot) | Holybro S500 V2 kit |
| --- | --- | --- | --- | --- |
| 1 agents | OK | OK | OK | OK |
| 2 MAVLink | X | X (own protocol) | OK | OK |
| 3 simulation | X | ~ own simulator, not PX4 | OK | OK |
| 4 licence | OK (MIT) | ~ library under GPL | OK | OK |
| 5 GPS route | X no GPS | X no GPS | OK | OK |
| 6 wind | X 87 g | X 37 g | ~ to measure | ~ to measure |
| 7 ceiling, return | X | X | OK | OK |
| 8 payload | X | X 40 g | OK (estimate) | OK 1,500 g |
| 9 pump output | X | ? | OK | OK |
| 10 geotagged camera | ~ no GPS tag | ~ camera toolchain gone | ~ add a Pi camera | ~ add a Pi camera |
| 11 radio range | X Wi-Fi | ~ range not checked | OK telemetry and RC in the lot | OK SiK radio |
| **Price** | 89-172 EUR used | about 710 EUR with radio and deck | 250 EUR | USD 549, in stock |
| **Must-haves met** | **2 / 11** | **1 / 11** | **9 / 11** | **9 / 11** |
| Sources | [specs](https://www.ryzerobotics.com/tello-edu/specs), [used prices](https://www.ebay.fr/sch/i.html?_nkw=dji+tello+drone), [DJITelloPy licence](https://github.com/damiafuentes/DJITelloPy/blob/master/LICENSE.txt) | [specs](https://www.bitcraze.io/products/crazyflie-2-1-brushless/), [price](https://www.generationrobots.com/en/404391-crazyflie-21-brushless.html), [Crazyradio](https://store.bitcraze.io/collections/kits), [cflib licence](https://github.com/bitcraze/crazyflie-lib-python/blob/master/LICENSE.txt), [camera toolchain](https://github.com/bitcraze/aideck-gap8-examples) | seller's ad (250 EUR, contents to confirm), [Pixhawk 4 in PX4](https://docs.px4.io/main/en/flight_controller/pixhawk4), [PX4 actuators](https://docs.px4.io/main/en/payloads/generic_actuator_control) | [kit](https://holybro.com/products/s500-v2-development-kit), [PX4 licence](https://github.com/PX4/PX4-Autopilot/blob/main/LICENSE), [MAVSDK-Python licence](https://github.com/mavlink/MAVSDK-Python/blob/main/LICENSE.txt) |

- **Small SDK drones** (Tello EDU, also RoboMaster TT and CoDrone EDU): cheap
  and easy to program, but no GPS, no MAVLink, too light for wind, nothing to
  carry a pump. Tello and RoboMaster are no longer sold new; the CoDrone
  library has no licence.
- **Research drones** (Crazyflie 2.1+ and Brushless): open and very precise in
  a lab, but no GPS, 15 to 40 g of payload
  ([Crazyflie 2.1+](https://www.bitcraze.io/products/crazyflie-2-1-plus/)), and a GPL Python library that our
  code cannot import. The AI-deck camera needs a tool that can no longer be
  downloaded (its maker, GreenWaves, was liquidated in 2025).
- **PX4 kits**: GPS missions, ceiling and return home, a sprayer output,
  payload to spare, MAVSDK under BSD-3. Two points to close: wind tolerance is
  not published (measure it on the first flights), and the camera must be
  added. Pixhawk 4 is discontinued but still built by PX4 v1.18
  ([releases](https://github.com/PX4/PX4-Autopilot/releases)). The X500 V2
  kit (USD 609) is sold out.
- Out of budget: ModalAI Starling 2 Max, from USD 3,200.

## MCP server

MCP is the standard way to give tools to an AI agent. An MCP server for a
drone turns the agent's questions into MAVLink messages.

**Retained: `hieutachi/mavlink-mcp`** (MIT, built on MAVSDK, BSD-3). In
practice:

1. the agent calls `get_telemetry` ("where are you?");
2. the server asks the drone in MAVLink;
3. it answers position, battery, flight mode, GPS, armed or not.

The path to full control, on the same server:

1. **Read** (MD3): read-only is the default (`MAVLINK_MCP_READONLY=true`),
   enforced by the server; the agent reads everything, commands nothing.
2. **Command**: with `MAVLINK_MCP_READONLY=false` the agent gets `arm`,
   `takeoff`, `goto_location`, `fly_mission`, `land`, `return_to_launch`.
3. **Full control**: the agent flies whole missions by itself.

Safeguards stay on at every step: a maximum altitude
(`MAVLINK_MCP_MAX_ALTITUDE_M`, default 50 m, to set to 90) and a soft
geofence around home (`MAVLINK_MCP_GEOFENCE_RADIUS_M`, default 200 m).
`arm` and `takeoff` also ask for `confirm=true`. Risk: one author and mock
tests only, so MD3 starts with a real PX4 simulation run.

| Server | Licence | Read-only | Tested on | Use |
| --- | --- | --- | --- | --- |
| [hieutachi/mavlink-mcp](https://github.com/hieutachi/mavlink-mcp) | MIT | by default; full control when switched off | mocks only | retained |
| [PeterJBurke/droneserver](https://github.com/PeterJBurke/droneserver) | MIT | yes, without an API key | ArduPilot simulation, nightly | fallback; remove its unlicensed `mcp-server` dependency |
| [ion-g-ion/MAVLinkMCP](https://github.com/ion-g-ion/MAVLinkMCP) | MIT | no | PX4 simulation | no safety gate |
| drone-sim (our prototype) | project | today the agent cannot arm or approve | ArduPilot, Gazebo and AirSim | reference |

13 other servers were excluded because they have no licence file. No MCP
server exists for the Crazyflie.

## Where the agents run, and which models

| Piece | Runs where | Model |
| --- | --- | --- |
| Coordinator and axis agents (Sowing, Diagnosis, Markets) | Fred v3.13.0 (ADR-0001), one Agritech pod (ADR-0002), on the shared instance: k3d on Messan's computer, reached through Tailscale (`docs/sprints/s1/messan.md`) | A language model through the LiteLLM gateway: Mistral Small 4 by default, GPT-5 mini for comparison (ADR-0002, proposed; the final model is chosen in sprint 2). The H-T4 trial used `mistral-medium-latest` and `pixtral-12b-2409` |
| Drone agent (proposed) | The same Agritech pod, so the coordinator can call it | The same gateway and model |
| `mavlink-mcp` server | A ground-station laptop at the field, wired to the telemetry radio; Fred reaches it over the network (Tailscale, to test) | None |
| Autopilot (PX4) | On the drone (Pixhawk) | None: it keeps the drone stable, flies the mission, applies the failsafes |
| Photo diagnosis | The phone browser (ONNX Runtime Web) | MobileNetV3-Large, team 2 |
| Drone camera | A Raspberry Pi on the drone (to add) | None |

- **The agent never flies in real time.** It sends high-level orders (take
  off, fly this mission, land) and reads the result. PX4 keeps the drone
  stable and returns home on its own if the link or the agent drops.
- **Drone tools go on their own agent.** Fred refuses to start an agent if
  one of its MCP servers cannot be reached (`docs/trials/ht4-photo-tool.md`):
  with the drone tools on an axis agent, that agent would stop whenever the
  drone is off.
- **A connection is needed in the field.** The language model runs at the
  provider, and the platform does not work offline (ADR-0001); a 4G link at
  the parcel is to check. The shared instance also needs Messan's computer
  to stay on.
- As everywhere in the project, the language model produces no figure: every
  number comes from a tool (AGENTS.md).

## Vision

- **The drone takes the photos**, with a geotagged camera. Nothing is
  computed on board.
- **The phone does the computing**: team 2's model (MobileNetV3-Large,
  `diagnose_photo`) analyses a photo in 51.5 ms in the phone browser
  (`docs/trials/ht2-latency.md`). That figure was measured on leaf photos
  taken with the phone, not yet on photos from the drone.
- Excluded: Ultralytics YOLO (AGPL-3.0) and YOLO-NAS (weights for
  non-commercial use only).
- If a model must run on the drone later: EfficientNet-Lite0 in 8-bit on a
  Raspberry Pi (Apache-2.0; loses 0.7 points of accuracy in 8-bit).

## Decision for the group

The sprint plan says "Crazyflie retained subject to confirmation, PX4
simulation". The two do not fit: the Crazyflie does not run PX4 and has no
GPS, so it cannot survey a parcel. This benchmark recommends the PX4 kit; the
group decides, then a new ADR-0004 (embedded axis, not written yet) records
it.

## What is verified

| Level | What |
| --- | --- |
| Tested by us | In the drone-sim prototype, kept outside this repository until ADR-0004: the agent flies a survey in simulation (ArduPilot with Gazebo and AirSim): take-off by a person, survey proposed by the agent, approved, flown, return and landing; drift in a 6 m/s wind with gusts: 1.24 m in Gazebo, 0.70 m in AirSim |
| Read at the source | Licences (LICENSE files), payloads, prices and stock (store pages), Pixhawk 4 support in PX4 v1.18, the end of the GAP8 toolchain |
| Not verified | The used lot's contents; the F450's payload and flight time (estimates); wind tolerance of every kit; anything on PX4 itself (our simulation runs ArduPilot); the 90 m Benin ceiling (ANAC text needed); shipping and customs to Benin |

## Open points

1. The used lot: are the ESCs and a receiver included, is the Pixhawk 4
   genuine, which batteries and which telemetry band (433 or 915 MHz)?
2. Wind and flight time with the pump or the camera on board: measure them.
3. Pre-trained model weights carry ImageNet and COCO terms (open in H-T3).
4. Budget: confirm the 300 EUR order of magnitude with the group.
5. Network path from the field to Fred (ground-station laptop, Tailscale,
   4G coverage at the parcel): to test before the first real flight.

## Sources

- Drones: [Ryze Tello EDU](https://www.ryzerobotics.com/tello-edu/specs),
  [Crazyflie 2.1 Brushless](https://www.bitcraze.io/products/crazyflie-2-1-brushless/),
  [Generation Robots price](https://www.generationrobots.com/en/404391-crazyflie-21-brushless.html),
  [Holybro S500 V2](https://holybro.com/products/s500-v2-development-kit),
  [Holybro X500 V2](https://holybro.com/products/px4-development-kit-x500-v2),
  [PX4 Pixhawk 4](https://docs.px4.io/main/en/flight_controller/pixhawk4),
  [PX4 actuators](https://docs.px4.io/main/en/payloads/generic_actuator_control),
  [ModalAI Starling](https://www.modalai.com/pages/starlings),
  [CoDrone EDU](https://www.robolink.com/codrone-edu/).
- Licences: [PX4](https://github.com/PX4/PX4-Autopilot/blob/main/LICENSE),
  [MAVSDK-Python](https://github.com/mavlink/MAVSDK-Python/blob/main/LICENSE.txt),
  [cflib](https://github.com/bitcraze/crazyflie-lib-python/blob/master/LICENSE.txt),
  [DJITelloPy](https://github.com/damiafuentes/DJITelloPy/blob/master/LICENSE.txt),
  [pymavlink](https://github.com/ArduPilot/pymavlink/blob/master/COPYING).
- Crazyflie camera: [aideck-gap8-examples](https://github.com/bitcraze/aideck-gap8-examples).
- Vision: [EfficientNet-Lite](https://github.com/tensorflow/tpu/blob/master/models/official/efficientnet/lite/README.md),
  [ultralytics](https://github.com/ultralytics/ultralytics),
  [YOLO-NAS licence](https://github.com/Deci-AI/super-gradients/blob/master/LICENSE.YOLONAS.md).
