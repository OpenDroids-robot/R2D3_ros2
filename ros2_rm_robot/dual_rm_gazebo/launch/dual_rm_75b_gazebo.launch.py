import os
import xacro
from launch import LaunchDescription, LaunchContext
from launch.actions import ExecuteProcess, RegisterEventHandler, DeclareLaunchArgument, OpaqueFunction
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration

# Recursive function to strip XML comments from the DOM
def strip_comments(node):
    for child in list(node.childNodes):
        if child.nodeType == child.COMMENT_NODE:
            node.removeChild(child)
        else:
            strip_comments(child)

def launch_setup(context: LaunchContext, *args, **kwargs):
    package_name = 'dual_rm_gazebo'
    robot_name_in_model = 'dual_rm_75b_description'
    pkg_share = FindPackageShare(package=package_name).find(package_name) 
    urdf_model_path = os.path.join(pkg_share, 'config/dual_rm_75b_gazebo.urdf.xacro')

    gripper_type_str = LaunchConfiguration('gripper_type').perform(context)

    doc = xacro.process_file(urdf_model_path, mappings={'gripper_type': gripper_type_str})
    
    # Strip comments so the Gazebo ROS 2 Control CLI parser doesn't throw error
    strip_comments(doc)
    
    robot_description_xml = doc.toxml()
    
    # Strip newlines to prevent gazebo_ros2_control YAML parser crash
    robot_description_xml = robot_description_xml.replace('\n', '').replace('\r', '')
    
    params = {'robot_description': robot_description_xml}

    gazebo = ExecuteProcess(
        cmd=['gazebo', '--verbose', '-s', 'libgazebo_ros_init.so', '-s', 'libgazebo_ros_factory.so'],
        output='screen')

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'use_sim_time': True}, params, {"publish_frequency": 15.0}],
        output='screen'
    )

    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', f'{robot_name_in_model}',
                                   '-x','0.0', '-y','0.0', '-z','0.25'], 
                        output='screen')

    load_joint_state_controller = Node(package='controller_manager', executable='spawner', arguments=['joint_state_broadcaster'])
    load_left_arm_controller = Node(package='controller_manager', executable='spawner', arguments=['left_arm_controller'])
    load_right_arm_controller = Node(package='controller_manager', executable='spawner', arguments=['right_arm_controller'])
    load_platform_controller = Node(package='controller_manager', executable='spawner', arguments=['platform_controller'])

    nodes = [gazebo, node_robot_state_publisher, spawn_entity]

    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=spawn_entity, on_exit=[load_joint_state_controller])))
    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_left_arm_controller])))
    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_right_arm_controller])))
    nodes.append(RegisterEventHandler(event_handler=OnProcessExit(target_action=load_joint_state_controller, on_exit=[load_platform_controller])))

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