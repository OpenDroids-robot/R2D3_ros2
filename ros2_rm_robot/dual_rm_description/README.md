# Dual RM Description

## 1. Project Introduction

`dual_rm_description` is the core robot description package for the R2D3 dual-arm mobile robot. It contains the URDF (Unified Robot Description Format), Xacro macros, 3D visual and collision meshes, and RViz2 visualization configurations.

The implemented functionality includes:

1. Modular Xacro architecture separating the AGV mobile base, torso, arms, grippers, and sensors.
2. Dynamic hardware support with on-the-fly URDF generation for four robot configurations:
   - 65b arm with Dummy grippers
   - 65b arm with 4C2 2-DOF grippers
   - 75b arm with Dummy grippers
   - 75b arm with 4C2 2-DOF grippers
3. Standalone RViz2 visualization using `display.launch.py` and `joint_state_publisher_gui` for rapid kinematic debugging and joint testing without requiring a physics simulator.

---

## 2. File Structure

```text
.
├── dual_rm_description               # Core robot description package
│   ├── CMakeLists.txt
│   ├── config                        # Sensor and camera parameter files
│   │   └── wrist_cameras.yaml
│   ├── launch                        # Launch scripts
│   │   └── display.launch.py         # Standalone RViz2 visualization
│   ├── meshes                        # Visual and collision meshes
│   │   ├── arms_65b/
│   │   ├── arms_75b/
│   │   ├── common/
│   │   └── grippers/
│   │       └── 4c2/
│   ├── package.xml
│   ├── rviz                          # RViz2 configurations
│   │   └── view.rviz
│   └── urdf                          # Modular Xacro components
│       ├── agv/
│       ├── arms/
│       ├── body/
│       ├── grippers/
│       ├── legacy/
│       ├── materials/
│       ├── sensors/
│       ├── transmissions/
│       └── r2d3_description.urdf.xacro
```

---

## 3. Build

```bash
cd ~/R2D3

colcon build --packages-select dual_rm_description

source install/setup.bash
```

---

## 4. Visualization Bringup

The standalone RViz visualization script (`display.launch.py`) mirrors the launch arguments used by the simulation packages.

It automatically:

- Generates the robot URDF using Xacro with the selected `robot_model` and `gripper_type`
- Starts `robot_state_publisher`
- Launches `joint_state_publisher_gui` for interactive joint manipulation
- Opens RViz2 using the default `view.rviz` configuration

### Available Robot Configurations

#### 1. 65b arm with Dummy grippers

```bash
ros2 launch dual_rm_description display.launch.py robot_model:=65b gripper_type:=dummy
```

#### 2. 65b arm with 4C2 grippers

```bash
ros2 launch dual_rm_description display.launch.py robot_model:=65b gripper_type:=4c2
```

#### 3. 75b arm with Dummy grippers

```bash
ros2 launch dual_rm_description display.launch.py robot_model:=75b gripper_type:=dummy
```

#### 4. 75b arm with 4C2 grippers

```bash
ros2 launch dual_rm_description display.launch.py robot_model:=75b gripper_type:=4c2
```

---

## 5. Supported Hardware Configurations

| Robot Model | Gripper | Launch Arguments |
|-------------|----------|------------------|
| 65b | Dummy | `robot_model:=65b gripper_type:=dummy` |
| 65b | 4C2 | `robot_model:=65b gripper_type:=4c2` |
| 75b | Dummy | `robot_model:=75b gripper_type:=dummy` |
| 75b | 4C2 | `robot_model:=75b gripper_type:=4c2` |

---

## 6. Package Summary

### `dual_rm_description`

Provides:

- Core URDF and Xacro definitions for the R2D3 robot
- Modular robot description architecture
- High-quality visual and collision meshes (STL/DAE)
- Standalone RViz2 visualization and kinematic debugging tools
- Interactive joint control through `joint_state_publisher_gui`
- Support for RealMan 65b and 75b arm variants
- Support for both Dummy and 4C2 grippers
- Consistent `robot_model` and `gripper_type` launch arguments compatible with downstream packages such as `r2d3_mujoco`, `r2d3_bringup`, and `dual_rm_gazebo`