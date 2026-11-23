"""Spawn the dynamic DURIUS floater in an already running ocean world."""

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
        'durius',
        'model.sdf',
    )

    world = LaunchConfiguration('world')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_durius',
        output='screen',
        arguments=[
            '-world', world,
            '-file', model_file,
            # Keep this exact name: the world buoyancy filter uses it.
            '-name', 'durius',
            '-allow_renaming', 'false',
            '-x', x,
            '-y', y,
            '-z', z,
            '-R', roll,
            '-P', pitch,
            '-Y', yaw,
        ],
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='durius_bridge',
        output='screen',
        arguments=[
            '/model/durius/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value='ocean_world',
            description='Gazebo world in which DURIUS is spawned.',
        ),
        DeclareLaunchArgument('x', default_value='25.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument(
            'z',
            default_value='1.8',
            description='Initial height from DURIUS_parameters.txt.',
        ),
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
                    'model': 'durius',
                    'world': LaunchConfiguration('world'),
                }.items(),
            ),
        ]),
    ])
