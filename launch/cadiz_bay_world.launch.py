"""Start Cadiz Bay with vessel_v2 and an X500 parked on its aft deck."""

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
                launch_arguments={'world': 'cadiz_bay', **arguments}.items(),
            ),
        ])

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        include('sim.launch.py', headless=LaunchConfiguration('headless')),
        include('spawn_vessel_v2.launch.py', z='0.24'),
        include('spawn_uav.launch.py', x='-2.5', z='1.35'),
    ])
