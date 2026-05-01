#!/usr/bin/env python3
"""
JY-ME01 角度编码器 ROS2 驱动节点
连接方式: USB转TTL串口, 波特率 9600
输出频率: 5Hz (可配置)

发布话题: /encoder/angle (std_msgs/Float64)
           /encoder/pick_distance (std_msgs/Float64)
"""

import serial
import time
import math
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64


class EncoderDriverNode(Node):
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, rate=5.0):
        super().__init__('encoder_driver_node')

        self.declare_parameter('port', port)
        self.declare_parameter('baudrate', baudrate)
        self.declare_parameter('rate', rate)

        self.port = self.get_parameter('port').value
        self.baudrate = self.get_parameter('baudrate').value
        self.rate = self.get_parameter('rate').value

        self.angle = 0.0
        self.connected = False

        self.angle_pub = self.create_publisher(Float64, 'encoder/angle', 10)
        self.distance_pub = self.create_publisher(Float64, 'encoder/pick_distance', 10)

        self.get_logger().info(f'Encoder driver node starting...')
        self.get_logger().info(f'Port: {self.port}, Baudrate: {self.baudrate}, Rate: {self.rate}Hz')

        self.driver_thread = threading.Thread(target=self.driver_loop, daemon=True)
        self.driver_thread.start()

    def driver_loop(self):
        try:
            ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.5
            )
            self.connected = True
            self.get_logger().info(f'\033[32mSerial port opened: {self.port}\033[0m')

            ser.write(b'AT\r\n')
            time.sleep(0.2)
            response = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
            if 'OK' not in response:
                self.get_logger().warn('AT command did not get OK response, continuing...')
            self.get_logger().info('Encoder connected successfully')

            prate_ms = int(1000 / self.rate)
            self.get_logger().info(f'Setting output rate: {self.rate}Hz (PRATE={prate_ms})')
            ser.write(f'AT+PRATE={prate_ms}\r\n'.encode())
            time.sleep(0.2)
            ser.read(ser.in_waiting)

            time.sleep(0.3)
            ser.read(ser.in_waiting)

            last_publish_time = time.time()
            buffer = ''

            while rclpy.ok() and self.connected:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    buffer += data.decode('ascii', errors='ignore')

                    lines = buffer.split('\n')
                    buffer = lines[-1]

                    for line in lines[:-1]:
                        line = line.strip()
                        if line.startswith('Angle:'):
                            try:
                                self.angle = float(line[6:])
                                self.get_logger().debug(f'Angle: {self.angle:.2f}')
                            except ValueError:
                                pass

                current_time = time.time()
                if current_time - last_publish_time >= 1.0 / self.rate:
                    self.publish_angle()
                    last_publish_time = current_time

        except serial.SerialException as e:
            self.get_logger().error(f'Serial error: {e}')
        except Exception as e:
            self.get_logger().error(f'Driver error: {e}')
        finally:
            if 'ser' in locals() and ser.is_open:
                try:
                    ser.write(b'AT+PRATE=0\r\n')
                    time.sleep(0.1)
                    ser.close()
                except:
                    pass
            self.get_logger().info('Serial port closed')

    def publish_angle(self):
        angle_msg = Float64()
        angle_msg.data = self.angle
        self.angle_pub.publish(angle_msg)

        theta_rad = math.radians(self.angle)
        term = 14 - 30.5 * math.sin(theta_rad)
        pick_distance = 30.5 * math.cos(theta_rad) - 34.7 + math.sqrt(3364 - term ** 2)

        distance_msg = Float64()
        distance_msg.data = pick_distance
        self.distance_pub.publish(distance_msg)


def main():
    rclpy.init()
    node = EncoderDriverNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
