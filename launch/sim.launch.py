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
    rviz_config = os.path.join(pkg_asv_sim, 'configs', 'vessel_viz.rviz')
    map_yaml_file = os.path.join(pkg_asv_sim, 'map', 'map.yaml')
    urdf_path = os.path.join(pkg_asv_sim, "urdf", "vessel_v2.urdf")

    with open(urdf_path, "r") as f:
        robot_description = f.read()
    
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
            
            # '/model/vessel_v2/pose@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/model/vessel_v2/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            
            # --- AGGIUNTO: Porta i joint_states da Gazebo a ROS ---
            '/world/ocean_world/model/vessel_v2/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
            
            '/model/vessel_v2/joint/left_engine_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',
            '/model/vessel_v2/joint/right_engine_joint/cmd_thrust@std_msgs/msg/Float64]gz.msgs.Double',

            '/vessel_v2/camera@sensor_msgs/msg/Image[gz.msgs.Image',
            '/vessel_v2/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',

            # '/vessel_v2/lidar@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/vessel_v2/lidar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/vessel_v2/sonar/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',

            '/vessel_v2/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat'
        ],
        remappings=[
            # ('/model/vessel_v2/pose', '/tf'),
            # --- AGGIUNTO: Rimappa il topic sul default di ROS 2 ---
            ('/world/ocean_world/model/vessel_v2/joint_state', '/joint_states')
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

    # 4. Robot State Publisher (Legge l'URDF)
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": True,
            }
        ],
    )

    # 5. Odometria custom
    odom_tf = Node(
        package='asv_simulator',
        executable='gazebo_odom.py',
        output='screen'
    )

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
    # Nodo RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}], # 
        output='screen'
    )
   
    return LaunchDescription([
        set_model_path,
        gz_sim,
        bridge,
        # lifecycle_manager,
        # tf_map_to_ocean,
        robot_state_publisher,
        odom_tf,
        tf_lidar,            # Attivato
        tf_camera,           # Attivato
        tf_camera_optical,   # Attivato
        tf_sonar,            # Attivato
        tf_gps,
        pointcloud_to_laserscan_node,
        rviz_node,
    ])