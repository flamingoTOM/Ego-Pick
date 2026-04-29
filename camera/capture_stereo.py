#!/usr/bin/env python3
"""
双目立体图像采集
每隔3秒采集一对左右图像，保存到 stereo/left 和 stereo/right
"""

import os
import cv2
import time

# 目录设置
CAMERA_DIR = os.path.dirname(os.path.abspath(__file__))
LEFT_DIR = os.path.join(CAMERA_DIR, "stereo", "left")
RIGHT_DIR = os.path.join(CAMERA_DIR, "stereo", "right")

# 创建目录
os.makedirs(LEFT_DIR, exist_ok=True)
os.makedirs(RIGHT_DIR, exist_ok=True)

# 摄像头设置
FRAME_WIDTH = 1280
FRAME_HEIGHT = 480
TARGET_FPS = 30


def main():
    # 打开摄像头
    cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return

    # 强制MJPG格式
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"摄像头: {actual_w}x{actual_h} @ {actual_fps:.0f} FPS")
    print(f"保存目录: {os.path.join(CAMERA_DIR, 'stereo')}")
    print(f"采集间隔: 3秒")
    print(f"按 Ctrl+C 停止\n")

    count = 0
    last_capture = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("错误: 无法读取帧")
                break

            # 每隔3秒采集一次
            now = time.time()
            if now - last_capture >= 3.0:
                # 分割左右画面
                mid = actual_w // 2
                left_frame = frame[:, mid:]
                right_frame = frame[:, :mid]

                # 生成文件名（使用时间戳）
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                left_path = os.path.join(LEFT_DIR, f"{timestamp}_L.png")
                right_path = os.path.join(RIGHT_DIR, f"{timestamp}_R.png")

                # 保存
                cv2.imwrite(left_path, left_frame)
                cv2.imwrite(right_path, right_frame)

                count += 1
                print(f"[{count:03d}] 保存: {timestamp}_L.png, {timestamp}_R.png")
                last_capture = now

    except KeyboardInterrupt:
        print(f"\n已停止，共采集 {count} 对图像")

    cap.release()


if __name__ == '__main__':
    main()
