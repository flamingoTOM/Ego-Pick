#!/usr/bin/env python3
"""
深度估计模块
使用SGBM算法从立体图像计算深度图
"""

import cv2
import numpy as np
import os

# 配置
CAMERA_DIR = os.path.dirname(os.path.abspath(__file__))
CALIB_FILE = os.path.join(CAMERA_DIR, "stereo_calibration.yaml")


def load_calibration(filename):
    """加载标定参数 - 使用OpenCV读取YAML"""
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
        'image_width': int(fs.getNode('image_width').real()),
        'image_height': int(fs.getNode('image_height').real()),
    }

    fs.release()
    return calib


def stereo_rectify(calib, width, height):
    """计算校正映射表"""
    left_map1, left_map2 = cv2.initUndistortRectifyMap(
        calib['M1'], calib['D1'], calib['R1'], calib['P1'],
        (width, height), cv2.CV_16SC2
    )
    right_map1, right_map2 = cv2.initUndistortRectifyMap(
        calib['M2'], calib['D2'], calib['R2'], calib['P2'],
        (width, height), cv2.CV_16SC2
    )
    return left_map1, left_map2, right_map1, right_map2


def preprocess(gray_left, gray_right):
    """图像预处理"""
    # 小核高斯模糊去噪（保留边缘纹理）
    gray_left = cv2.GaussianBlur(gray_left, (3, 3), 0)
    gray_right = cv2.GaussianBlur(gray_right, (3, 3), 0)

    # CLAHE增强对比度（避免全局过曝）
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray_left = clahe.apply(gray_left)
    gray_right = clahe.apply(gray_right)

    return gray_left, gray_right


def create_sgbm():
    """创建SGBM算法"""
    sgbm = cv2.StereoSGBM_create(
        minDisparity=0,
        numDisparities=128,      # 16的倍数，视差范围
        blockSize=7,             # 匹配块大小，奇数，更稳定
        P1=8 * 3 * 7**2,        # 平滑度参数P1
        P2=32 * 3 * 7**2,        # 平滑度参数P2
        disp12MaxDiff=1,         # 左右视差检查
        uniquenessRatio=15,       # 唯一性检查
        speckleWindowSize=100,   # 噪点过滤窗口
        speckleRange=2,          # 噪点范围
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )
    return sgbm


def compute_disparity(sgbm, gray_left, gray_right):
    """计算视差图"""
    disparity = sgbm.compute(gray_left, gray_right)
    return disparity


def postprocess_disparity(disparity):
    """视差图后处理"""
    # 先转为float32真实视差
    disparity_f = disparity.astype(np.float32) / 16.0

    # 掩码无效值（负数）
    valid_mask = disparity_f >= 0

    # 对有效视差做中值滤波（只处理有效区域）
    disparity_f_filtered = np.zeros_like(disparity_f)
    if valid_mask.any():
        # 临时将无效值设为中值再滤波
        median_val = np.median(disparity_f[valid_mask])
        disparity_f_temp = disparity_f.copy()
        disparity_f_temp[~valid_mask] = median_val
        disparity_f_filtered = cv2.medianBlur(disparity_f_temp, 5)
        # 恢复有效值
        disparity_f_filtered[valid_mask] = disparity_f[valid_mask]
    else:
        return np.zeros_like(disparity_f, dtype=np.uint8), disparity_f

    # 归一化到0-255用于显示
    disp_norm = np.zeros_like(disparity_f_filtered, dtype=np.uint8)
    if valid_mask.any():
        d_min = disparity_f_filtered[valid_mask].min()
        d_max = disparity_f_filtered[valid_mask].max()
        if d_max > d_min:
            disp_norm[valid_mask] = ((disparity_f_filtered[valid_mask] - d_min) * 255 / (d_max - d_min + 1e-6)).astype(np.uint8)
        else:
            disp_norm[valid_mask] = 128

    return disp_norm, disparity_f_filtered


