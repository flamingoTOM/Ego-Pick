#!/usr/bin/env python3
"""
IMU 立方体可视化 — Qt 独立窗口（不经过 RViz）
订阅 /imu/data_raw，将四元数姿态映射到一个 3D 旋转立方体上。
"""

import math
import threading
from collections import deque

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QWidget
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont


# ---------------------------------------------------------------------------
# 3D math helpers
# ---------------------------------------------------------------------------

def quat_to_rotation_matrix(qx, qy, qz, qw):
    """四元数 → 3×3 旋转矩阵"""
    s = 2.0 / (qx * qx + qy * qy + qz * qz + qw * qw)
    m = np.eye(3)
    m[0, 0] = 1 - s * (qy * qy + qz * qz)
    m[0, 1] = s * (qx * qy - qz * qw)
    m[0, 2] = s * (qx * qz + qy * qw)
    m[1, 0] = s * (qx * qy + qz * qw)
    m[1, 1] = 1 - s * (qx * qx + qz * qz)
    m[1, 2] = s * (qy * qz - qx * qw)
    m[2, 0] = s * (qx * qz - qy * qw)
    m[2, 1] = s * (qy * qz + qx * qw)
    m[2, 2] = 1 - s * (qx * qx + qy * qy)
    return m


def project(point3d, fov=500, cx=200, cy=200):
    """3D 点 → 2D 屏幕坐标（透视投影）"""
    z = point3d[2] + 5.0  # 偏移避免除零
    scale = fov / z
    return (point3d[0] * scale + cx, -point3d[1] * scale + cy)


# 立方体 8 个顶点 (±1, ±1, ±1)
CUBE_VERTICES = [
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1],  [1, -1, 1],  [1, 1, 1],  [-1, 1, 1],
]

# 12 条边 (顶点索引)
CUBE_EDGES = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7),
]

# 6 个面 (顶点索引, 逆时针顺序)
CUBE_FACES = [
    (0, 1, 2, 3),  # 前
    (5, 4, 7, 6),  # 后
    (4, 0, 3, 7),  # 左
    (1, 5, 6, 2),  # 右
    (3, 2, 6, 7),  # 上
    (4, 5, 1, 0),  # 下
]

# 面颜色 (与轴对齐: 前=红, 后=暗红, 左=绿, 右=暗绿, 上=蓝, 下=暗蓝)
FACE_COLORS = [
    QColor(220, 60, 60, 160),   # 前 - 红 (X+)
    QColor(120, 30, 30, 120),   # 后 - 暗红 (X-)
    QColor(60, 200, 60, 160),   # 左 - 绿 (Y+)
    QColor(30, 100, 30, 120),   # 右 - 暗绿 (Y-)
    QColor(60, 80, 220, 160),   # 上 - 蓝 (Z+)
    QColor(30, 40, 120, 120),   # 下 - 暗蓝 (Z-)
]


# ---------------------------------------------------------------------------
# Qt 立方体 widget
# ---------------------------------------------------------------------------

class CubeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(420, 420)
        self.quat = [0.0, 0.0, 0.0, 1.0]  # x,y,z,w
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.acc = [0.0, 0.0, 0.0]
        self.gyro = [0.0, 0.0, 0.0]

    def set_imu(self, quat, euler, acc, gyro):
        self.quat = quat
        self.roll, self.pitch, self.yaw = euler
        self.acc = acc
        self.gyro = gyro
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        painter.fillRect(0, 0, w, h, QColor(20, 20, 30))

        qx, qy, qz, qw = self.quat
        rot = quat_to_rotation_matrix(qx, qy, qz, qw)

        # 变换后的顶点
        transformed = []
        for v in CUBE_VERTICES:
            p = rot @ np.array(v)
            transformed.append(project(p, fov=400, cx=cx, cy=cy))

        # 面 ( painter's algorithm: 按深度排序 )
        face_depths = []
        for i, face in enumerate(CUBE_FACES):
            avg_z = np.mean([(rot @ np.array(CUBE_VERTICES[j]))[2] for j in face])
            face_depths.append((avg_z, i))
        face_depths.sort()  # 远 → 近

        for _, idx in face_depths:
            face = CUBE_FACES[idx]
            pts = [QPointF(transformed[j][0], transformed[j][1]) for j in face]
            painter.setBrush(QBrush(FACE_COLORS[idx]))
            painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
            painter.drawPolygon(pts)

        # 边
        painter.setPen(QPen(QColor(200, 200, 255, 200), 2))
        for i, j in CUBE_EDGES:
            painter.drawLine(
                int(transformed[i][0]), int(transformed[i][1]),
                int(transformed[j][0]), int(transformed[j][1]),
            )

        # 顶点
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        for x2, y2 in transformed:
            painter.drawEllipse(int(x2) - 3, int(y2) - 3, 6, 6)

        # 轴标签 (旋转后的 X/Y/Z 方向)
        axes = [
            ('X+', [1, 0, 0], QColor(255, 80, 80)),
            ('Y+', [0, 1, 0], QColor(80, 255, 80)),
            ('Z+', [0, 0, 1], QColor(80, 80, 255)),
        ]
        painter.setFont(QFont("Consolas", 11, QFont.Bold))
        for label, direction, color in axes:
            p = rot @ np.array(direction) * 2.0
            px, py = project(p, fov=400, cx=cx, cy=cy)
            painter.setPen(color)
            painter.drawText(int(px) - 8, int(py) + 4, label)

        # 数值
        painter.setFont(QFont("Consolas", 10))
        info_y = h - 70
        painter.setPen(QColor(200, 200, 255))
        painter.drawText(15, info_y, f"Roll: {self.roll:+.1f}°  Pitch: {self.pitch:+.1f}°  Yaw: {self.yaw:+.1f}°")
        painter.setPen(QColor(130, 130, 130))
        painter.drawText(15, info_y + 18, f"Acc: ({self.acc[0]:.2f}, {self.acc[1]:.2f}, {self.acc[2]:.2f}) m/s²")
        painter.drawText(15, info_y + 36, f"Gyro: ({self.gyro[0]:.2f}, {self.gyro[1]:.2f}, {self.gyro[2]:.2f}) deg/s")


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IMU Cube Viewer")
        self.setGeometry(100, 100, 500, 560)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("IMU Attitude — Cube Visualization")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin: 8px;")
        layout.addWidget(title)

        self.status = QLabel("Waiting for IMU data...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: orange; font-size: 12px;")
        layout.addWidget(self.status)

        self.cube = CubeWidget()
        layout.addWidget(self.cube, alignment=Qt.AlignCenter)


# ---------------------------------------------------------------------------
# ROS2 节点
# ---------------------------------------------------------------------------

class IMUViewerNode(Node):
    def __init__(self):
        super().__init__('imu_viewer_node')
        self._lock = threading.Lock()
        self._latest = None
        self.create_subscription(Imu, 'imu/data_raw', self.imu_callback, 10)

    def imu_callback(self, msg: Imu):
        q = msg.orientation
        quat = [q.x, q.y, q.z, q.w]

        roll = math.degrees(math.atan2(
            2 * (q.w * q.x + q.y * q.z),
            1 - 2 * (q.x * q.x + q.y * q.y)))
        sinp = 2 * (q.w * q.y - q.z * q.x)
        pitch = math.degrees(math.asin(max(-1, min(1, sinp))))
        yaw = math.degrees(math.atan2(
            2 * (q.w * q.z + q.x * q.y),
            1 - 2 * (q.y * q.y + q.z * q.z)))

        with self._lock:
            self._latest = {
                'quat': quat,
                'euler': (roll, pitch, yaw),
                'acc': (msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z),
                'gyro': (math.degrees(msg.angular_velocity.x),
                         math.degrees(msg.angular_velocity.y),
                         math.degrees(msg.angular_velocity.z)),
            }

    def pop(self):
        with self._lock:
            data = self._latest
            self._latest = None
            return data


def main():
    rclpy.init()

    app = QApplication([])
    app.setStyleSheet("QMainWindow, QWidget { background-color: #1a1a2e; } QLabel { color: #ddd; }")
    window = MainWindow()
    node = IMUViewerNode()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    def update():
        data = node.pop()
        if data is not None:
            window.cube.set_imu(
                data['quat'], data['euler'],
                data['acc'], data['gyro'])
            window.status.setText("IMU Connected")
            window.status.setStyleSheet("color: lime; font-size: 12px;")

    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(50)

    window.show()
    try:
        app.exec_()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
