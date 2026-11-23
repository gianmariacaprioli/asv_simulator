"""Spawn nautilus_vessel in an already running Gazebo ocean world."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('asv_simulator')
    model_file = os.path.join(
        package_share,
        'models',
        'nautilus_vessel',
        'model.sdf',
    )
    odom_topic = '/model/nautilus_vessel/odometry'
    joint_state_topic = '/model/nautilus_vessel/joint_state'

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_nautilus_vessel',
        output='screen',
        arguments=[
            '-world', LaunchConfiguration('world'),
            '-file', model_file,
            '-name', 'nautilus_vessel',
            '-allow_renaming', 'false',
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-R', LaunchConfiguration('roll'),
            '-P', LaunchConfiguration('pitch'),
            '-Y', LaunchConfiguration('yaw'),
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='nautilus_bridge',
        output='screen',
        arguments=[
            f'{odom_topic}@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            f'{joint_state_topic}@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        remappings=[(joint_state_topic, '/nautilus_vessel/joint_states')],
    )

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='ocean_world'),
        DeclareLaunchArgument('x', default_value='-10.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.098'),
        DeclareLaunchArgument('roll', default_value='0.0'),
        DeclareLaunchArgument('pitch', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        spawn,
        bridge,
        GroupAction([
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(package_share, 'launch', 'vehicle_tf.launch.py')
                ),
                launch_arguments={
                    'model': 'nautilus_vessel',
                    'world': LaunchConfiguration('world'),
                }.items(),
            ),
        ]),
    ])
