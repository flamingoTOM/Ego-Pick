from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='stereo_pkg',
            executable='stereo_camera_node',
            name='stereo_camera_node',
            output='screen',
            parameters=[{
                'device_index': 8,
                'jpeg_quality': 80,
            }],
        ),
        Node(
            package='stereo_pkg',
            executable='stereo_viewer_node',
            name='stereo_viewer_node',
            output='screen',
        ),
    ])
