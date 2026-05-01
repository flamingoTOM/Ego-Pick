"""IMU 立方体可视化 — Qt 独立窗口（不经过 RViz）"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
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
            package='imu_pkg',
            executable='qt_imu_viewer',
            name='qt_imu_viewer',
            output='screen',
        ),
    ])
