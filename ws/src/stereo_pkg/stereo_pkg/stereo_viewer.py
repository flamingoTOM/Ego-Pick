#!/usr/bin/env python3
"""
双目相机画面查看器
订阅 /stereo/left 和 /stereo/right (各 ~27KB MJPG)，本地解码并分屏显示
"""

import sys
import threading
import time

import numpy as np
import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class StereoViewerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stereo Camera Viewer")
        self.setGeometry(100, 100, 800, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        camera_layout = QHBoxLayout()

        self.left_label = QLabel("Left Camera")
        self.left_label.setMinimumSize(320, 240)
        self.left_label.setStyleSheet("border: 2px solid green;")
        self.left_label.setAlignment(Qt.AlignCenter)
        camera_layout.addWidget(self.left_label)

        self.right_label = QLabel("Right Camera")
        self.right_label.setMinimumSize(320, 240)
        self.right_label.setStyleSheet("border: 2px solid red;")
        self.right_label.setAlignment(Qt.AlignCenter)
        camera_layout.addWidget(self.right_label)

        layout.addLayout(camera_layout)

        status_layout = QHBoxLayout()
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet("font-weight: bold;")
        self.status_label = QLabel("Waiting for frames...")
        status_layout.addWidget(self.fps_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)


class StereoSubscriberNode(Node):
    def __init__(self):
        super().__init__('stereo_viewer_node')
        self._lock = threading.Lock()
        self._latest_left = None
        self._latest_right = None
        self._fps_frames = 0
        self._fps_last_time = time.time()
        self._current_fps = 0

        qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
        )
        self.create_subscription(CompressedImage, 'stereo/left', self.left_cb, qos)
        self.create_subscription(CompressedImage, 'stereo/right', self.right_cb, qos)

    def left_cb(self, msg):
        data = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if frame is None:
            return
        with self._lock:
            self._latest_left = frame
            self._fps_frames += 1
            now = time.time()
            if now - self._fps_last_time >= 1.0:
                self._current_fps = self._fps_frames / (now - self._fps_last_time)
                self._fps_frames = 0
                self._fps_last_time = now

    def right_cb(self, msg):
        data = np.frombuffer(msg.data, dtype=np.uint8)
        frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if frame is None:
            return
        with self._lock:
            self._latest_right = frame

    def get_frames(self):
        with self._lock:
            left = self._latest_left.copy() if self._latest_left is not None else None
            right = self._latest_right.copy() if self._latest_right is not None else None
            fps = self._current_fps
            return left, right, fps


def to_qimage(rgb):
    h, w = rgb.shape[:2]
    return QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)


def main():
    rclpy.init()

    app = QApplication(sys.argv)
    window = StereoViewerWindow()
    node = StereoSubscriberNode()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    def update_timer():
        left, right, fps = node.get_frames()
        if left is not None:
            left_rgb = cv2.cvtColor(left, cv2.COLOR_BGR2RGB)
            window.left_label.setPixmap(QPixmap.fromImage(to_qimage(left_rgb)))
        if right is not None:
            right_rgb = cv2.cvtColor(right, cv2.COLOR_BGR2RGB)
            window.right_label.setPixmap(QPixmap.fromImage(to_qimage(right_rgb)))
        window.fps_label.setText(f"FPS: {fps:.1f}")
        window.status_label.setText("Receiving stereo frames...")

    timer = QTimer()
    timer.timeout.connect(update_timer)
    timer.start(50)

    window.show()

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
