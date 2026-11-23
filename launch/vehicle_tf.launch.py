"""Start a vehicle's TF publishers once Gazebo produces its odometry."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def vessel_sensor_nodes():
    tf_lidar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_lidar',
        arguments=['0.0', '0.0', '0.5', '0.0', '0.0', '0.0', 'lidar_link', 'vessel_v2/lidar_link/gpu_lidar']
    )

    tf_camera = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_camera',
        arguments=['0.0', '0.0', '0.2', '0.0', '0.0', '0.0', 'camera_link', 'vessel_v2/camera_link/camera']
    )

    tf_camera_optical = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_camera_optical',
        arguments=['0.0', '0.0', '0.0', '-1.5708', '0.0', '-1.5708', 'vessel_v2/camera_link/camera', 'vessel_v2/camera_link/camera_optical']
    )

    tf_sonar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_sonar',
        arguments=['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', 'sonar_link', 'vessel_v2/sonar_link/sonar']
    )

    tf_gps = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_gps',
        arguments=['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', 'gps_link', 'vessel_v2/gps_link/gps_sensor']
    )

    pointcloud_to_laserscan_node = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        remappings=[
            ('cloud_in', '/vessel_v2/lidar/points'),
            ('scan', '/vessel_v2/lidar_2d') # Il nuovo topic pulito per lo SLAM
        ],
        parameters=[{
            'target_frame': 'lidar_link',
            'transform_tolerance': 0.01,
            # Se il Lidar è a Z=1.8, l'acqua è a -1.8 rispetto a lui.
            # Tagliamo a -1.0 per filtrare via il mare in modo sicuro!
            'min_height': -0.2,  # Prendi solo 20 cm sotto il laser
            'max_height': 3.0,   # Prendi solo 20 cm sopra il laser
            'angle_increment': 0.0087266, # mezzo grado di risoluzione (alleggerisce il carico)
            'angle_min': -1.5708,  # -90 gradi
            'angle_max': 1.5708,   # +90 gradi
            'scan_time': 0.1,
            'range_min': 0.5,
            'range_max': 50.0,
            'use_inf': True,
        }],
        output='screen'
    )

    return [tf_lidar, tf_camera, tf_camera_optical, tf_sonar, tf_gps,
            pointcloud_to_laserscan_node]


def vehicle_nodes(context):
    world = LaunchConfiguration('world').perform(context)
    model = LaunchConfiguration('model').perform(context)
    odom_topic = f'/model/{model}/odometry'
    odom_frame = 'odom' if model == 'vessel_v2' else f'{model}/odom'

    publishers = [
        Node(
            package='asv_simulator',
            executable='odometry_tf_broadcaster.py',
            name=f'{model}_odometry_tf',
            parameters=[{'odom_topic': odom_topic, 'use_sim_time': True}],
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name=f'{model}_world_to_odom',
            arguments=['--frame-id', world, '--child-frame-id', odom_frame],
        ),
    ]

    if model != 'durius':
        urdf_path = os.path.join(
            get_package_share_directory('asv_simulator'), 'urdf', f'{model}.urdf',
        )
        with open(urdf_path) as urdf:
            robot_description = urdf.read()
        publishers.append(Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace='' if model == 'vessel_v2' else model,
            parameters=[{
                'robot_description': robot_description,
                'frame_prefix': 'nautilus_vessel/' if model == 'nautilus_vessel' else '',
                'use_sim_time': True,
            }],
        ))

    if model == 'vessel_v2':
        publishers.extend(vessel_sensor_nodes())

    # Gazebo create can exit successfully even when the request times out.
    # A message from the running model confirms it exists before publishing TF.
    wait_for_odometry = ExecuteProcess(
        cmd=['ros2', 'topic', 'echo', '--once', '--field', 'child_frame_id',
             odom_topic, 'nav_msgs/msg/Odometry'],
        name=f'wait_for_{model}_odometry',
    )

    def start_publishers(event, context):
        if event.returncode == 0 and not context.is_shutdown:
            return publishers
        return []

    return [
        RegisterEventHandler(OnProcessExit(
            target_action=wait_for_odometry, on_exit=start_publishers,
        )),
        wait_for_odometry,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('world'),
        DeclareLaunchArgument('model'),
        OpaqueFunction(function=vehicle_nodes),
    ])
