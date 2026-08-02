from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_moveit_rviz_launch


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("r2d3_description", package_name="dual_rm_65b_moveit_config").to_moveit_configs()
    return generate_moveit_rviz_launch(moveit_config)