def disparity_to_depth(disparity_f, Q, baseline_mm=15.15):
    """视差转深度"""
    # baseline_mm: 基线距离，单位毫米
    # 焦距（像素）
    f = Q[2, 3]

    # 裁剪视差避免零除（但不要太激进）
    disparity_f = np.clip(disparity_f, 0.1, None)

    # 计算深度: Z = f * B / disparity
    # f: 像素, B: 毫米 -> Z: 毫米
    # 转换为米: Z_m = Z_mm / 1000
    depth_mm = (f * baseline_mm) / disparity_f
    depth_m = depth_mm / 1000.0

    # 构建xyz（用于兼容）
    xyz = np.zeros((*disparity_f.shape, 3), dtype=np.float32)
    xyz[:, :, 2] = depth_m

    return depth_m, xyz

    return depth, xyz


class DepthProcessor:
    """深度处理器"""

    def __init__(self, calib_file=CALIB_FILE):
        # 加载标定参数
        self.calib = load_calibration(calib_file)
        self.image_width = self.calib['image_width']
        self.image_height = self.calib['image_height']

        # 实际图像尺寸（双目拼接后）
        self.actual_width = 640  # 实际处理的图像宽度
        self.actual_height = 480

        # 如果实际图像与标定图像宽度不同，需要缩放Q矩阵
        if self.actual_width != self.image_width:
            self.scale = self.actual_width / self.image_width
            # 调整Q矩阵参数
            self.Q = self.calib['Q'].copy()
            self.Q[0, 3] *= self.scale  # cx
            self.Q[1, 3] *= self.scale  # cy
            self.Q[2, 3] *= self.scale  # f
        else:
            self.Q = self.calib['Q']

        # 计算校正映射表（用于实际图像尺寸）
        self.left_map1, self.left_map2, self.right_map1, self.right_map2 = stereo_rectify(
            self.calib, self.actual_width, self.actual_height
        )

        # 创建SGBM
        self.sgbm = create_sgbm()

        print(f"深度处理器初始化完成")
        print(f"图像尺寸: {self.image_width}x{self.image_height}")
        baseline_m = np.linalg.norm(self.calib['T'])  # T向量单位是米
        print(f"基线距离: {baseline_m:.2f}m")

    def process(self, left_frame, right_frame):
        """
        处理左右图像，返回视差图和深度图
        """
        # 立体校正（去畸变+行对齐）
        left_rectified = cv2.remap(left_frame, self.left_map1, self.left_map2, cv2.INTER_LINEAR)
        right_rectified = cv2.remap(right_frame, self.right_map1, self.right_map2, cv2.INTER_LINEAR)

        # 转灰度图
        gray_left = cv2.cvtColor(left_rectified, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(right_rectified, cv2.COLOR_BGR2GRAY)

        # 预处理
        gray_left, gray_right = preprocess(gray_left, gray_right)

        # 计算视差
        disparity = compute_disparity(self.sgbm, gray_left, gray_right)

        # 视差后处理
        disp_norm, disparity_f = postprocess_disparity(disparity)

        # 视差转深度（使用缩放后的Q矩阵）
        baseline_mm = 15.15  # 相机基线，单位毫米
        depth, xyz = disparity_to_depth(disparity_f, self.Q, baseline_mm=baseline_mm)

        # 深度图归一化显示
        depth_display = self._normalize_depth_for_display(depth)

        return {
            'left_rectified': left_rectified,
            'right_rectified': right_rectified,
            'disparity_norm': disp_norm,
            'disparity_float': disparity_f,
            'depth': depth,
            'xyz': xyz,
            'depth_display': depth_display,
        }

    def _normalize_depth_for_display(self, depth):
        """深度图归一化用于显示"""
        depth_display = np.zeros_like(depth, dtype=np.uint8)
        valid_depth = (depth > 0) & np.isfinite(depth)
        if valid_depth.any():
            d_min = depth[valid_depth].min()
            d_max = depth[valid_depth].max()
            if d_max > d_min:
                depth_display[valid_depth] = ((depth[valid_depth] - d_min) * 255.0 / (d_max - d_min)).astype(np.uint8)
            else:
                depth_display[valid_depth] = 128
        return cv2.applyColorMap(depth_display, cv2.COLORMAP_JET)

    def get_depth_stats(self, depth):
        """获取深度统计信息"""
        valid_mask = depth > 0
        if valid_mask.any():
            return {
                'mean': depth[valid_mask].mean() * 1000,  # mm
                'min': depth[valid_mask].min() * 1000,
                'max': depth[valid_mask].max() * 1000,
            }
        return {'mean': 0, 'min': 0, 'max': 0}
