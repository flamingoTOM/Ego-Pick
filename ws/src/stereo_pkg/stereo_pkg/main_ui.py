#!/usr/bin/env python3
"""
Ego-Pick 主界面
订阅编码器角度/距离 + 双目相机左右画面并可视化
"""

import sys
import threading
from collections import deque

import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from sensor_msgs.msg import CompressedImage

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ego-Pick Monitor")
        self.setGeometry(100, 100, 1200, 700)

        self.max_points = 200
        self.time_data = deque(maxlen=self.max_points)
        self.angle_data = deque(maxlen=self.max_points)
        self.distance_data = deque(maxlen=self.max_points)
        self.time_counter = 0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        status_layout = QHBoxLayout()
        self.angle_label = QLabel("Angle: --.- °")
        self.distance_label = QLabel("Distance: --.- mm")
        self.status_label = QLabel("Status: Connecting...")
        status_layout.addWidget(self.angle_label)
        status_layout.addWidget(self.distance_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_label)
        layout.addLayout(status_layout)

        self.figure = Figure(figsize=(12, 2.5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        gs = GridSpec(1, 2, figure=self.figure)
        self.ax_angle = self.figure.add_subplot(gs[0, 0])
        self.ax_distance = self.figure.add_subplot(gs[0, 1])

        self.ax_angle.set_xlabel("Time (frames)")
        self.ax_angle.set_ylabel("Angle (°)")
        self.ax_angle.set_title("Angle vs Time")
        self.ax_angle.set_ylim(0, 360)
        self.ax_angle.set_autoscaley_on(False)
        self.ax_angle.grid(True)

        self.ax_distance.set_xlabel("Time (frames)")
        self.ax_distance.set_ylabel("Distance (mm)")
        self.ax_distance.set_title("Pick Distance vs Time")
        self.ax_distance.set_ylim(0, 60)
        self.ax_distance.set_autoscaley_on(False)
        self.ax_distance.grid(True)

        self.line_angle, = self.ax_angle.plot([], [], 'b-', linewidth=1)
        self.line_distance, = self.ax_distance.plot([], [], 'r-', linewidth=1)

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

        fps_layout = QHBoxLayout()
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet("font-weight: bold;")
        fps_layout.addWidget(self.fps_label)
        fps_layout.addStretch()
        layout.addLayout(fps_layout)


class SubscriberNode(Node):
    def __init__(self):
        super().__init__('ego_pick_subscriber')
        self._lock = threading.Lock()
        self._latest_angle = 0.0
        self._new_distance = None
        self._latest_left = None
        self._latest_right = None
        self._fps_frames = 0
        self._fps_last_time = time.time()
        self._current_fps = 0

        self.create_subscription(Float64, 'encoder/angle', self.angle_callback, 10)
        self.create_subscription(Float64, 'encoder/pick_distance', self.distance_callback, 10)
        self.create_subscription(CompressedImage, 'stereo/left', self.left_callback, 10)
        self.create_subscription(CompressedImage, 'stereo/right', self.right_callback, 10)

    def angle_callback(self, msg):
        with self._lock:
            self._latest_angle = msg.data

    def distance_callback(self, msg):
        with self._lock:
            self._new_distance = (msg.data, self._latest_angle)

    def left_callback(self, msg):
        with self._lock:
            data = np.frombuffer(msg.data, dtype=np.uint8)
            self._latest_left = cv2.imdecode(data, cv2.IMREAD_COLOR)
            self._count_fps()

    def right_callback(self, msg):
        with self._lock:
            data = np.frombuffer(msg.data, dtype=np.uint8)
            self._latest_right = cv2.imdecode(data, cv2.IMREAD_COLOR)

    def _count_fps(self):
        self._fps_frames += 1
        now = time.time()
        if now - self._fps_last_time >= 1.0:
            self._current_fps = self._fps_frames / (now - self._fps_last_time)
            self._fps_frames = 0
            self._fps_last_time = now

    def pop_encoder_data(self):
        with self._lock:
            data = self._new_distance
            self._new_distance = None
            return data

    def get_camera_frames(self):
        with self._lock:
            return self._latest_left, self._latest_right, self._current_fps


def to_qimage(rgb):
    h, w = rgb.shape[:2]
    return QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)


def main():
    rclpy.init()

    app = QApplication(sys.argv)
    window = MainWindow()
    node = SubscriberNode()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    def update_timer():
        result = node.pop_encoder_data()
        if result is not None:
            distance, angle = result
            window.time_data.append(window.time_counter)
            window.angle_data.append(angle)
            window.distance_data.append(distance)
            window.time_counter += 1

            window.line_angle.set_data(list(window.time_data), list(window.angle_data))
            window.line_distance.set_data(list(window.time_data), list(window.distance_data))

            tmax = max(window.time_data) if window.time_data else 1
            window.ax_angle.set_xlim(0, tmax)
            window.ax_distance.set_xlim(0, tmax)

            window.angle_label.setText(f"Angle: {angle:.1f} °")
            window.distance_label.setText(f"Distance: {distance:.1f} mm")
            window.status_label.setText("Status: Connected")
            window.canvas.draw()

        left, right, fps = node.get_camera_frames()
        if left is not None:
            left_rgb = cv2.cvtColor(left, cv2.COLOR_BGR2RGB)
            window.left_label.setPixmap(QPixmap.fromImage(to_qimage(left_rgb)))
        if right is not None:
            right_rgb = cv2.cvtColor(right, cv2.COLOR_BGR2RGB)
            window.right_label.setPixmap(QPixmap.fromImage(to_qimage(right_rgb)))
        window.fps_label.setText(f"FPS: {fps:.1f}")

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
