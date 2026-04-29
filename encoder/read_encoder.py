#!/usr/bin/env python3
"""
JY-ME01 角度编码器读取脚本
连接方式: COM3, 波特率 9600
输出频率: 5Hz

使用ASCII模式读取角度
"""

import serial
import time
import sys

# 串口配置
PORT = 'COM3'
BAUDRATE = 9600

def log(msg):
    print(msg, flush=True)

def main():
    import sys
    sys.stdout.reconfigure(line_buffering=True)

    log(f"正在连接 {PORT} @ {BAUDRATE} baud...")
    log("按 Ctrl+C 退出\n")
    sys.stdout.flush()

    try:
        ser = serial.Serial(
            port=PORT,
            baudrate=BAUDRATE,
            timeout=0.5
        )
        log(f"串口已打开: {ser.portstr}")

        # 检查连接
        ser.write(b'AT\r\n')
        time.sleep(0.2)
        response = ser.read(ser.in_waiting).decode('ascii', errors='ignore')
        if 'OK' not in response:
            log("警告: AT命令未得到OK回复，尝试继续...")
        log("连接成功!\n")

        # 设置5Hz输出 (PRATE=200, 单位ms)
        log("设置回传速率: 5Hz (PRATE=200)")
        ser.write(b'AT+PRATE=200\r\n')
        time.sleep(0.2)
        ser.read(ser.in_waiting)  # 清空回复

        # 清空缓冲区
        time.sleep(0.3)
        ser.read(ser.in_waiting)

        log("\n--- 角度输出 (5Hz) ---\n")

        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                line = data.decode('ascii', errors='ignore').strip()
                if line.startswith('Angle:'):
                    try:
                        angle = float(line[6:])
                        timestamp = time.strftime("%H:%M:%S")
                        log(f"[{timestamp}] 角度: {angle:.2f}°")
                    except ValueError:
                        pass  # 忽略解析失败的行

    except serial.SerialException as e:
        log(f"串口错误: {e}")
    except KeyboardInterrupt:
        log("\n\n已停止")
    finally:
        if 'ser' in locals() and ser.is_open:
            # 恢复单次回传
            ser.write(b'AT+PRATE=0\r\n')
            time.sleep(0.1)
            ser.close()
            log("串口已关闭")

if __name__ == '__main__':
    main()
