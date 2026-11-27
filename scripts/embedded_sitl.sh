#!/usr/bin/env bash
# PX4 SITL for the embedded trial: stock x500 quadcopter in PX4's default Gazebo
# world, without a window. Run in WSL2 (or Linux) with PX4 built from source.
# Usage: bash scripts/embedded_sitl.sh [mavlink_target_ip]
#   mavlink_target_ip: where mavlink-mcp listens on UDP 14540. Default: the WSL
#   default gateway, which is the Windows host in WSL's NAT mode.
# Env: PX4_DIR (default ~/PX4-Autopilot); GZ_BIN_DIR if `gz` is not on PATH.
set -euo pipefail

px4_dir="${PX4_DIR:-$HOME/PX4-Autopilot}"
[ -n "${GZ_BIN_DIR:-}" ] && export PATH="$GZ_BIN_DIR:$PATH"
target="${1:-$(ip route | awk '/^default/ {print $3; exit}')}"
bin="$px4_dir/build/px4_sitl_default/bin"

command -v gz >/dev/null || { echo "gz (Gazebo Harmonic) not found: set GZ_BIN_DIR" >&2; exit 1; }
[ -x "$bin/px4" ] || { echo "PX4 not built in $px4_dir: run 'make px4_sitl'" >&2; exit 1; }

cd "$px4_dir"
# Daemon mode: without a terminal, PX4's interactive shell would spin.
HEADLESS=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 "$bin/px4" -d &
px4_pid=$!
trap 'kill $px4_pid 2>/dev/null || true' EXIT

until "$bin/px4-mavlink" status >/dev/null 2>&1; do sleep 1; done
# PX4's own API link stays on localhost; this one reaches mavlink-mcp on the target.
"$bin/px4-mavlink" start -x -u 14600 -r 4000000 -o 14540 -t "$target" -m onboard
echo "PX4 SITL running; MAVLink API link to $target:14540"
wait $px4_pid
