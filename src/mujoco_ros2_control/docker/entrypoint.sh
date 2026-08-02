#!/bin/bash

# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"

if [ -f "${ROS_WS}/install/setup.bash" ]; then
    echo "Sourcing ${ROS_WS}/install/setup.bash"
    # shellcheck disable=SC1091
    source "${ROS_WS}/install/setup.bash"
else
    echo "The ${ROS_WS} workspace is not yet built."
    echo "To build:"
    echo "  cd ${ROS_WS}"
    echo "  colcon build"
fi

# Execute the command passed into this entrypoint
exec "$@"
