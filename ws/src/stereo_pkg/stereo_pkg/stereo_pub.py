#!/usr/bin/env python3
"""
USB双目摄像头 ROS2 节点
- v4l2-ctl FIFO 读 MJPG 原始数据
- 640x480 分辨率，DDS 发布左右 topic
- DDS 队列 depth=1 防止旧帧积压
"""

import os
import signal
import subprocess
import tempfile
import threading
import queue

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Header
from turbojpeg import TurboJPEG


class V4L2FIFOCapture:
    def __init__(self, device="/dev/video8", width=1280, height=480):
        self.device = device
        self.width = width
        self.height = height
        self.actual_w = width
        self.actual_h = height
        self._fd = None
        self._proc = None
        self._buf = b''
        self._open()

    def _open(self):
        fifo = tempfile.mktemp(suffix='.mjpg')
        os.mkfifo(fifo)
        self._fifo = fifo

        self._proc = subprocess.Popen(
            ['v4l2-ctl', '-d', self.device,
             '--set-fmt-video', f'width={self.width},height={self.height},pixelformat=MJPG',
             '--set-parm', '30',
             '--stream-mmap', '--stream-to=' + fifo],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setsid,
        )
        self._fd = open(fifo, 'rb')
        self._buf = b''
        while True:
            chunk = self._fd.read(16384)
            if not chunk:
                break
            self._buf += chunk
            idx = self._buf.find(b'\xff\xd8', 2)
            if idx >= 0:
                self._buf = self._buf[idx:]
                break

    def read(self):
        data = self._buf
        self._buf = b''
        while True:
            chunk = self._fd.read(8192)
            if not chunk:
                return None
            data += chunk
            idx = data.find(b'\xff\xd8', 2)
            if idx >= 0:
                self._buf = data[idx:]
                return data[:idx]

    def close(self):
        if self._proc and self._proc.poll() is None:
            try:
                os.killpg(os.getpgid(self._proc.pid), signal.SIGTERM)
            except OSError:
                pass
            self._proc.wait()
        if self._fd:
            self._fd.close()
        try:
            os.unlink(self._fifo)
        except OSError:
            pass


class StereoCameraNode(Node):
    def __init__(self):
        super().__init__('stereo_camera_node')

        self.declare_parameter('device_index', 8)
        device_index = self.get_parameter('device_index').value
        self.declare_parameter('jpeg_quality', 50)
        jpeg_quality = self.get_parameter('jpeg_quality').value

        device = f"/dev/video{device_index}"
        self.get_logger().info(f'Opening camera at {device}...')

        try:
            self.cap = V4L2FIFOCapture(device, 1280, 480)
        except Exception as e:
            self.get_logger().error(f'无法打开摄像头: {e}')
            return

        self.get_logger().info(
            f'Camera: {self.cap.actual_w}x{self.cap.actual_h} @ 30fps MJPG')

        self.jpeg = TurboJPEG()
        self.jpeg_quality = jpeg_quality

        qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
        )
        self.left_pub = self.create_publisher(CompressedImage, 'stereo/left', qos)
        self.right_pub = self.create_publisher(CompressedImage, 'stereo/right', qos)

        self._mjpeg_q = queue.Queue(maxsize=3)
        self._latest_left = None
        self._latest_right = None
        self._lock = threading.Lock()
        self._running = True

        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()
        self._encode_thread = threading.Thread(target=self._encode_loop, daemon=True)
        self._encode_thread.start()

        self.timer = self.create_timer(1.0 / 30.0, self.publish_frame)

    def _read_loop(self):
        while self._running:
            try:
                data = self.cap.read()
                if data is None or len(data) < 100:
                    continue
                if self._mjpeg_q.full():
                    try:
                        self._mjpeg_q.get_nowait()
                    except queue.Empty:
                        pass
                self._mjpeg_q.put_nowait(data)
            except Exception:
                continue

    def _encode_loop(self):
        while self._running:
            try:
                mjpeg_data = self._mjpeg_q.get(timeout=1.0)
            except queue.Empty:
                continue

            frame = cv2.imdecode(np.frombuffer(mjpeg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue

            mid = self.cap.actual_w // 2
            left = frame[:, mid:]
            right = frame[:, :mid]

            left_buf = self.jpeg.encode(left, self.jpeg_quality)
            right_buf = self.jpeg.encode(right, self.jpeg_quality)

            with self._lock:
                self._latest_left = left_buf
                self._latest_right = right_buf

    def publish_frame(self):
        with self._lock:
            if self._latest_left is None:
                return
            left_buf = self._latest_left
            right_buf = self._latest_right
            self._latest_left = None
            self._latest_right = None

        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = 'camera'

        left_msg = CompressedImage()
        left_msg.header = header
        left_msg.format = 'jpeg'
        left_msg.data = left_buf
        self.left_pub.publish(left_msg)

        right_msg = CompressedImage()
        right_msg.header = header
        right_msg.format = 'jpeg'
        right_msg.data = right_buf
        self.right_pub.publish(right_msg)

    def destroy_node(self):
        self._running = False
        if hasattr(self, 'cap'):
            self.cap.close()
        super().destroy_node()


def main():
    rclpy.init()
    node = StereoCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
