#!/usr/bin/env python3
"""
IMU 驱动节点 — 维特 JY-ME01 系列 (WitMotion)
串口读取原始协议 → 解析加速度/角速度/姿态角 → 发布 sensor_msgs/Imu
"""

import math
import struct
import threading

import numpy as np
import rclpy
import serial
from rclpy.node import Node
from sensor_msgs.msg import Imu


def hex_to_short(raw_data):
    return list(struct.unpack("hhhh", bytearray(raw_data)))


def check_sum(list_data, check_data):
    return sum(list_data) & 0xff == check_data


def get_quaternion_from_euler(roll, pitch, yaw):
    qx = math.sin(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) \
       - math.cos(roll / 2) * math.sin(pitch / 2) * math.sin(yaw / 2)
    qy = math.cos(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2) \
       + math.sin(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2)
    qz = math.cos(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2) \
       - math.sin(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2)
    qw = math.cos(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) \
       + math.sin(roll / 2) * math.sin(pitch / 2) * math.sin(yaw / 2)
    return [qx, qy, qz, qw]


class IMUDriverNode(Node):
    def __init__(self):
        super().__init__('imu_driver_node')

        self.declare_parameter('port', '/dev/ttyUSB0')
        self.declare_parameter('baudrate', 9600)
        port = self.get_parameter('port').value
        baudrate = self.get_parameter('baudrate').value

        self.imu_pub = self.create_publisher(Imu, 'imu/data_raw', 10)
        self.imu_msg = Imu()
        self.imu_msg.header.frame_id = 'imu_link'

        # 全局数据缓存
        self._buff = {}
        self._key = 0
        self.acceleration = [0.0, 0.0, 0.0]
        self.angularVelocity = [0.0, 0.0, 0.0]
        self.angle_degree = [0.0, 0.0, 0.0]

        self.get_logger().info(f'Opening IMU on {port} @ {baudrate}...')
        self.driver_thread = threading.Thread(
            target=self._driver_loop, args=(port, baudrate), daemon=True)
        self.driver_thread.start()

    def _driver_loop(self, port, baudrate):
        try:
            self._ser = serial.Serial(port=port, baudrate=baudrate, timeout=0.5)
            if not self._ser.is_open:
                self._ser.open()
            self.get_logger().info('Serial port opened successfully')
        except Exception as e:
            self.get_logger().error(f'Serial port opening failure: {e}')
            return

        while rclpy.ok():
            try:
                buff_count = self._ser.in_waiting
            except Exception:
                self.get_logger().error('IMU disconnected')
                return

            if buff_count > 0:
                buff_data = self._ser.read(buff_count)
                for i in range(buff_count):
                    tag = self._handle_serial_data(buff_data[i])
                    if tag:
                        self._publish_imu()

    def _handle_serial_data(self, raw_data):
        self._buff[self._key] = raw_data
        self._key += 1
        if self._buff[0] != 0x55:
            self._key = 0
            return False
        if self._key < 11:
            return False

        data_buff = list(self._buff.values())
        flag = False

        if self._buff[1] == 0x51:
            if check_sum(data_buff[0:10], data_buff[10]):
                self.acceleration = [
                    hex_to_short(data_buff[2:10])[i] / 32768.0 * 16 * 9.8
                    for i in range(3)
                ]
            else:
                self.get_logger().warn('0x51 Check failure')

        elif self._buff[1] == 0x52:
            if check_sum(data_buff[0:10], data_buff[10]):
                self.angularVelocity = [
                    hex_to_short(data_buff[2:10])[i] / 32768.0 * 2000
                    for i in range(3)
                ]
            else:
                self.get_logger().warn('0x52 Check failure')

        elif self._buff[1] == 0x53:
            if check_sum(data_buff[0:10], data_buff[10]):
                self.angle_degree = [
                    hex_to_short(data_buff[2:10])[i] / 32768.0 * 180
                    for i in range(3)
                ]
                flag = True
            else:
                self.get_logger().warn('0x53 Check failure')

        elif self._buff[1] == 0x54:
            if check_sum(data_buff[0:10], data_buff[10]):
                pass  # magnetometer data, not used
            else:
                self.get_logger().warn('0x54 Check failure')

        self._buff = {}
        self._key = 0
        return flag

    def _publish_imu(self):
        ax = self.acceleration[0]
        ay = self.acceleration[1]
        az = self.acceleration[2]

        gx = math.radians(self.angularVelocity[0])
        gy = math.radians(self.angularVelocity[1])
        gz = math.radians(self.angularVelocity[2])

        roll = math.radians(self.angle_degree[0])
        pitch = math.radians(self.angle_degree[1])
        yaw = math.radians(self.angle_degree[2])

        qua = get_quaternion_from_euler(roll, pitch, yaw)

        self.imu_msg.header.stamp = self.get_clock().now().to_msg()
        self.imu_msg.linear_acceleration.x = ax
        self.imu_msg.linear_acceleration.y = ay
        self.imu_msg.linear_acceleration.z = az
        self.imu_msg.angular_velocity.x = gx
        self.imu_msg.angular_velocity.y = gy
        self.imu_msg.angular_velocity.z = gz
        self.imu_msg.orientation.x = qua[0]
        self.imu_msg.orientation.y = qua[1]
        self.imu_msg.orientation.z = qua[2]
        self.imu_msg.orientation.w = qua[3]

        self.imu_pub.publish(self.imu_msg)


def main():
    rclpy.init()
    node = IMUDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
