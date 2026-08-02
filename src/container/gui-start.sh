#!/usr/bin/env bash
# Starts the in-container GUI stack, then execs the requested command.
#
# A virtual X server plus a window manager plus noVNC is the single universal GUI
# path: identical on macOS, Jetson, cloud and Linux, with no X11 socket bind-mount,
# no DISPLAY plumbing and no VNC client to install. It also gives Gazebo a GLX
# context rather than requiring headless EGL, which has been unreliable here --
# the symptom of EGL failure is /clock silently stalling rather than a clean error.
set -eu

export DISPLAY=":1"
GEOMETRY="${DROID_GEOMETRY:-1920x1080x24}"

Xvfb "$DISPLAY" -screen 0 "$GEOMETRY" +extension GLX +render -noreset >/tmp/xvfb.log 2>&1 &
for _ in $(seq 1 50); do
  xdpyinfo -display "$DISPLAY" >/dev/null 2>&1 && break
  sleep 0.2
done
xdpyinfo -display "$DISPLAY" >/dev/null 2>&1 || {
  echo "droid: virtual X server failed to start; see /tmp/xvfb.log" >&2
  exit 1
}

fluxbox >/tmp/fluxbox.log 2>&1 &
# -localhost is not optional. `-nopw` makes this an UNAUTHENTICATED VNC endpoint
# with full keyboard and mouse control, and without -localhost x11vnc binds
# 0.0.0.0:5900 -- reachable from any sibling container on the compose bridge
# network, and LAN-reachable the moment someone publishes port 5900. Bound to the
# loopback interface it is reachable only by websockify, which is the only thing
# that should ever dial it: it already connects to localhost:5900.
x11vnc -display "$DISPLAY" -forever -shared -nopw -localhost -quiet -rfbport 5900 \
  >/tmp/x11vnc.log 2>&1 &
websockify --web /usr/share/novnc 6080 localhost:5900 \
  >/tmp/websockify.log 2>&1 &

# Rogent mode: exactly one zenoh router, owned by this session supervisor.
# gui-start runs once per container start, so single-instance is true by
# construction -- no pgrep dance. Supervised here rather than started by any
# sim launch so the router (like the display and VNC above) outlives every
# individual sim or agent process; rogent and the sim nodes all dial
# tcp/localhost:7447. launch-sim.sh gates on that port actually listening.
# DROID_ROGENT is set by container/docker-compose.rogent.yml only.
if [ "${DROID_ROGENT:-}" = "1" ]; then
  # The ROS setup scripts read variables they do not set; relax -u around
  # sourcing only (same rationale as launch-sim.sh).
  set +u
  # shellcheck disable=SC1091
  . /opt/ros/jazzy/setup.sh
  set -u
  # Not on PATH: the setup script doesn't expose package-private executables;
  # this is the same binary `ros2 run rmw_zenoh_cpp rmw_zenohd` resolves to.
  /opt/ros/jazzy/lib/rmw_zenoh_cpp/rmw_zenohd >/tmp/rmw_zenohd.log 2>&1 &
fi

exec "$@"
