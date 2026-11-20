"""Spawn vessel_v2 in an already running Gazebo ocean world."""

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
            '/model/vessel_v2/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/world/ocean_world/model/vessel_v2/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/model/vessel_v2/joint/left_engine_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
            '/model/vessel_v2/joint/right_engine_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
            '/vessel_v2/camera@sensor_msgs/msg/Image[gz.msgs.Image',
            '/vessel_v2/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/vessel_v2/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/vessel_v2/sonar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/vessel_v2/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',
        ],
        remappings=[
            ('/world/ocean_world/model/vessel_v2/joint_state', '/joint_states'),
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
    ])
