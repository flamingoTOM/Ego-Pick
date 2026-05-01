#!/usr/bin/env python3
"""
Ego-Pick 主界面
订阅编码器角度/距离 + 双目相机左右画面 + IMU 姿态 并可视化
"""

import sys
import threading
from collections import deque

import time
import math

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSHistoryPolicy, QoSReliabilityPolicy
from std_msgs.msg import Float64
from sensor_msgs.msg import CompressedImage, Imu

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QPolygonF, QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec


def to_qimage(rgb):
    h, w = rgb.shape[:2]
    return QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)


class IMUAttitudeWidget(QWidget):
    """IMU 姿态可视化 — 姿态指示器 (飞机图标 + 航向弧)"""
    def __init__(self):
        super().__init__()
        self.setFixedSize(260, 260)
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.acc_x = 0.0
        self.acc_y = 0.0
        self.acc_z = 0.0
        self.gyro_x = 0.0
        self.gyro_y = 0.0
        self.gyro_z = 0.0

    def set_attitude(self, roll, pitch, yaw, ax=0, ay=0, az=0, gx=0, gy=0, gz=0):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.acc_x = ax
        self.acc_y = ay
        self.acc_z = az
        self.gyro_x = gx
        self.gyro_y = gy
        self.gyro_z = gz
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 12

        # 背景
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.setBrush(QColor(25, 25, 25))
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # 刻度
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        for deg in range(0, 360, 30):
            rad = math.radians(deg)
            x1 = cx + (r - 6) * math.sin(rad)
            y1 = cy - (r - 6) * math.cos(rad)
            x2 = cx + (r - 1) * math.sin(rad)
            y2 = cy - (r - 1) * math.cos(rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            if deg % 90 == 0:
                painter.setPen(QPen(QColor(170, 170, 170), 1))
                painter.setFont(QFont("Arial", 8, QFont.Bold))
                labels = {0: "N", 90: "E", 180: "S", 270: "W"}
                painter.drawText(int(x2) - 5, int(y2) + 4, labels[deg])
                painter.setPen(QPen(QColor(100, 100, 100), 1))

        # 飞机图标 (随 roll 旋转)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.roll)
        painter.setPen(QPen(QColor(0, 200, 255), 2))
        painter.setBrush(QColor(0, 200, 255))
        wing = r * 0.55
        body = r * 0.45
        pts = QPolygonF([
            QPointF(0, -body), QPointF(-5, 0), QPointF(-wing, 3), QPointF(-4, 3),
            QPointF(-3, body * 0.25), QPointF(0, body * 0.2),
            QPointF(3, body * 0.25), QPointF(4, 3), QPointF(wing, 3), QPointF(5, 0),
        ])
        painter.drawPolygon(pts)
        painter.restore()

        # pitch 水平线
        painter.save()
        painter.translate(cx, cy)
        p_off = self.pitch * r * 0.015
        p_off = max(-r * 0.6, min(r * 0.6, p_off))
        painter.setPen(QPen(QColor(255, 140, 0), 2))
        ln = int(r * 0.35)
        painter.drawLine(-ln, int(p_off), ln, int(p_off))
        painter.restore()

        # yaw 弧线
        painter.save()
        painter.setPen(QPen(QColor(255, 200, 0), 3))
        painter.drawArc(cx - r + 3, cy - r + 3, (r - 3) * 2, (r - 3) * 2,
                        -90 * 16, int(self.yaw * 16))
        painter.restore()

        # 数值
        painter.setFont(QFont("Consolas", 8))
        painter.setPen(QColor(0, 200, 255))
        by = cy + r + 14
        painter.drawText(5, int(by), f"R:{self.roll:+.1f}°  P:{self.pitch:+.1f}°  Y:{self.yaw:+.1f}°")
        painter.setPen(QColor(150, 150, 150))
        painter.drawText(5, int(by) + 14, f"Acc: ({self.acc_x:.1f}, {self.acc_y:.1f}, {self.acc_z:.1f})")
        painter.drawText(5, int(by) + 28, f"Gyro: ({self.gyro_x:.2f}, {self.gyro_y:.2f}, {self.gyro_z:.2f})")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ego-Pick Monitor")
        self.setGeometry(100, 100, 1400, 900)

        self.max_points = 200
        self.time_data = deque(maxlen=self.max_points)
        self.angle_data = deque(maxlen=self.max_points)
        self.distance_data = deque(maxlen=self.max_points)
        self.time_counter = 0

        # IMU chart data
        self.imu_time_data = deque(maxlen=self.max_points)
        self.imu_roll_data = deque(maxlen=self.max_points)
        self.imu_pitch_data = deque(maxlen=self.max_points)
        self.imu_yaw_data = deque(maxlen=self.max_points)
        self.imu_gx_data = deque(maxlen=self.max_points)
        self.imu_gy_data = deque(maxlen=self.max_points)
        self.imu_gz_data = deque(maxlen=self.max_points)
        self.imu_time_counter = 0

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Top row: encoder info + IMU attitude ---
        top_layout = QHBoxLayout()

        enc_col = QVBoxLayout()
        self.angle_label = QLabel("Angle: --.- °")
        self.distance_label = QLabel("Distance: --.- mm")
        self.status_label = QLabel("Status: Connecting...")
        enc_col.addWidget(self.angle_label)
        enc_col.addWidget(self.distance_label)
        enc_col.addWidget(self.status_label)

        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet("font-weight: bold; color: lime; font-size: 13px;")
        enc_col.addWidget(self.fps_label)

        top_layout.addLayout(enc_col)
        top_layout.addSpacing(20)

        imu_col = QVBoxLayout()
        imu_title = QLabel("IMU Attitude")
        imu_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        imu_col.addWidget(imu_title, alignment=Qt.AlignCenter)
        self.imu_widget = IMUAttitudeWidget()
        imu_col.addWidget(self.imu_widget, alignment=Qt.AlignCenter)
        top_layout.addLayout(imu_col)

        main_layout.addLayout(top_layout)

        # --- Encoder charts ---
        enc_chart = QHBoxLayout()
        enc_chart.addWidget(QLabel("Encoder:"))
        self.figure = Figure(figsize=(12, 2.2))
        self.canvas = FigureCanvas(self.figure)
        enc_chart.addWidget(self.canvas)
        main_layout.addLayout(enc_chart)

        gs = GridSpec(1, 2, figure=self.figure)
        self.ax_angle = self.figure.add_subplot(gs[0, 0])
        self.ax_dist = self.figure.add_subplot(gs[0, 1])

        self.ax_angle.set_xlabel("Time"); self.ax_angle.set_ylabel("Angle (°)")
        self.ax_angle.set_title("Angle vs Time"); self.ax_angle.set_ylim(0, 360)
        self.ax_angle.set_autoscaley_on(False); self.ax_angle.grid(True)

        self.ax_dist.set_xlabel("Time"); self.ax_dist.set_ylabel("Distance (mm)")
        self.ax_dist.set_title("Pick Distance vs Time"); self.ax_dist.set_ylim(0, 60)
        self.ax_dist.set_autoscaley_on(False); self.ax_dist.grid(True)

        self.line_angle, = self.ax_angle.plot([], [], 'b-', linewidth=1)
        self.line_dist, = self.ax_dist.plot([], [], 'r-', linewidth=1)

        # --- IMU charts ---
        imu_chart = QHBoxLayout()
        imu_chart.addWidget(QLabel("IMU:"))
        self.imu_figure = Figure(figsize=(12, 1.8))
        self.imu_canvas = FigureCanvas(self.imu_figure)
        imu_chart.addWidget(self.imu_canvas)
        main_layout.addLayout(imu_chart)

        gs_imu = GridSpec(1, 2, figure=self.imu_figure)
        self.ax_euler = self.imu_figure.add_subplot(gs_imu[0, 0])
        self.ax_gyro = self.imu_figure.add_subplot(gs_imu[0, 1])

        self.ax_euler.set_xlabel("Time"); self.ax_euler.set_ylabel("Angle (°)")
        self.ax_euler.set_title("Euler Angles"); self.ax_euler.set_ylim(-180, 180)
        self.ax_euler.set_autoscaley_on(False); self.ax_euler.grid(True)

        self.ax_gyro.set_xlabel("Time"); self.ax_gyro.set_ylabel("Rate (°/s)")
        self.ax_gyro.set_title("Angular Velocity"); self.ax_gyro.set_ylim(-200, 200)
        self.ax_gyro.set_autoscaley_on(False); self.ax_gyro.grid(True)

        self.l_roll, = self.ax_euler.plot([], [], 'r-', linewidth=1, label='Roll')
        self.l_pitch, = self.ax_euler.plot([], [], 'g-', linewidth=1, label='Pitch')
        self.l_yaw, = self.ax_euler.plot([], [], 'b-', linewidth=1, label='Yaw')
        self.ax_euler.legend(loc='upper right', fontsize=7)

        self.l_gx, = self.ax_gyro.plot([], [], 'r-', linewidth=1, label='X')
        self.l_gy, = self.ax_gyro.plot([], [], 'g-', linewidth=1, label='Y')
        self.l_gz, = self.ax_gyro.plot([], [], 'b-', linewidth=1, label='Z')
        self.ax_gyro.legend(loc='upper right', fontsize=7)

        # --- Stereo cameras ---
        cam_layout = QHBoxLayout()
        self.left_label = QLabel("Left Camera")
        self.left_label.setMinimumSize(320, 240)
        self.left_label.setStyleSheet("border: 2px solid green;")
        self.left_label.setAlignment(Qt.AlignCenter)
        cam_layout.addWidget(self.left_label)

        self.right_label = QLabel("Right Camera")
        self.right_label.setMinimumSize(320, 240)
        self.right_label.setStyleSheet("border: 2px solid red;")
        self.right_label.setAlignment(Qt.AlignCenter)
        cam_layout.addWidget(self.right_label)

        main_layout.addLayout(cam_layout)


class SubscriberNode(Node):
    def __init__(self):
        super().__init__('ego_pick_subscriber')
        self._lock = threading.Lock()
        self._latest_angle = 0.0
        self._new_distance = None
        self._latest_left = None
        self._latest_right = None
        self._latest_imu = None
        self._fps_frames = 0
        self._fps_last_time = time.time()
        self._current_fps = 0

        stereo_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
        )
        self.create_subscription(Float64, 'encoder/angle', self.angle_callback, 10)
        self.create_subscription(Float64, 'encoder/pick_distance', self.distance_callback, 10)
        self.create_subscription(CompressedImage, 'stereo/left', self.left_callback, stereo_qos)
        self.create_subscription(CompressedImage, 'stereo/right', self.right_callback, stereo_qos)
        self.create_subscription(Imu, 'imu/data_raw', self.imu_callback, 10)

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

    def imu_callback(self, msg):
        with self._lock:
            q = msg.orientation
            # quaternion to euler (ZYX)
            sinr_cosp = 2 * (q.w * q.x + q.y * q.z)
            cosr_cosp = 1 - 2 * (q.x * q.x + q.y * q.y)
            roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

            sinp = 2 * (q.w * q.y - q.z * q.x)
            pitch = math.degrees(math.asin(max(-1, min(1, sinp))))

            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

            self._latest_imu = {
                'roll': roll,
                'pitch': pitch,
                'yaw': yaw,
                'gx': math.degrees(msg.angular_velocity.x),
                'gy': math.degrees(msg.angular_velocity.y),
                'gz': math.degrees(msg.angular_velocity.z),
                'ax': msg.linear_acceleration.x,
                'ay': msg.linear_acceleration.y,
                'az': msg.linear_acceleration.z,
            }

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

    def pop_imu_data(self):
        with self._lock:
            data = self._latest_imu
            self._latest_imu = None
            return data

    def get_camera_frames(self):
        with self._lock:
            return self._latest_left, self._latest_right, self._current_fps


