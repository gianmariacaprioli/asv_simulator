"""Spawn vessel_v2 in an already running Gazebo ocean world."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('asv_simulator')
    joint_state = ['/world/', LaunchConfiguration('world'), '/model/vessel_v2/joint_state']
    model_file = os.path.join(
        package_share,
        'models',
        'vessel_v2',
        'vessel_v2.sdf',
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_vessel_v2',
        output='screen',
        arguments=[
            '-world', LaunchConfiguration('world'),
            '-file', model_file,
            '-name', 'vessel_v2',
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
        name='vessel_v2_bridge',
        output='screen',
        arguments=[
            '/vessel_v2/command/motor_speed@actuator_msgs/msg/Actuators]gz.msgs.Actuators',
            '/model/vessel_v2/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            [*joint_state, '@sensor_msgs/msg/JointState[gz.msgs.Model'],
            '/vessel_v2/camera@sensor_msgs/msg/Image[gz.msgs.Image',
            '/vessel_v2/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/vessel_v2/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/vessel_v2/sonar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/vessel_v2/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',
        ],
        remappings=[
            (joint_state, '/joint_states'),
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='ocean_world'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.0'),
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
                    'model': 'vessel_v2',
                    'world': LaunchConfiguration('world'),
                }.items(),
            ),
        ]),
    ])
