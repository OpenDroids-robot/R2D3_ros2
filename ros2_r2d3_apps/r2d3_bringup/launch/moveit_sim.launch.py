"""
MoveIt2 move_group launch for simulation.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from moveit_configs_utils import MoveItConfigsBuilder


def launch_setup(context, *args, **kwargs):
    robot_model_str = LaunchConfiguration("robot_model").perform(context)
    
    # ── EXTRACT THE GRIPPER ARGUMENT ───────────────────────────────
    gripper_type_str = LaunchConfiguration("gripper_type").perform(context)

    # ── Load MoveIt configs for the selected arm variant ───────────
    moveit_config = (
        MoveItConfigsBuilder(
            f"dual_rm_{robot_model_str}_description",
            package_name=f"dual_rm_{robot_model_str}_moveit_config",
        )
        .robot_description(mappings={"arm_model": robot_model_str, "gripper_type": gripper_type_str})
        # FORCE MOVE_GROUP TO USE THE DYNAMIC SRDF.XACRO FILE
        .robot_description_semantic(
            file_path=f"config/dual_rm_{robot_model_str}_description.srdf.xacro",
            mappings={"arm_model": robot_model_str, "gripper_type": gripper_type_str}
        )
        .to_moveit_configs()
    )

    # ── Build the full parameter dict for move_group ───────────────
    moveit_params = moveit_config.to_dict()
    moveit_params["use_sim_time"] = True

    # ── move_group node ─────────────────────────────────────────────
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        name="move_group",
        output="screen",
        parameters=[moveit_params],
    )

    return [move_group_node]


def generate_launch_description():
    # ── Arguments ─────────────────────────────────────────────────
    declare_robot_model = DeclareLaunchArgument(
        "robot_model",
        default_value="65b",
        description="Robot model variant: 65b or 75b",
    )
    
    declare_gripper_type = DeclareLaunchArgument(
        "gripper_type",
        default_value="dummy_gripper",
        description="Choose gripper type: dummy_gripper or 4c2",
    )

    return LaunchDescription(
        [
            declare_robot_model,
            declare_gripper_type,
            OpaqueFunction(function=launch_setup),
        ]
    )