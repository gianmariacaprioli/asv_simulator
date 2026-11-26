import os
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    AndSubstitution,
    EqualsSubstitution,
    IfElseSubstitution,
    LaunchConfiguration,
    NotSubstitution,
    OrSubstitution,
    PathJoinSubstitution,
)
from launch_ros.actions import Node, LifecycleNode
from ament_index_python.packages import (
    get_package_prefix,
    get_package_share_directory,
)


def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_asv_sim = get_package_share_directory('asv_simulator')
    pkg_asv_sim_prefix = get_package_prefix('asv_simulator')
    
    world = LaunchConfiguration('world')
    is_viana = EqualsSubstitution(world, 'viana_port')
    world_file = PathJoinSubstitution([pkg_asv_sim, 'worlds', [world, '.sdf']])
    rviz_config = PathJoinSubstitution([
        pkg_asv_sim, 'configs', LaunchConfiguration('rviz_config')
    ])
    map_yaml_file = os.path.join(pkg_asv_sim, 'map', 'map.yaml')

    set_model_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(pkg_asv_sim, 'models')
    )

    set_plugin_path = AppendEnvironmentVariable(
        'GZ_SIM_SYSTEM_PLUGIN_PATH',
        os.path.join(pkg_asv_sim_prefix, 'lib')
    )

    # Start physics independently. Gazebo's combined mode can wait for GUI
    # startup before loading the world, which also blocks entity creation.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-s -r -v 4 "', world_file, '"'],
        }.items(),
    )
    gz_gui = ExecuteProcess(
        cmd=['gz', 'sim', '-g', '-v', '3',
             '--render-engine-gui', LaunchConfiguration('gui_render_engine')],
        condition=IfCondition(AndSubstitution(
            NotSubstitution(LaunchConfiguration('headless')), LaunchConfiguration('start_gz_gui')
        )),
        output='screen',
    )

    # -------------------------------------------------------------------------
    # OPTIONAL DYNAMIC MODEL SPAWN
    #
    # No dynamic vehicle is spawned by default. Each flag includes the same
    # dedicated spawn_*.launch.py that can also be invoked later by the user.
    # Every include has an isolated launch-configuration scope, so generic
    # child arguments such as x/y/z cannot leak from one model into another.
    # Fixed entity names preserve topics, controllers and buoyancy filters.
    # -------------------------------------------------------------------------
    def optional_spawn_launch(launch_file, enabled, **configurations):
        return GroupAction(
            scoped=True,
            forwarding=False,
            launch_configurations={'world': world, **configurations},
            condition=IfCondition(enabled),
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(pkg_asv_sim, 'launch', launch_file)
                    )
                )
            ],
        )

    spawn_vessel_v2 = optional_spawn_launch(
        'spawn_vessel_v2.launch.py',
        LaunchConfiguration('spawn_vessel_v2'),
        x=IfElseSubstitution(is_viana, '-25.0', '0.0'),
    )
    spawn_uav = optional_spawn_launch(
        'spawn_uav.launch.py',
        LaunchConfiguration('spawn_uav'),
        external_control=LaunchConfiguration('x500_external_control'),
        x=IfElseSubstitution(is_viana, '0.0', '-2.5'),
        y=IfElseSubstitution(is_viana, '-18.0', '0.0'),
    )
    spawn_uuv = optional_spawn_launch(
        'spawn_uuv.launch.py',
        LaunchConfiguration('spawn_uuv'),
        x=IfElseSubstitution(is_viana, '20.0', '5.0'),
    )
    spawn_durius = optional_spawn_launch(
        'spawn_durius.launch.py',
        OrSubstitution(is_viana, LaunchConfiguration('spawn_durius')),
        spawn_entity=NotSubstitution(is_viana),
    )
    windturbine_visualization = GroupAction(
        condition=IfCondition(EqualsSubstitution(world, 'ocean_world')),
        actions=[
            Node(
                package='ros_gz_bridge',
                executable='parameter_bridge',
                name='windturbine_odometry_bridge',
                arguments=[
                    '/model/floating_windturbine/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                ],
                output='screen',
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_asv_sim, 'launch', 'vehicle_tf.launch.py')
                ),
                launch_arguments={'world': world, 'model': 'floating_windturbine'}.items(),
            ),
        ],
    )
    spawn_nautilus = optional_spawn_launch(
        'spawn_nautilus.launch.py',
        LaunchConfiguration('spawn_nautilus'),
        x=IfElseSubstitution(is_viana, '-37.0', '-10.0'),
        y=IfElseSubstitution(is_viana, '-17.0', '0.0'),
    )
    
    # Global bridge. Entity-specific bridges live in their spawn launch files.
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='clock_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen'
    )

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

    # Nodo RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        condition=IfCondition(AndSubstitution(
            LaunchConfiguration('start_rviz'),
            OrSubstitution(
                NotSubstitution(LaunchConfiguration('headless')),
                LaunchConfiguration('rviz_with_headless'),
            ),
        )),
        arguments=['-d', rviz_config, '-f', world],
        parameters=[{'use_sim_time': True}], # 
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world', default_value='ocean_world',
            choices=['ocean_world', 'viana_port', 'cadiz_bay'],
            description='World to load from the simulator package.',
        ),
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Run Gazebo without its GUI.',
        ),
        DeclareLaunchArgument(
            'start_gz_gui',
            default_value='true',
            description='Open the Gazebo GUI. The simulation server is always started.',
        ),
        DeclareLaunchArgument(
            'start_rviz',
            default_value='true',
            description='Open RViz when permitted by the headless settings.',
        ),
        DeclareLaunchArgument(
            'rviz_with_headless', default_value='false',
            description='Keep RViz open when the Gazebo GUI is disabled with headless.',
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value='vessel_viz.rviz',
            description='RViz configuration file inside the simulator configs directory.',
        ),
        DeclareLaunchArgument(
            'gui_render_engine',
            default_value='ogre',
            description='Rendering engine used by the Gazebo GUI.',
        ),
        DeclareLaunchArgument(
            'spawn_vessel_v2',
            default_value='false',
            description='Include the vessel_v2 spawn launcher.',
        ),
        DeclareLaunchArgument(
            'spawn_uav',
            default_value='false',
            description='Include the x500 UAV spawn launcher.',
        ),
        DeclareLaunchArgument(
            'x500_external_control',
            default_value='false',
            description='Spawn X500 without the local Gazebo velocity controller.',
        ),
        DeclareLaunchArgument(
            'spawn_uuv',
            default_value='false',
            description='Include the BlueROV2 Heavy spawn launcher.',
        ),
        DeclareLaunchArgument(
            'spawn_durius',
            default_value='false',
            description='Optionally spawn DURIUS with the main simulator.',
        ),
        DeclareLaunchArgument(
            'spawn_nautilus',
            default_value='false',
            description='Optionally spawn Nautilus with the main simulator.',
        ),
        set_model_path,
        set_plugin_path,
        gz_sim,
        gz_gui,
        spawn_vessel_v2,
        spawn_uav,
        spawn_uuv,
        spawn_durius,
        windturbine_visualization,
        spawn_nautilus,
        bridge,

        # Map server / SLAM restano disabilitati per ora.
        # map_server,
        # lifecycle_manager,

        rviz_node,
    ])
