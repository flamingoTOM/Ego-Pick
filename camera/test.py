#!/usr/bin/env python3
"""
深度处理测试脚本
对 /stereo 目录下的图像进行深度处理，输出三张深度图并进行自检
"""

import os
import cv2
import numpy as np
from depth_process import DepthProcessor


def self_check(depth, disparity_norm, depth_display):
    """自检：验证深度图是否符合要求"""
    checks = []

    # 检查1: 深度图是否有有效像素
    valid_mask = (depth > 0) & np.isfinite(depth)
    valid_ratio = valid_mask.sum() / depth.size
    checks.append(("有效深度像素比例", valid_ratio > 0.1, f"{valid_ratio*100:.1f}%"))

    # 检查2: 深度值范围是否合理（0.05m ~ 10m）
    if valid_mask.any():
        d_min = depth[valid_mask].min() * 1000  # mm
        d_max = depth[valid_mask].max() * 1000  # mm
        # 过滤掉超过10m的异常值
        reasonable_mask = (depth < 10) & valid_mask
        if reasonable_mask.any():
            d_min_ok = depth[reasonable_mask].min() * 1000
            d_max_ok = depth[reasonable_mask].max() * 1000
            checks.append(("深度范围合理", 50 < d_min_ok < 10000 and d_max_ok < 10000, f"{d_min_ok:.0f}~{d_max_ok:.0f}mm"))
        else:
            checks.append(("深度范围合理", False, f"{d_min:.0f}~{d_max:.0f}mm (全部异常)"))

    # 检查3: 视差图是否有对比度
    if disparity_norm.max() > disparity_norm.min():
        checks.append(("视差图有对比度", True, f"min={disparity_norm.min()}, max={disparity_norm.max()}"))
    else:
        checks.append(("视差图有对比度", False, "全黑/全白"))

    # 检查4: 深度显示图不是全黑
    checks.append(("深度显示图非全黑", depth_display.max() > 0, f"max={depth_display.max()}"))

    # 检查5: 基线距离是否合理（10~100mm）
    T = processor.calib['T']
    baseline = np.linalg.norm(T)
    checks.append(("基线距离合理", 10 < baseline < 100, f"{baseline:.1f}mm"))

    return checks


# 目录设置
CAMERA_DIR = os.path.dirname(os.path.abspath(__file__))
STEREO_DIR = os.path.join(CAMERA_DIR, "stereo")
LEFT_DIR = os.path.join(STEREO_DIR, "left")
RIGHT_DIR = os.path.join(STEREO_DIR, "right")

print("=" * 50)
print("深度处理自检测试")
print("=" * 50)

# 初始化深度处理器
print("\n初始化深度处理器...")
processor = DepthProcessor()

# 获取stereo目录下的图像
left_files = sorted([f for f in os.listdir(LEFT_DIR) if f.endswith(('.png', '.jpg'))])
right_files = sorted([f for f in os.listdir(RIGHT_DIR) if f.endswith(('.png', '.jpg'))])

# 配对
pairs = []
for lf in left_files:
    # 适配 L1.png -> R1.png 格式
    base = lf.replace('L', '').replace('.png', '').replace('.jpg', '')
    rf = 'R' + base + '.png'
    if rf in right_files:
        pairs.append((lf, rf))

print(f"找到 {len(pairs)} 对图像")

if len(pairs) < 3:
    print(f"错误: 需要至少3对图像，当前只有 {len(pairs)} 对")
    print(f"请先运行 capture_stereo.py 采集图像")
    exit(1)

# 取前三对进行处理
results = []
for i, (lf, rf) in enumerate(pairs[:3]):
    print(f"\n处理第 {i+1}/3 对: {lf}, {rf}")

    # 读取图像
    left_img = cv2.imread(os.path.join(LEFT_DIR, lf))
    right_img = cv2.imread(os.path.join(RIGHT_DIR, rf))

    if left_img is None or right_img is None:
        print(f"  错误: 无法读取图像")
        continue

    # 深度处理
    result = processor.process(left_img, right_img)

    # 自检
    checks = self_check(
        result['depth'],
        result['disparity_norm'],
        result['depth_display']
    )

    # 保存结果
    output_dir = os.path.join(STEREO_DIR, f"output_{i+1}")
    os.makedirs(output_dir, exist_ok=True)

    cv2.imwrite(os.path.join(output_dir, "disparity.png"), result['disparity_norm'])
    cv2.imwrite(os.path.join(output_dir, "depth_raw.png"), result['depth_display'])
    cv2.imwrite(os.path.join(output_dir, "depth_color.png"), result['depth_display'])

    # 左矫正图
    cv2.imwrite(os.path.join(output_dir, "left_rectified.png"), result['left_rectified'])
    cv2.imwrite(os.path.join(output_dir, "right_rectified.png"), result['right_rectified'])

    results.append({
        'pair': (lf, rf),
        'checks': checks,
        'output_dir': output_dir
    })

# 输出自检结果
print("\n" + "=" * 50)
print("自检结果")
print("=" * 50)

all_passed = True
for i, r in enumerate(results):
    print(f"\n【第 {i+1} 对】{r['pair'][0]}")
    for name, passed, detail in r['checks']:
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}: {detail}")
        if not passed:
            all_passed = False

# 总结
print("\n" + "=" * 50)
if all_passed:
    print("[PASS] All self-checks passed! Depth processing is normal")
    print("=" * 50)
else:
    print("[FAIL] Some self-checks failed, please check configuration")
    print("=" * 50)

# 输出路径
print("\n输出目录:")
for i, r in enumerate(results):
    print(f"  第{i+1}对: {r['output_dir']}")
