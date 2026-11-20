"""Spawn nautilus_vessel in an already running Gazebo ocean world."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    model_file = os.path.join(
        get_package_share_directory('asv_simulator'),
        'models',
        'nautilus_vessel',
        'model.sdf',
    )

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
            '/model/nautilus_vessel/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='ocean_world'),
        DeclareLaunchArgument('x', default_value='-10.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.035'),
        DeclareLaunchArgument('roll', default_value='0.0'),
        DeclareLaunchArgument('pitch', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        spawn,
        bridge,
    ])
