import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node, LifecycleNode
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_asv_sim = get_package_share_directory('asv_simulator')
    
    world_file = os.path.join(pkg_asv_sim, 'worlds', 'ocean_world.sdf')
    # urdf_path = os.path.join(pkg_asv_sim, 'urdf', 'vessel_v2.urdf')
    rviz_config = os.path.join(pkg_asv_sim, 'configs', 'vessel_viz.rviz')

    map_yaml_file = os.path.join(pkg_asv_sim, 'map', 'map.yaml')

    # with open(urdf_path, 'r') as infp:
    #     robot_description = infp.read()
    
    set_model_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(pkg_asv_sim, 'models')
    )
    
    # Nodo 1: Avvia Gazebo Harmonic
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r -v 4 {world_file}'}.items(),
    )
    
    # Nodo 2: Il Ponte di Comunicazione aggiornato con le TF
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            
            # IL TRUCCO PER LE TF DINAMICHE: Convertiamo le pose di Gazebo in TF per RViz
            '/model/vessel_v2/pose@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            
            '/model/vessel_v2/joint/left_engine_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
            '/model/vessel_v2/joint/right_engine_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',

            '/vessel_v2/camera@sensor_msgs/msg/Image[gz.msgs.Image',
            '/vessel_v2/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',

            # '/vessel_v2/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/vessel_v2/lidar@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/vessel_v2/sonar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',

            '/vessel_v2/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat'
        ],
        # Mappiamo il topic di Gazebo sul topic standard /tf di ROS 2
        remappings=[
            ('/model/vessel_v2/pose', '/tf')
        ],
        output='screen'
    )

    # Nodo 3: TF Statica per i Sensori di Prua
    # Argomenti: x y z yaw pitch roll frame_padre frame_figlio
    # Ricordi? Li avevamo messi a x=6.0, z=1.8 nell'SDF

    # robot_state_publisher = Node(
    #     package='robot_state_publisher',
    #     executable='robot_state_publisher',
    #     name='robot_state_publisher',
    #     output='screen',
    #     parameters=[{'robot_description': robot_description}],
    # )

        # 3. Map Server (Lifecycle Node)
    map_server = LifecycleNode(
        package='nav2_map_server',
        executable='map_server',
        namespace ='',
        name='map_server',
        output='screen',
        parameters=[
            {'yaml_filename': map_yaml_file},
            {'frame_id': 'map'},
            {'topic_name': 'map'},
            {'use_sim_time': True}
        ],
    )

    # 4. Lifecycle Manager (Attiva automaticamente il map_server)
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'autostart': True},
            {'node_names': ['map_server']}
        ]
    )

        # TF: map -> ocean_world
    # Questa allinea l'origine della mappa (0,0) con l'origine del mondo Gazebo (0,0)
    # Invertiamo l'offset dell'origine della mappa: [-25.65, -25.65, -0.25] -> [25.65, 25.65, 0.25]
    tf_map_to_ocean = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_map_to_ocean',
        arguments=['300.00', '600.00', '0.0', '-1.309', '0', '0.0', 'map', 'ocean_world']
    )

    tf_camera = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_camera',
        arguments=['6.0', '0.0', '2.0', '0.0', '0.0', '0.0', 'vessel_v2', 'vessel_v2/sensors_link/camera']
    )

    tf_sensors = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_sensors',
        arguments=['6.0', '0.0', '1.8', '0.0', '0.0', '0.0', 'vessel_v2', 'vessel_v2/sensors_link/gpu_lidar']
    )

    # Nodo 4: TF Statica per il Sonar (inclinato in basso)
    tf_sonar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_sonar',
        arguments=['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', 'vessel_v2/sonar_link', 'vessel_v2/sonar_link/sonar']
    )

    # Nodo 5: TF Statica per il GPS
    tf_gps = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_gps',
        arguments=['-3.0', '0.0', '2.5', '0.0', '0.0', '0.0', 'vessel_v2', 'vessel_v2/gps_link/gps_sensor']
    )

    # Nodo RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        output='screen'
    )
    
    return LaunchDescription([
        set_model_path,
        gz_sim,
        bridge,
        # map_server,
        # lifecycle_manager,
        # tf_map_to_ocean,
        # robot_state_publisher,
        tf_camera,
        tf_sensors,
        tf_sonar,
        tf_gps,
        rviz_node,
    ])