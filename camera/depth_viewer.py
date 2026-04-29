#!/usr/bin/env python3
"""
双目深度实时显示
基于SGBM算法，实时显示左相机、右相机和深度图
直接使用标定文件里的参数
"""

import cv2
import numpy as np
import time
import math
import os

# 标定参数来自 stereo_calibration.yaml
CALIB_FILE = os.path.join(os.path.dirname(__file__), "stereo_calibration.yaml")


def load_calibration(filename):
    """加载标定参数"""
    fs = cv2.FileStorage(filename, cv2.FILE_STORAGE_READ)
    calib = {
        'M1': fs.getNode('M1').mat(),
        'D1': fs.getNode('D1').mat(),
        'M2': fs.getNode('M2').mat(),
        'D2': fs.getNode('D2').mat(),
        'R': fs.getNode('R').mat(),
        'T': fs.getNode('T').mat(),
        'R1': fs.getNode('R1').mat(),
        'R2': fs.getNode('R2').mat(),
        'P1': fs.getNode('P1').mat(),
        'P2': fs.getNode('P2').mat(),
        'Q': fs.getNode('Q').mat(),
    }
    fs.release()
    return calib


# 加载标定参数
calib = load_calibration(CALIB_FILE)
print(f"基线距离: {np.linalg.norm(calib['T'])*1000:.1f}mm")

# 图像尺寸
WIDTH = 640
HEIGHT = 480
SIZE = (WIDTH, HEIGHT)

# 校正查找映射表（使用标定文件里的R1/R2/P1/P2）
left_map1, left_map2 = cv2.initUndistortRectifyMap(
    calib['M1'], calib['D1'], calib['R1'], calib['P1'], SIZE, cv2.CV_16SC2
)
right_map1, right_map2 = cv2.initUndistortRectifyMap(
    calib['M2'], calib['D2'], calib['R2'], calib['P2'], SIZE, cv2.CV_16SC2
)


def create_stereo_matcher():
    """创建SGBM匹配器（小基线优化参数）"""
    stereo = cv2.StereoSGBM_create(
        minDisparity=0,
        numDisparities=128,
        blockSize=7,
        P1=8 * 3 * 7**2,
        P2=32 * 3 * 7**2,
        disp12MaxDiff=1,        # 左右一致性检查
        preFilterCap=1,
        uniquenessRatio=15,
        speckleWindowSize=100,
        speckleRange=2,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY  # 小基线用3WAY更快更稳定
    )
    return stereo


def process_depth(disparity, Q):
    """处理视差图，生成深度相关信息"""
    # 先将视差转为真实视差（除以16）
    disparity_f = disparity.astype(np.float32) / 16.0

    # 归一化视差图（灰度）
    disp_norm = cv2.normalize(disparity_f, None, alpha=0, beta=255,
                              norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # 深度伪彩色图
    disp_color = cv2.normalize(disparity_f, None, alpha=0, beta=255,
                              norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    disp_color = cv2.applyColorMap(disp_color, cv2.COLORMAP_JET)

    # 计算三维坐标 (m)
    # reprojectImageTo3D 输入已经是真实视差，输出Z是米（因为标定文件里T单位是米）
    threeD = cv2.reprojectImageTo3D(disparity_f, Q, handleMissingValues=True)

    return disp_norm, disp_color, threeD


def onmouse_pick_points(event, x, y, flags, param):
    """鼠标点击获取三维坐标"""
    if event == cv2.EVENT_LBUTTONDOWN:
        threeD = param
        z = threeD[y][x][2]
        # 检查是否是有效值
        if np.isfinite(z):
            print(f'\n像素坐标 x = {x}, y = {y}')
            print(f"世界坐标 xyz (m): {threeD[y][x][0]:.3f}, {threeD[y][x][1]:.3f}, {z:.3f}")
            # 计算到原点距离
            distance = math.sqrt(threeD[y][x][0]**2 + threeD[y][x][1]**2 + z**2)
            print(f"距离原点: {distance:.3f} m")
        else:
            print(f'\n像素坐标 x = {x}, y = {y} - 无效深度')


def main():
    # 打开摄像头
    cap = cv2.VideoCapture(0, cv2.CAP_MSMF)
    if not cap.isOpened():
        print("错误: 无法打开摄像头")
        return

    # 设置分辨率 (1280x480 双目拼接)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"摄像头: {actual_w}x{actual_h}")

    # 创建SGBM匹配器
    stereo = create_stereo_matcher()

    # 创建窗口
    cv2.namedWindow("depth_color", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("depth_gray", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("left", cv2.WINDOW_AUTOSIZE)
    cv2.namedWindow("stereo_rectified", cv2.WINDOW_AUTOSIZE)

    fps = 0.0
    frame_count = 0

    print("\n按 q 退出，按鼠标左键点击深度图查看三维坐标")

    while True:
        t1 = time.time()

        ret, frame = cap.read()
        if not ret:
            print("错误: 无法读取帧")
            break

        # 分割左右画面
        if actual_w == 1280:
            left_frame = frame[0:480, 0:640]
            right_frame = frame[0:480, 640:1280]
        else:
            mid = actual_w // 2
            left_frame = frame[:, :mid]
            right_frame = frame[:, mid:]

        # 先对彩色图做立体校正（保留彩色纹理）
        imgL_rectified_color = cv2.remap(left_frame, left_map1, left_map2, cv2.INTER_LINEAR)
        imgR_rectified_color = cv2.remap(right_frame, right_map1, right_map2, cv2.INTER_LINEAR)

        # 再转灰度图给SGBM
        imgL_rectified = cv2.cvtColor(imgL_rectified_color, cv2.COLOR_BGR2GRAY)
        imgR_rectified = cv2.cvtColor(imgR_rectified_color, cv2.COLOR_BGR2GRAY)

        # 计算视差
        disparity = stereo.compute(imgL_rectified, imgR_rectified)

        # 校正后的左右图像拼接（用于立体显示）
        stereo_rectified = np.hstack((imgL_rectified_color, imgR_rectified_color))

        # 处理深度信息
        disp_norm, disp_color, threeD = process_depth(disparity, calib['Q'])

        # 设置鼠标回调
        cv2.setMouseCallback("depth_color", onmouse_pick_points, threeD)

        # 计算帧率
        fps = (fps + (1.0 / (time.time() - t1))) / 2
        frame_count += 1

        # 显示图像
        cv2.putText(disp_color, f"fps={fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("depth_color", disp_color)
        cv2.imshow("depth_gray", disp_norm)
        cv2.imshow("left", left_frame)
        cv2.imshow("stereo_rectified", stereo_rectified)

        if cv2.waitKey(1) & 0xff == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n共处理 {frame_count} 帧")


if __name__ == '__main__':
    main()
