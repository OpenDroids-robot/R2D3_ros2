"""
Full-stack MuJoCo bringup: sim + Nav2 (SLAM/localization) + optional MoveIt2.
Self-contained MuJoCo counterpart of dual_rm_navigation/bringup_sim.launch.py
and r2d3_bringup/bringup_sim.launch.py; reuses their sub-launches and configs.

Startup ordering: Nav2/SLAM/MoveIt are NOT started on a blind timer. A
readiness-gate node (scripts/wait_for_sim_ready.py) blocks until the MuJoCo sim
is genuinely ready (/scan flowing + odom->base_footprint + base_footprint->laser_link
TF available), then the nav stack fires off that node's exit. This is what makes
the map come up reliably regardless of how long the sim takes to start (cold
MJCF cache, GUI/MoveIt/RViz CPU contention, slower machines).
"""

import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

from moveit_configs_utils import MoveItConfigsBuilder


def launch_setup(context, *args, **kwargs):
    pkg_mujoco = get_package_share_directory("r2d3_mujoco")
    pkg_nav = get_package_share_directory("dual_rm_navigation")
    pkg_bringup = get_package_share_directory("r2d3_bringup")

    robot_model = LaunchConfiguration("robot_model")
    gripper_type = LaunchConfiguration("gripper_type")
    world = LaunchConfiguration("world")
    mode = LaunchConfiguration("mode")
    slam_type = LaunchConfiguration("slam_type")
    map_yaml = LaunchConfiguration("map")
    use_rviz = LaunchConfiguration("use_rviz")
    use_moveit = LaunchConfiguration("use_moveit")
    headless = LaunchConfiguration("headless")
    ready_timeout = LaunchConfiguration("ready_timeout")

    robot_model_str = robot_model.perform(context)
    gripper_type_str = gripper_type.perform(context)

    # ── INJECT ENVIRONMENT VARIABLE ───────────────────────────────
    os.environ["GRIPPER_TYPE"] = gripper_type_str

    nav2_params = os.path.join(pkg_nav, "config", "nav2_params.yaml")
    slam_params = os.path.join(pkg_nav, "config", "slam_toolbox_params.yaml")
    rtabmap_params = os.path.join(pkg_nav, "config", "rtabmap_params.yaml")

    # MoveIt parameters for the combined RViz view
    moveit_config = (
        MoveItConfigsBuilder(
            f"dual_rm_{robot_model_str}_description",
            package_name=f"dual_rm_{robot_model_str}_moveit_config",
        )
        .robot_description(
            mappings={
                "arm_model": robot_model_str,
                "gripper_type": gripper_type_str,
            }
        )
        .robot_description_semantic(
            file_path=f"config/dual_rm_{robot_model_str}_description.srdf.xacro",
            mappings={
                "arm_model": robot_model_str,
                "gripper_type": gripper_type_str,
            }
        )
        .to_moveit_configs()
    )

    # 1. MuJoCo simulation (robot + controllers + sensors)
    sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_mujoco, "launch", "mujoco_sim.launch.py")),
        launch_arguments={
            "robot_model": robot_model,
            "gripper_type": gripper_type,
            "world": world,
            "headless": headless,
        }.items(),
    )

    # 2. RViz (combined Nav2 + MoveIt view from r2d3_bringup)
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(pkg_bringup, "rviz", "nav2_moveit_view.rviz")],
        parameters=[
            {"use_sim_time": True},
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
        ],
        output="screen",
        condition=IfCondition(use_rviz),
    )

    # 3. Readiness gate: blocks until the sim can actually feed Nav2/SLAM
    sim_ready_gate = Node(
        package="r2d3_mujoco",
        executable="wait_for_sim_ready.py",
        name="wait_for_sim_ready",
        output="screen",
        arguments=["--timeout", ready_timeout],
    )

    # --- Actions deferred until the sim reports ready ---------------------

    # 4a. SLAM Toolbox (mapping, 2D lidar)
    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_nav, "launch", "slam.launch.py")),
        launch_arguments={"use_sim_time": "true", "params_file": slam_params}.items(),
        condition=IfCondition(PythonExpression(
            ["'", mode, "' == 'slam' and '", slam_type, "' == 'slam_toolbox'"])),
    )

    # 4b. RTAB-Map SLAM (RGB-D + lidar)
    rtabmap_slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_nav, "launch", "rtabmap.launch.py")),
        launch_arguments={
            "use_sim_time": "true", "params_file": rtabmap_params,
            "localization": "false"}.items(),
        condition=IfCondition(PythonExpression(
            ["'", mode, "' == 'slam' and '", slam_type, "' == 'rtabmap'"])),
    )

    # 4c. RTAB-Map localization
    rtabmap_loc_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_nav, "launch", "rtabmap.launch.py")),
        launch_arguments={
            "use_sim_time": "true", "params_file": rtabmap_params,
            "localization": "true"}.items(),
        condition=IfCondition(PythonExpression(
            ["'", mode, "' == 'localization' and '", slam_type, "' == 'rtabmap'"])),
    )

    # 4d. RTAB-Map depth-only SLAM
    rtabmap_depth_slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav, "launch", "rtabmap_depth_only.launch.py")),
        launch_arguments={"use_sim_time": "true", "localization": "false"}.items(),
        condition=IfCondition(PythonExpression(
            ["'", mode, "' == 'slam' and '", slam_type, "' == 'rtabmap_depth_only'"])),
    )

    # 4e. RTAB-Map depth-only localization
    rtabmap_depth_loc_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav, "launch", "rtabmap_depth_only.launch.py")),
        launch_arguments={"use_sim_time": "true", "localization": "true"}.items(),
        condition=IfCondition(PythonExpression(
            ["'", mode, "' == 'localization' and '", slam_type, "' == 'rtabmap_depth_only'"])),
    )

    # 4f. AMCL + map_server localization (slam_toolbox backend)
    localization_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav, "launch", "localization.launch.py")),
        launch_arguments={
            "use_sim_time": "true", "params_file": nav2_params,
            "map": map_yaml}.items(),
        condition=IfCondition(PythonExpression(
            ["'", mode, "' == 'localization' and '", slam_type, "' == 'slam_toolbox'"])),
    )

    # 4g. Nav2 stack
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav, "launch", "navigation.launch.py")),
        launch_arguments={
            "use_sim_time": "true", "params_file": nav2_params}.items(),
    )

    # 4h. MoveIt2 move_group (reused from r2d3_bringup)
    moveit_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, "launch", "moveit_sim.launch.py")),
        launch_arguments={
            "robot_model": robot_model,
            "gripper_type": gripper_type,
        }.items(),
        condition=IfCondition(use_moveit),
    )

    # Fire the whole nav/slam/moveit stack once the sim reports ready.
    start_stack_when_ready = RegisterEventHandler(
        OnProcessExit(
            target_action=sim_ready_gate,
            on_exit=[
                slam_toolbox_launch,
                rtabmap_slam_launch,
                rtabmap_loc_launch,
                rtabmap_depth_slam_launch,
                rtabmap_depth_loc_launch,
                localization_launch,
                nav2_launch,
                moveit_launch,
            ],
        )
    )

    return [
        sim_launch,
        rviz_node,
        sim_ready_gate,
        start_stack_when_ready,
    ]


