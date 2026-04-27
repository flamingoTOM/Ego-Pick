#!/usr/bin/env python3.10
"""
USB Camera Publisher for ROS2 Humble
Publishes camera frames to ROS2 image topic

Usage:
    1. Build workspace: cd ~/ego_ws && colcon build
    2. Source workspace: source install/setup.bash
    3. Run: python3 usb_cam_publisher.py
       Or (as ROS2 node): ros2 run ego_ws usb_cam_publisher
"""

import rclpy
from rclpy.node import Node
import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image


class UsbCamPublisher(Node):
    def __init__(self):
        super().__init__('usb_cam_publisher')

        # Declare parameters
        self.declare_parameter('device', '/dev/video8')
        self.declare_parameter('frame_id', 'usb_cam')
        self.declare_parameter('publish_rate', 30.0)

        device = self.get_parameter('device').value
        self.frame_id = self.get_parameter('frame_id').value
        publish_rate = self.get_parameter('publish_rate').value

        self.get_logger().info(f'Opening camera: {device}')

        # Open camera
        self.cap = cv2.VideoCapture(device)
        if not self.cap.isOpened():
            self.get_logger().error(f'Failed to open camera: {device}')
            raise RuntimeError(f'Cannot open camera: {device}')

        # Set camera resolution (optional)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        # Get actual properties
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.get_logger().info(f'Camera opened: {width}x{height} @ {fps}fps')

        # Bridge for OpenCV <-> ROS Image
        self.bridge = CvBridge()

        # Publisher
        self.publisher = self.create_publisher(Image, 'image_raw', 10)

        # Timer for publishing
        timer_period = 1.0 / publish_rate
        self.timer = self.create_timer(timer_period, self.publish_frame)

        self.get_logger().info('USB camera publisher started!')

    def publish_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn('Failed to read frame from camera')
            return

        # Convert BGR to RGB (ROS image message expects RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Create image message
        img_msg = self.bridge.cv2_to_imgmsg(frame_rgb, encoding='rgb8')
        img_msg.header.frame_id = self.frame_id
        img_msg.header.stamp = self.get_clock().now().to_msg()

        self.publisher.publish(img_msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UsbCamPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
