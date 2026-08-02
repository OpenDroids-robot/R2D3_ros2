# R2D3 MuJoCo Simulation

## 1. Project Introduction

`r2d3_mujoco` is a unified ROS 2 bringup and physics simulation package for the R2D3 dual-arm mobile robot using the MuJoCo physics engine.

The implemented functionality includes:

1. Unified simulation environment integrating MuJoCo, RViz2, MoveIt2, and Navigation2 (Nav2).
2. Dynamic hardware support with on-the-fly URDF-to-MJCF conversion for four robot configurations:
   - 65b arm with Dummy grippers
   - 65b arm with 4C2 2-DOF grippers
   - 75b arm with Dummy grippers
   - 75b arm with 4C2 2-DOF grippers
3. Synchronized stack bringup using a custom readiness gate to ensure controllers, sensors, and TFs are fully available before launching MoveIt2 and Nav2.

---

## 2. File Structure

```text
.
├── r2d3_mujoco                       # MuJoCo simulation package
│   ├── CMakeLists.txt
│   ├── config                        # Controller parameter files
│   │   ├── controllers_65b.yaml
│   │   └── controllers_75b.yaml
│   ├── launch                        # Launch scripts
│   │   ├── bringup_sim.launch.py     # Full-stack simulation bringup
│   │   └── mujoco_sim.launch.py      # Core MuJoCo physics launch
│   ├── package.xml
│   ├── scripts                       # Utility Python scripts
│   │   ├── ensure_mjcf.py            # URDF-to-MJCF conversion and caching
│   │   └── wait_for_sim_ready.py     # Simulation readiness gate
│   ├── urdf                          # MuJoCo-specific URDF components
│   │   ├── ros2_control/
│   │   ├── mujoco_inputs.urdf.xacro
│   │   └── r2d3_mujoco.urdf.xacro
│   └── worlds                        # MuJoCo scene files
│       └── nav_empty.xml
```

---

## 3. Build

```bash
cd ~/sim/

colcon build --packages-select r2d3_mujoco

source install/setup.bash
```

---

## 4. Unified Simulation Bringup

The main launch script automatically:

- Compiles the robot URDF and generates a cached MuJoCo MJCF model (`ensure_mjcf.py`)
- Starts the MuJoCo physics simulation using `mujoco_ros2_control`
- Spawns the R2D3 robot and loads the appropriate `ros2_control` interfaces
- Waits until `/scan` and odometry transforms become available (`wait_for_sim_ready.py`)
- Launches MoveIt2 for dual-arm motion planning
- Launches Navigation2 (Nav2) for mobile base navigation
- Opens a combined RViz2 visualization

### Available Robot Configurations

#### 1. 65b arm with Dummy grippers

```bash
ros2 launch r2d3_mujoco bringup_sim.launch.py robot_model:=65b gripper_type:=dummy
```

#### 2. 65b arm with 4C2 grippers

```bash
ros2 launch r2d3_mujoco bringup_sim.launch.py robot_model:=65b gripper_type:=4c2
```

#### 3. 75b arm with Dummy grippers

```bash
ros2 launch r2d3_mujoco bringup_sim.launch.py robot_model:=75b gripper_type:=dummy
```

#### 4. 75b arm with 4C2 grippers

```bash
ros2 launch r2d3_mujoco bringup_sim.launch.py robot_model:=75b gripper_type:=4c2
```

---

## 5. Automated Test Nodes

The MuJoCo simulation uses the same standardized testing nodes as the Gazebo simulation.

After the simulation has fully started and the readiness gate has completed, open a **new terminal** and source the workspace:

```bash
source ~/sim/install/setup.bash
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

1. Left arm moves to the wave pose
2. Left arm returns to the home pose
3. Right arm moves to the wave pose
4. Right arm returns to the home pose

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

### `r2d3_mujoco`

Provides:

- Unified MuJoCo simulation launch
- Automated URDF-to-MJCF conversion and caching
- Simulation readiness synchronization
- MuJoCo physics integration through `mujoco_ros2_control`
- Navigation2 and MoveIt2 integration
- Dedicated controller configurations for both 65b and 75b robot variants
- Dynamic robot model selection
- Dynamic gripper selection (Dummy or 4C2)
- Support for both navigation and manipulation in a single launch workflow