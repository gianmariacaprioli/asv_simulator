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

    # -------------------------------------------------------------------------
    # ROBOT CONFIGURATION
    #
    # Questa e' la sola lista da estendere quando aggiungerai nuovi UAV / USV.
    # Per ora manteniamo i frame gia' usati dalla simulazione corrente:
    #   vessel_v2 -> odom
    #   x500      -> x500/odom
    # -------------------------------------------------------------------------
    robots = [
        {
            'name': 'usv_0',
            'odom_topic': '/model/vessel_v2/odometry',
            'odom_frame': 'odom',
        },
        {
            'name': 'uav_0',
            'odom_topic': '/model/x500/odometry',
            'odom_frame': 'x500/odom',
        },
    ]

    # -------------------------------------------------------------------------
    # GENERIC ODOMETRY -> TF BROADCASTERS
    #
    # Viene creata una istanza per ogni robot. Il nodo generico legge
    # frame_id e child_frame_id direttamente dal messaggio nav_msgs/Odometry.
    # Questo sostituisce gazebo_odom.py e gazebo_odom_x500.py.
    # -------------------------------------------------------------------------
    odometry_tf_nodes = []

    for robot in robots:
        odometry_tf_nodes.append(
            Node(
                package='asv_simulator',
                executable='odometry_tf_broadcaster.py',
                name=f'{robot["name"]}_odometry_tf',
                output='screen',
                parameters=[
                    {
                        'odom_topic': robot['odom_topic'],
                        'use_sim_time': True,
                    }
                ],
            )
        )

    # -------------------------------------------------------------------------
    # GLOBAL SIMULATION FRAME
    #
    # Durante la fase Gazebo senza SLAM crea un'origine comune:
    #
    #                         ocean_world
    #                        /           \
    #                     odom         x500/odom
    #
    # Gli odom correnti sono allineati al world Gazebo, quindi queste
    # trasformazioni sono identita'.
    #
    # IMPORTANTE PER SLAM:
    # quando SLAM/localization pubblichera' map -> <robot>/odom, questo nodo
    # dovra' essere disabilitato per evitare due parent dello stesso odom.
    # -------------------------------------------------------------------------
    global_frame_manager = Node(
        package='asv_simulator',
        executable='global_frame_manager.py',
        name='global_frame_manager',
        output='screen',
        parameters=[
            {
                'global_frame': 'ocean_world',
                'odom_frames': [
                    robot['odom_frame']
                    for robot in robots
                ],
                'use_sim_time': True,
            }
        ],
    )

    with open(urdf_path, "r") as f:
        robot_description = f.read()
    
    set_model_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(pkg_asv_sim, 'models')
    )

    x500_urdf_path = os.path.join(
        pkg_asv_sim,
        "urdf",
        "x500.urdf"
    )

    with open(x500_urdf_path, "r") as f:
        x500_robot_description = f.read()
    
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

            '/vessel_v2/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',

            # UAV BRIDGE
            '/model/x500/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/x500/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/x500/enable@std_msgs/msg/Bool]gz.msgs.Boolean',
            '/world/ocean_world/model/x500/link/base_link/sensor/navsat_sensor/navsat@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',
        ],
        remappings=[
            # ('/model/vessel_v2/pose', '/tf'),
            # --- AGGIUNTO: Rimappa il topic sul default di ROS 2 ---
            ('/world/ocean_world/model/vessel_v2/joint_state', '/joint_states'),    
            ('/world/ocean_world/model/x500/link/base_link/sensor/navsat_sensor/navsat','/x500/gps/fix'),
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
    # tf_map_to_ocean = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     name='tf_map_to_ocean',
    #     arguments=['300.00', '600.00', '0.0', '-1.309', '0', '0.0', 'map', 'ocean_world']
    # )

    # -------------------------------------------------------------------------
    # VECCHIE TF GLOBALI STATICHE - SOSTITUITE DA global_frame_manager.py
    #
    # NON lanciarle insieme al global_frame_manager, altrimenti avremmo piu'
    # publisher per le stesse trasformazioni.
    # -------------------------------------------------------------------------

    # tf_ocean_to_odom = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     name='tf_ocean_to_odom',
    #     arguments=[
    #         '0', '0', '0',
    #         '0', '0', '0',
    #         'ocean_world',
    #         'odom'
    #     ],
    # )

    # tf_ocean_to_x500_odom = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     name='tf_ocean_to_x500_odom',
    #     arguments=[
    #         '0', '0', '0',
    #         '0', '0', '0',
    #         'ocean_world',
    #         'x500/odom'
    #     ],
    # )

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

    x500_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace="x500",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": x500_robot_description,
                "use_sim_time": True,
            }
        ],
    )

    # 5. Odometria custom
    #
    # Questi due nodi sono stati sostituiti dal broadcaster generico
    # odometry_tf_broadcaster.py creato automaticamente per ogni robot
    # dalla lista "robots" all'inizio del file.
    #
    # NON vanno lanciati insieme ai nuovi nodi, altrimenti avremmo piu'
    # publisher per:
    #   odom -> base_link
    #   x500/odom -> x500/base_link

    # odom_tf = Node(
    #     package='asv_simulator',
    #     executable='gazebo_odom.py',
    #     output='screen'
    # )

    # x500_odom_tf = Node(
    #     package='asv_simulator',
    #     executable='gazebo_odom_x500.py',
    #     output='screen',
    # )

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

    # -------------------------------------------------------------------------
    # VECCHIA TF STATICA X500 - NON USARE
    #
    # x500/base_link si muove rispetto a x500/odom, quindi questa relazione
    # NON puo' essere statica. Ora viene pubblicata dinamicamente da
    # odometry_tf_broadcaster.py usando /model/x500/odometry.
    # -------------------------------------------------------------------------

    # x500_odom_tf = Node(
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     name='x500_odom_tf',
    #     arguments=['0', '0', '0', '0', '0', '0', 'x500/odom', 'x500/base_link']
    # )
   
    return LaunchDescription([
        set_model_path,
        gz_sim,
        bridge,

        # Map server / SLAM restano disabilitati per ora.
        # map_server,
        # lifecycle_manager,

        # Un solo nodo gestisce il riferimento globale comune della simulazione.
        global_frame_manager,

        # Un broadcaster TF dinamico per ogni robot presente nella lista "robots".
        *odometry_tf_nodes,

        robot_state_publisher,
        x500_robot_state_publisher,

        tf_lidar,            # Attivato
        tf_camera,           # Attivato
        tf_camera_optical,   # Attivato
        tf_sonar,            # Attivato
        tf_gps,
        pointcloud_to_laserscan_node,
        rviz_node,
    ])
