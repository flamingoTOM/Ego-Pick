#!/usr/bin/env python3
"""
IMU 立方体可视化节点
订阅 /imu/data_raw，将四元数姿态映射到 RViz2 中的立方体 Marker。
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Quaternion, Vector3, Point
from std_msgs.msg import ColorRGBA


class IMUCubeNode(Node):
    def __init__(self):
        super().__init__('imu_cube_node')
        self.marker_pub = self.create_publisher(Marker, 'imu/cube_marker', 10)
        self.create_subscription(Imu, 'imu/data_raw', self.imu_callback, 10)

    def imu_callback(self, msg: Imu):
        marker = Marker()
        marker.header = msg.header
        marker.ns = 'imu_cube'
        marker.id = 0
        marker.type = Marker.CUBE
        marker.action = Marker.ADD
        marker.lifetime = rclpy.duration.Duration(seconds=0).to_msg()

        # 立方体尺寸
        marker.scale = Vector3(x=0.3, y=0.3, z=0.3)

        # 位置 (原点在 base_link 前方 0.5m 上方 0.5m，便于观察)
        marker.pose.position = Point(x=0.5, y=0.0, z=0.5)
        marker.pose.orientation = msg.orientation  # 直接使用 IMU 四元数

        # 颜色：蓝底半透明
        marker.color = ColorRGBA(r=0.1, g=0.5, b=1.0, a=0.7)

        self.marker_pub.publish(marker)


def main():
    rclpy.init()
    node = IMUCubeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
