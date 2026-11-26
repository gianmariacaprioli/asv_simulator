"""Start ocean_world with three vehicles positioned around the wind turbine."""

import math
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression


def generate_launch_description():
    launch_dir = Path(get_package_share_directory('asv_simulator')) / 'launch'

    def include(filename, *, condition=None, **arguments):
        return GroupAction([
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(str(launch_dir / filename)),
                launch_arguments={'world': 'ocean_world', **arguments}.items(),
            ),
        ], condition=condition)

    # Place the vessel east of the tower floater, bow toward its center.
    # Clearance is measured from the hull collision box to the cylinder.
    bow_and_floater = 3.0 + 13.11 / 2
    clearance = LaunchConfiguration('vessel_clearance')
    vessel_x = PythonExpression([str(bow_and_floater), ' + ', clearance])
    uav_x = PythonExpression([str(bow_and_floater + 2.5), ' + ', clearance])
    vessel_yaw = str(math.pi)
    # At z=-2 the floater radius is 3 m; the UUV is 0.50 m long.
    uuv_y = -(3.0 + 2.0 + 0.50 / 2)

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('start_rviz', default_value='false'),
        DeclareLaunchArgument(
            'vessel_clearance', default_value='5.0',
            description='Initial clearance in metres between the bow and the centre floater.',
        ),
        DeclareLaunchArgument('include_uuv', default_value='true'),
        include(
            'sim.launch.py', headless=LaunchConfiguration('headless'),
            start_rviz=LaunchConfiguration('start_rviz'),
        ),
        include('spawn_vessel_v2.launch.py', x=vessel_x, z='0.24', yaw=vessel_yaw),
        include(
            'spawn_uuv.launch.py', condition=IfCondition(LaunchConfiguration('include_uuv')),
            x='0.0', y=str(uuv_y), z='-2.0', yaw=str(math.pi / 2),
        ),
        include('spawn_uav.launch.py', x=uav_x, z='1.35', yaw=vessel_yaw),
    ])
