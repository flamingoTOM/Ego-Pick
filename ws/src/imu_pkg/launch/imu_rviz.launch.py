import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('imu_pkg')
    rviz_config = os.path.join(pkg, 'rviz', 'imu_display.rviz')

    return LaunchDescription([
        Node(
            package='imu_pkg',
            executable='imu_node',
            name='imu_driver_node',
            output='screen',
            parameters=[{
                'port': '/dev/ttyUSB1',
                'baudrate': 9600,
            }],
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='imu_broadcaster',
            arguments=['--x', '0', '--y', '0', '--z', '0',
                       '--qx', '0', '--qy', '0', '--qz', '0', '--qw', '1',
                       '--frame-id', 'base_link',
                       '--child-frame-id', 'imu_link'],
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            output='screen',
        ),
    ])
