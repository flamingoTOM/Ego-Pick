#!/usr/bin/env python3
"""
USB双目摄像头 - PyQt5显示左右原始画面和深度图
固定参数: 1280x480 MJPG 30FPS
集成深度估计功能
"""

import sys
import cv2
import numpy as np
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QHBoxLayout, QGroupBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

from depth_process import DepthProcessor


class CameraViewer(QMainWindow):
    # 固定参数
    FRAME_WIDTH = 1280   # 双目拼接: 左右各640
    FRAME_HEIGHT = 480
    TARGET_FPS = 30

    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB 双目摄像头 - 左/右/深度 三画面显示")

        # 打开摄像头 - 强制MSMF后端
        self.cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
        if not self.cap.isOpened():
            print("错误: 无法打开摄像头")
            sys.exit(1)
        print("使用后端: CAP_MSMF")

        # 强制MJPG格式
        FOURCC = cv2.VideoWriter_fourcc(*'MJPG')
        if not self.cap.set(cv2.CAP_PROP_FOURCC, FOURCC):
            print("警告: MJPG格式设置失败")

        # 设置分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, self.TARGET_FPS)

        # 获取实际参数
        self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
        self.fourcc_str = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

        print(f"摄像头: {self.actual_width}x{self.actual_height} @ {actual_fps:.0f} FPS | 格式: {self.fourcc_str}")

        # 初始化深度处理器
        print("初始化深度处理器...")
        try:
            self.depth_processor = DepthProcessor()
            self.depth_enabled = True
        except Exception as e:
            print(f"警告: 深度处理器初始化失败: {e}")
            self.depth_enabled = False

        # 创建UI
        self.init_ui()

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / min(actual_fps, 60)))

        self.frame_count = 0
        self.last_time = time.time()
        self.fps = 0.0
        self.total_frames = 0

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # 信息标签
        info_text = f"1280x480 (左右各640x480) MJPG | 目标帧率: {self.TARGET_FPS} | 三画面同显"
        if self.depth_enabled:
            info_text += " | 深度: ON"
        info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)

        # 同时显示三个画面: 左、右、深度
        display_widget = QWidget()
        display_layout = QHBoxLayout(display_widget)

        # 左摄像头
        left_group = QGroupBox("左摄像头 (LEFT)")
        left_layout = QVBoxLayout()
        self.left_label = QLabel()
        self.left_label.setAlignment(Qt.AlignCenter)
        self.left_label.setMinimumSize(320, 240)
        self.left_label.setStyleSheet("border: 2px solid green;")
        left_layout.addWidget(self.left_label)
        left_group.setLayout(left_layout)
        display_layout.addWidget(left_group)

        # 右摄像头
        right_group = QGroupBox("右摄像头 (RIGHT)")
        right_layout = QVBoxLayout()
        self.right_label = QLabel()
        self.right_label.setAlignment(Qt.AlignCenter)
        self.right_label.setMinimumSize(320, 240)
        self.right_label.setStyleSheet("border: 2px solid red;")
        right_layout.addWidget(self.right_label)
        right_group.setLayout(right_layout)
        display_layout.addWidget(right_group)

        # 深度图
        if self.depth_enabled:
            depth_group = QGroupBox("深度图 (Depth)")
            depth_layout = QVBoxLayout()
            self.depth_label = QLabel()
            self.depth_label.setAlignment(Qt.AlignCenter)
            self.depth_label.setMinimumSize(320, 240)
            self.depth_label.setStyleSheet("border: 2px solid purple;")
            depth_layout.addWidget(self.depth_label)
            depth_group.setLayout(depth_layout)
            display_layout.addWidget(depth_group)

        main_layout.addWidget(display_widget)

        # 状态栏
        self.status_label = QLabel("等待帧...")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.status_label.setText("错误: 无法读取帧")
            return

        self.frame_count += 1
        self.total_frames += 1

        current_time = time.time()
        elapsed = current_time - self.last_time
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_time = current_time

        # 分割左右画面
        mid = self.actual_width // 2
        if mid * 2 == self.actual_width and self.actual_width > self.actual_height:
            right_frame = frame[:, :mid]
            left_frame = frame[:, mid:]
        else:
            left_frame = frame
            right_frame = frame

        # 转换并显示原始图像
        left_rgb = cv2.cvtColor(left_frame, cv2.COLOR_BGR2RGB)
        right_rgb = cv2.cvtColor(right_frame, cv2.COLOR_BGR2RGB)

        self.left_label.setPixmap(QPixmap.fromImage(self.to_qimage(left_rgb)))
        self.right_label.setPixmap(QPixmap.fromImage(self.to_qimage(right_rgb)))

        # 深度处理
        if self.depth_enabled:
            result = self.depth_processor.process(left_frame, right_frame)

            # 显示深度图
            self.depth_label.setPixmap(QPixmap.fromImage(self.to_qimage(result['depth_display'])))

            # 获取深度统计
            stats = self.depth_processor.get_depth_stats(result['depth'])
            depth_info = f"深度: 均值={stats['mean']:.0f}mm 范围=[{stats['min']:.0f}, {stats['max']:.0f}]mm"
        else:
            depth_info = ""

        left_h, left_w = left_rgb.shape[:2]
        right_h, right_w = right_rgb.shape[:2]

        self.status_label.setText(
            f"FPS: {self.fps:.1f} | "
            f"左: {left_w}x{left_h} | "
            f"右: {right_w}x{right_h} | "
            f"{depth_info}"
        )

    def to_qimage(self, rgb):
        h, w = rgb.shape[:2]
        return QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888)

    def closeEvent(self, event):
        self.timer.stop()
        self.cap.release()
        print(f"\n已关闭，共捕获 {self.total_frames} 帧")
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = CameraViewer()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