def main():
    rclpy.init()

    app = QApplication(sys.argv)
    window = MainWindow()
    node = SubscriberNode()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    def update_timer():
        # --- Encoder ---
        result = node.pop_encoder_data()
        if result is not None:
            distance, angle = result
            window.time_data.append(window.time_counter)
            window.angle_data.append(angle)
            window.distance_data.append(distance)
            window.time_counter += 1

            window.line_angle.set_data(list(window.time_data), list(window.angle_data))
            window.line_dist.set_data(list(window.time_data), list(window.distance_data))

            tmax = max(window.time_data) if window.time_data else 1
            window.ax_angle.set_xlim(0, tmax)
            window.ax_dist.set_xlim(0, tmax)

            window.angle_label.setText(f"Angle: {angle:.1f} °")
            window.distance_label.setText(f"Distance: {distance:.1f} mm")
            window.status_label.setText("Status: Connected")
            window.canvas.draw()

        # --- IMU ---
        imu = node.pop_imu_data()
        if imu is not None:
            window.imu_widget.set_attitude(
                imu['roll'], imu['pitch'], imu['yaw'],
                imu['ax'], imu['ay'], imu['az'],
                imu['gx'], imu['gy'], imu['gz']
            )

            window.imu_time_data.append(window.imu_time_counter)
            window.imu_roll_data.append(imu['roll'])
            window.imu_pitch_data.append(imu['pitch'])
            window.imu_yaw_data.append(imu['yaw'])
            window.imu_gx_data.append(imu['gx'])
            window.imu_gy_data.append(imu['gy'])
            window.imu_gz_data.append(imu['gz'])
            window.imu_time_counter += 1

            tmax = max(window.imu_time_data) if window.imu_time_data else 1
            window.ax_euler.set_xlim(0, tmax)
            window.ax_gyro.set_xlim(0, tmax)

            window.l_roll.set_data(list(window.imu_time_data), list(window.imu_roll_data))
            window.l_pitch.set_data(list(window.imu_time_data), list(window.imu_pitch_data))
            window.l_yaw.set_data(list(window.imu_time_data), list(window.imu_yaw_data))
            window.l_gx.set_data(list(window.imu_time_data), list(window.imu_gx_data))
            window.l_gy.set_data(list(window.imu_time_data), list(window.imu_gy_data))
            window.l_gz.set_data(list(window.imu_time_data), list(window.imu_gz_data))
            window.imu_canvas.draw()

        # --- Cameras ---
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
