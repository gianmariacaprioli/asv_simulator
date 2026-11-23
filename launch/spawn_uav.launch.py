"""Spawn the x500 UAV in an already running Gazebo ocean world."""

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
        'x500',
        'model.sdf',
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_x500',
        output='screen',
        arguments=[
            '-world', LaunchConfiguration('world'),
            '-file', model_file,
            '-name', 'x500',
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
        name='x500_bridge',
        output='screen',
        arguments=[
            '/model/x500/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/x500/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/x500/enable@std_msgs/msg/Bool]gz.msgs.Boolean',
            '/world/ocean_world/model/x500/link/base_link/sensor/navsat_sensor/navsat@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',
        ],
        remappings=[
            (
                '/world/ocean_world/model/x500/link/base_link/sensor/navsat_sensor/navsat',
                '/x500/gps/fix',
            ),
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='ocean_world'),
        DeclareLaunchArgument('x', default_value='-2.5'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='2.0'),
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
                    'model': 'x500',
                    'world': LaunchConfiguration('world'),
                }.items(),
            ),
        ]),
    ])
