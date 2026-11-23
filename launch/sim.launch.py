import os
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import IfElseSubstitution, LaunchConfiguration
from launch_ros.actions import Node, LifecycleNode
from ament_index_python.packages import (
    get_package_prefix,
    get_package_share_directory,
)


def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_asv_sim = get_package_share_directory('asv_simulator')
    pkg_asv_sim_prefix = get_package_prefix('asv_simulator')
    
    world_file = os.path.join(pkg_asv_sim, 'worlds', 'ocean_world.sdf')
    rviz_config = os.path.join(pkg_asv_sim, 'configs', 'vessel_viz.rviz')
    map_yaml_file = os.path.join(pkg_asv_sim, 'map', 'map.yaml')

    set_model_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(pkg_asv_sim, 'models')
    )

    set_plugin_path = AppendEnvironmentVariable(
        'GZ_SIM_SYSTEM_PLUGIN_PATH',
        os.path.join(pkg_asv_sim_prefix, 'lib')
    )

    # Nodo 1: Avvia Gazebo Harmonic
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': [
                IfElseSubstitution(LaunchConfiguration('headless'), '-s ', ''),
                f'-r -v 4 "{world_file}"',
            ]
        }.items(),
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
    def optional_spawn_launch(launch_file, flag):
        return GroupAction(
            scoped=True,
            forwarding=False,
            condition=IfCondition(LaunchConfiguration(flag)),
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
        'spawn_vessel_v2',
    )
    spawn_uav = optional_spawn_launch(
        'spawn_uav.launch.py',
        'spawn_uav',
    )
    spawn_uuv = optional_spawn_launch(
        'spawn_uuv.launch.py',
        'spawn_uuv',
    )
    spawn_durius = optional_spawn_launch(
        'spawn_durius.launch.py',
        'spawn_durius',
    )
    spawn_nautilus = optional_spawn_launch(
        'spawn_nautilus.launch.py',
        'spawn_nautilus',
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
        condition=UnlessCondition(LaunchConfiguration('headless')),
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}], # 
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'headless',
            default_value='false',
            description='Run Gazebo server only and skip RViz.',
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
        spawn_vessel_v2,
        spawn_uav,
        spawn_uuv,
        spawn_durius,
        spawn_nautilus,
        bridge,

        # Map server / SLAM restano disabilitati per ora.
        # map_server,
        # lifecycle_manager,

        rviz_node,
    ])