def generate_launch_description():
    pkg_mujoco = get_package_share_directory("r2d3_mujoco")
    return LaunchDescription([
        DeclareLaunchArgument("robot_model", default_value="65b", description="Robot model variant: 65b or 75b"),
        DeclareLaunchArgument("gripper_type", default_value="dummy", description="Gripper type: dummy or 4c2"),
        DeclareLaunchArgument("world", default_value=os.path.join(pkg_mujoco, "worlds", "nav_empty.xml"), description="MuJoCo scene XML (full path)"),
        DeclareLaunchArgument("mode", default_value="slam", description="'slam' for mapping, 'localization' for existing map"),
        DeclareLaunchArgument("slam_type", default_value="slam_toolbox", description="SLAM backend: 'slam_toolbox', 'rtabmap', or 'rtabmap_depth_only'"),
        DeclareLaunchArgument("map", default_value="", description="Path to map YAML (localization + slam_toolbox)"),
        DeclareLaunchArgument("use_rviz", default_value="true", description="Launch RViz2"),
        DeclareLaunchArgument("use_moveit", default_value="true", description="Launch MoveIt2 move_group"),
        DeclareLaunchArgument("headless", default_value="false", description="Run MuJoCo without the Simulate window"),
        DeclareLaunchArgument("ready_timeout", default_value="90.0", description="Fallback: start Nav2/SLAM after this many seconds"),
        OpaqueFunction(function=launch_setup),
    ])