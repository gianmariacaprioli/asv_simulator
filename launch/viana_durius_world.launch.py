"""Start Viana do Castelo with DURIUS, Nautilus, BlueROV2 and X500."""

import math
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    launch_dir = Path(get_package_share_directory('asv_simulator')) / 'launch'

    def include(filename, **arguments):
        return GroupAction([
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(str(launch_dir / filename)),
                launch_arguments={'world': 'viana_port', **arguments}.items(),
            ),
        ])

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('start_gz_gui', default_value='true'),
        DeclareLaunchArgument('start_rviz', default_value='false'),
        DeclareLaunchArgument('rviz_config', default_value='vessel_viz.rviz'),
        include(
            'sim.launch.py', headless=LaunchConfiguration('headless'),
            start_gz_gui=LaunchConfiguration('start_gz_gui'),
            start_rviz=LaunchConfiguration('start_rviz'),
            rviz_config=LaunchConfiguration('rviz_config'),
        ),
        include('spawn_nautilus.launch.py', x='-37.0', y='-17.0'),
        include(
            'spawn_uuv.launch.py', x='0.0', y='-18.0', z='-2.5',
            yaw=str(math.pi / 5),
        ),
        # Nautilus starts at (-37, -17, 0.098) with yaw zero.
        include('spawn_uav.launch.py', x='-38.02', y='-17.0', z='0.16'),
    ])
