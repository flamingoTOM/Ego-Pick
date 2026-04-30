#!/usr/bin/env python3
"""
Encoder Pick Distance 可视化界面
订阅 /encoder/pick_distance 和 /encoder/angle 话题并实时绘图
"""

import sys
import threading
from collections import deque

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.gridspec import GridSpec


class EncoderPlotWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Encoder Monitor")
        self.setGeometry(100, 100, 1000, 500)

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

        self.figure = Figure(figsize=(10, 3.5))
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

    def update_plot(self, distance, angle):
        self.time_data.append(self.time_counter)
        self.angle_data.append(angle)
        self.distance_data.append(distance)
        self.time_counter += 1

        self.line_angle.set_data(list(self.time_data), list(self.angle_data))
        self.line_distance.set_data(list(self.time_data), list(self.distance_data))

        tmax = max(self.time_data) if self.time_data else 1
        self.ax_angle.set_xlim(0, tmax)
        self.ax_distance.set_xlim(0, tmax)

        self.angle_label.setText(f"Angle: {angle:.1f} °")
        self.distance_label.setText(f"Distance: {distance:.1f} mm")
        self.status_label.setText("Status: Connected")

        self.canvas.draw()


class EncoderSubscriberNode(Node):
    def __init__(self):
        super().__init__('encoder_subscriber_node')
        self._lock = threading.Lock()
        self._latest_angle = 0.0
        self._new_distance = None

        self.create_subscription(Float64, 'encoder/angle', self.angle_callback, 10)
        self.create_subscription(Float64, 'encoder/pick_distance', self.distance_callback, 10)

    def angle_callback(self, msg):
        with self._lock:
            self._latest_angle = msg.data

    def distance_callback(self, msg):
        with self._lock:
            self._new_distance = (msg.data, self._latest_angle)

    def pop_data(self):
        """返回最新的一对 (distance, angle)，仅读取一次"""
        with self._lock:
            data = self._new_distance
            self._new_distance = None
            return data


def main():
    rclpy.init()

    app = QApplication(sys.argv)
    plot_window = EncoderPlotWindow()
    node = EncoderSubscriberNode()

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    def update_timer():
        result = node.pop_data()
        if result is not None:
            distance, angle = result
            plot_window.update_plot(distance, angle)

    timer = QTimer()
    timer.timeout.connect(update_timer)
    timer.start(50)

    plot_window.show()

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
