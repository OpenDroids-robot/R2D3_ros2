import os
import xacro
from launch import LaunchDescription, LaunchContext
from launch.actions import RegisterEventHandler, DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription, SetEnvironmentVariable
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

# Recursive function to strip XML comments from the DOM
def strip_comments(node):
    for child in list(node.childNodes):
        if child.nodeType == child.COMMENT_NODE:
            node.removeChild(child)
        else:
            strip_comments(child)

def launch_setup(context: LaunchContext, *args, **kwargs):
    package_name = 'dual_rm_gazebo'
    robot_name_in_model = 'dual_rm_65b_description'
    pkg_share = FindPackageShare(package=package_name).find(package_name) 
    pkg_description = get_package_share_directory('dual_rm_description')
    
    urdf_model_path = os.path.join(pkg_share, 'config/dual_rm_65b_gz_sim.urdf.xacro')

    gripper_type_str = LaunchConfiguration('gripper_type').perform(context)

    # Process Xacro dynamically and pass the harmonic gazebo_version
    doc = xacro.process_file(urdf_model_path, mappings={'gripper_type': gripper_type_str, 'gazebo_version': 'harmonic'})
    
    # Strip comments so the Gazebo ROS 2 Control CLI parser doesn't choke on em-dashes
    strip_comments(doc)
    
    robot_description_xml = doc.toxml()
    
    # Strip newlines to prevent gazebo_ros2_control YAML parser crash
    robot_description_xml = robot_description_xml.replace('\n', '').replace('\r', '')
    
    params = {'robot_description': robot_description_xml}

    # Gazebo Harmonic specific setups
    gz_resource_path = SetEnvironmentVariable(name='GZ_SIM_RESOURCE_PATH', value=os.path.join(pkg_description, 'meshes'))

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': '-r -v 4 empty.sdf'}.items(),
    )

    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge', arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'], output='screen')

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'use_sim_time': True}, params, {"publish_frequency": 15.0}],
        output='screen'
    )

    spawn_entity = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', robot_name_in_model, '-x', '0.0', '-y', '0.0', '-z', '0.25', '-allow_renaming', 'true'],
        output='screen'
    )

    # Controllers
    load_joint_state_controller = Node(package='controller_manager', executable='spawner', arguments=['joint_state_broadcaster'])
    load_left_arm_controller = Node(package='controller_manager', executable='spawner', arguments=['left_arm_controller'])
    load_right_arm_controller = Node(package='controller_manager', executable='spawner', arguments=['right_arm_controller'])
    load_platform_controller = Node(package='controller_manager', executable='spawner', arguments=['platform_controller'])
    load_agv_controller = Node(package='controller_manager', executable='spawner', arguments=['agv_controller'])

    nodes = [gz_resource_path, gz_sim, bridge, node_robot_state_publisher, spawn_entity]

    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[load_joint_state_controller])))
    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_left_arm_controller])))
    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_right_arm_controller])))
    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_platform_controller])))
    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_agv_controller])))

    # Conditionally sequence grippers
    if gripper_type_str == '4c2':
        load_left_gripper_controller = Node(package='controller_manager', executable='spawner', arguments=['left_gripper_controller'])
        load_right_gripper_controller = Node(package='controller_manager', executable='spawner', arguments=['right_gripper_controller'])
        nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_left_gripper_controller])))
        nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_right_gripper_controller])))

    return nodes

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('gripper_type', default_value='dummy', choices=['dummy', '4c2'], description='Gripper variant'),
        OpaqueFunction(function=launch_setup)
    ])