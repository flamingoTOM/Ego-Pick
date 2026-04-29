#!/usr/bin/env python3
"""
JY-ME01 角度编码器实时绘图脚本
连接方式: COM3, 波特率 9600
输出频率: 5Hz
"""

import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# 串口配置
PORT = 'COM3'
BAUDRATE = 9600
MAX_POINTS = 200  # 最多显示点数

class EncoderReader:
    def __init__(self):
        self.ser = None
        self.angles = deque(maxlen=MAX_POINTS)
        self.times = deque(maxlen=MAX_POINTS)
        self.start_time = None
        self.connected = False

    def connect(self):
        try:
            self.ser = serial.Serial(
                port=PORT,
                baudrate=BAUDRATE,
                timeout=0.5
            )
            time.sleep(0.1)

            # 检查连接
            self.ser.write(b'AT\r\n')
            time.sleep(0.2)
            response = self.ser.read(self.ser.in_waiting).decode('ascii', errors='ignore')
            if 'OK' not in response:
                print("警告: AT命令未得到OK回复，尝试继续...")

            # 设置5Hz输出 (PRATE=200, 单位ms)
            self.ser.write(b'AT+PRATE=200\r\n')
            time.sleep(0.2)
            self.ser.read(self.ser.in_waiting)  # 清空回复

            # 清空缓冲区
            time.sleep(0.3)
            self.ser.read(self.ser.in_waiting)

            self.start_time = time.time()
            self.connected = True
            print(f"连接成功! 端口: {self.ser.portstr}")
            return True

        except serial.SerialException as e:
            print(f"串口错误: {e}")
            return False

    def read_angle(self):
        if not self.connected:
            return None

        try:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                lines = data.decode('ascii', errors='ignore').split('\r\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('Angle:'):
                        try:
                            angle = float(line[6:])
                            elapsed = time.time() - self.start_time
                            self.angles.append(angle)
                            self.times.append(elapsed)
                            return angle
                        except ValueError:
                            continue
        except Exception as e:
            print(f"读取错误: {e}")
        return None

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.write(b'AT+PRATE=0\r\n')
            time.sleep(0.1)
            self.ser.close()
            print("串口已关闭")

def main():
    reader = EncoderReader()

    if not reader.connect():
        return

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(12, 6))
    line, = ax.plot([], [], 'b-', linewidth=1)
    ax.set_xlabel('时间 (秒)')
    ax.set_ylabel('角度 (°)')
    ax.set_title('JY-ME01 角度编码器实时数据')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 360)

    current_angle_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12,
                                  verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    def init():
        line.set_data([], [])
        current_angle_text.set_text('')
        return line, current_angle_text

    def animate(frame):
        angle = reader.read_angle()

        if len(reader.times) > 0:
            times_array = np.array(reader.times)
            angles_array = np.array(reader.angles)

            # 动态调整X轴范围
            if times_array[-1] > 40:
                ax.set_xlim(times_array[-1] - 40, times_array[-1])

            line.set_data(times_array, angles_array)

            if angle is not None:
                current_angle_text.set_text(f'当前角度: {angle:.2f}°\n时间: {times_array[-1]:.1f}s\n点数: {len(reader.angles)}')

        return line, current_angle_text

    print("按 Ctrl+C 退出绘图窗口")
    try:
        ani = animation.FuncAnimation(fig, animate, init_func=init, interval=50, blit=True, cache_frame_data=False)
        plt.show()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        reader.close()

if __name__ == '__main__':
    main()
