# R2D3 Apps

## 1. Project Introduction

`ros2_r2d3_apps` is a unified ROS 2 bringup, configuration, and testing package for the R2D3 dual-arm mobile robot.

The implemented functionality includes:

1. Unified simulation environment launch integrating Gazebo, RViz2, MoveIt2, and Navigation2 (Nav2).
2. Dynamic hardware support for four robot configurations:
   - 65b arm with Dummy grippers
   - 65b arm with 4C2 2-DOF grippers
   - 75b arm with Dummy grippers
   - 75b arm with 4C2 2-DOF grippers
3. Automated C++ test nodes for validating AGV chassis navigation and dual-arm trajectory execution.

---

## 2. File Structure

```text
.
├── r2d3_bringup                      # Unified launch and configuration package
│   ├── CMakeLists.txt
│   ├── config                        # Configuration parameter files
│   ├── launch                        # Launch scripts
│   │   ├── bringup_sim.launch.py     # Main simulation bringup
│   │   └── moveit_sim.launch.py      # MoveIt2 integration
│   ├── package.xml
│   └── rviz                          # RViz2 configurations
│       └── nav2_moveit_view.rviz
│
└── r2d3_test_nodes                   # Automated C++ testing package
    ├── CMakeLists.txt
    ├── include
    │   └── r2d3_test_nodes
    │       ├── test_agv_motion.hpp
    │       └── test_arm_motion.hpp
    ├── package.xml
    └── src
        ├── test_agv_motion.cpp
        └── test_arm_motion.cpp
```

---

## 3. Build

```bash
cd ~/R2D3_updated/

colcon build --packages-select r2d3_bringup r2d3_test_nodes

source install/setup.bash
```

---

## 4. Unified Simulation Bringup

The main launch script automatically:

- Starts a minimal Gazebo simulation (`nav_empty.sdf`)
- Spawns the R2D3 robot
- Starts ROS 2 controllers
- Launches MoveIt2 for dual-arm planning
- Launches Navigation2 (Nav2) for mobile base navigation
- Opens a combined RViz2 visualization

### Available Robot Configurations

#### 1. 65b arm with Dummy grippers

```bash
ros2 launch r2d3_bringup bringup_sim.launch.py robot_model:=65b gripper_type:=dummy
```

#### 2. 65b arm with 4C2 grippers

```bash
ros2 launch r2d3_bringup bringup_sim.launch.py robot_model:=65b gripper_type:=4c2
```

#### 3. 75b arm with Dummy grippers

```bash
ros2 launch r2d3_bringup bringup_sim.launch.py robot_model:=75b gripper_type:=dummy
```

#### 4. 75b arm with 4C2 grippers

```bash
ros2 launch r2d3_bringup bringup_sim.launch.py robot_model:=75b gripper_type:=4c2
```

---

## 5. Automated Test Nodes

After the simulation has fully started, open a **new terminal** and source the workspace:

```bash
source ~/R2D3_updated/install/setup.bash
```

### AGV Motion Test

This test publishes `TwistStamped` commands to the differential drive controller.

Motion sequence:

1. Move forward (0.2 m/s)
2. Stop
3. Rotate clockwise (-0.5 rad/s)
4. Stop
5. Move backward
6. Stop

Run:

```bash
ros2 run r2d3_test_nodes test_agv_motion
```

---

### Dual-Arm Motion Test

This test connects to the following action servers:

- `left_arm_controller`
- `right_arm_controller`

Motion sequence:

1. Left arm moves to wave pose
2. Left arm returns home
3. Right arm moves to wave pose
4. Right arm returns home

Run:

```bash
ros2 run r2d3_test_nodes test_arm_motion
```

---

## Supported Hardware Configurations

| Robot Model | Gripper | Launch Arguments |
|-------------|----------|------------------|
| 65b | Dummy | `robot_model:=65b gripper_type:=dummy` |
| 65b | 4C2 | `robot_model:=65b gripper_type:=4c2` |
| 75b | Dummy | `robot_model:=75b gripper_type:=dummy` |
| 75b | 4C2 | `robot_model:=75b gripper_type:=4c2` |

---

## Package Summary

### `r2d3_bringup`

Provides:

- Unified simulation launch
- Gazebo integration
- Navigation2 bringup
- MoveIt2 integration
- RViz2 configuration
- Dynamic robot model selection
- Dynamic gripper selection

### `r2d3_test_nodes`

Provides automated C++ validation nodes for:

- AGV chassis motion
- Dual-arm trajectory execution