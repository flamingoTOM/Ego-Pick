from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='encoder_pkg',
            executable='encoder_node',
            name='encoder_driver_node',
            output='screen',
            parameters=[{
                'port': '/dev/ttyUSB0',
                'baudrate': 9600,
                'rate': 10.0,
            }],
        ),
        Node(
            package='encoder_pkg',
            executable='encoder_plot_node',
            name='encoder_plot_node',
            output='screen',
        ),
    ])
