# ROS2 Ego Data Collection System - Software Architecture Design

## 1. 系统概述 / System Overview

### 1.1 硬件配置 / Hardware Configuration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Jetson NX Compute Platform                        │
│                    (Ubuntu 22.04 + ROS2 Humble)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   Gripper 1   │           │   Gripper 2   │           │  Data Storage │
│   (Left)      │           │   (Right)     │           │   & Export   │
└───────────────┘           └───────────────┘           └───────────────┘
        │                           │                           ▲
        │                           │                           │
   ┌────┴────┐                ┌────┴────┐                ┌─────┴─────┐
   │ Sensor  │                │ Sensor  │                │  Export   │
   │ Suite 1 │                │ Suite 2 │                │  Node     │
   └─────────┘                └─────────┘                └───────────┘
```

**每个夹爪传感器套件 / Per Gripper Sensor Suite:**

| 传感器 | 数量 | 接口 | 数据类型 |
|--------|------|------|----------|
| 编码器 (Encoder) | 1 | USB2.0 | 角度值 (0-360°)，用于推导开合距离 |
| 双目相机 (Stereo Camera) | 1组(2目) | USB2.0 | 立体图像对 |
| 鱼眼镜头 (Fisheye) | 1 | USB2.0 | 广角图像 |
| IMU | 1 | USB2.0 | 9-DOF (加速度/角速度/磁力计) |

### 1.2 系统架构图 / System Architecture Diagram

```
                                ┌─────────────────────────────────────────────────────┐
                                │              RViz2 Visualization                     │
                                │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
                                │  │3D Pose  │ │Stereo    │ │Fisheye   │ │Gripper   │ │
                                │  │Display   │ │View      │ │View      │ │State     │ │
                                │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
                                └─────────────────────────────────────────────────────┘
                                                          ▲
                                                          │ visualization topics
                                  ┌─────────────────────────┼─────────────────────────┐
                                  │                         │                         │
                          ┌───────▼────────┐       ┌───────▼────────┐       ┌───────▼────────┐
                          │ Gripper 1      │       │ Gripper 2      │       │ Storage &     │
                          │ State Manager  │       │ State Manager  │       │ Export Node   │
                          └───────┬────────┘       └───────┬────────┘       └───────┬────────┘
                                  │                         │                         │
        ═══════════════════════════╪═════════════════════════╪═════════════════════════╪══════════════════════════
        ║                          │                         │                         │                    ║
        ║  ┌──────────────────────┐ │ │ ┌──────────────────────┐ │ │ ┌──────────────────────┐ │ ║
        ║  │   Encoder Node 1    │ │ │ │   Encoder Node 2    │ │ │ │   Data Recorder     │ │ ║
        ║  │   /gripper1/encoder │ │ │ │   /gripper2/encoder │ │ │ │   /data_recorder    │ │ ║
        ║  └──────────────────────┘ │ │ └──────────────────────┘ │ │ └──────────────────────┘ │ ║
        ║  ┌──────────────────────┐ │ │ ┌──────────────────────┐ │ │                         │ ║
        ║  │  IMU Node 1          │ │ │ │  IMU Node 2          │ │ │                         │ ║
        ║  │  /gripper1/imu_raw   │ │ │ │  /gripper2/imu_raw   │ │ │                         │ ║
        ║  └──────────────────────┘ │ │ └──────────────────────┘ │ │                         │ ║
        ║  ┌──────────────────────┐ │ │ ┌──────────────────────┐ │ │                         │ ║
        ║  │  Stereo Camera 1     │ │ │ │  Stereo Camera 2     │ │ │                         │ ║
        ║  │  /gripper1/stereo/*  │ │ │ │  /gripper2/stereo/*  │ │ │                         │ ║
        ║  └──────────────────────┘ │ │ └──────────────────────┘ │ │                         │ ║
        ║  ┌──────────────────────┐   │ │ ┌──────────────────────┐   │                         ║
        ║  │  Fisheye Camera 1    │   │ │ │  Fisheye Camera 2    │   │                         ║
        ║  │  /gripper1/fisheye/* │   │ │ │  /gripper2/fisheye/* │   │                         │ ║
        ║  └──────────────────────┘   │ │ └──────────────────────┘   │                         │ ║
        ║                            │ │                            │                         ║
        ═════════════════════════════╧═╪════════════════════════════╧═════════════════════════════════════
                                   │   │
                        ROS2 Topic Bus (DDS)
```

---

## 2. ROS2 节点架构 / ROS2 Node Architecture

### 2.1 节点列表 / Node List

| 节点名称 | 命名空间 | 功能描述 | 实时性 |
|----------|----------|----------|--------|
| `encoder_node` | `/gripper{1,2}` | 采集编码器数据 | Soft Real-time |
| `imu_node` | `/gripper{1,2}` | 采集IMU原始数据 | Hard Real-time |
| `stereo_camera_node` | `/gripper{1,2}` | 双目相机图像采集 | Soft Real-time |
| `fisheye_camera_node` | `/gripper{1,2}` | 鱼眼镜头图像采集 | Soft Real-time |
| `gripper_state_manager` | `/gripper{1,2}` | 融合传感器状态 | Soft Real-time |
| `pose_estimator` | `/gripper{1,2}` | 基于IMU的姿态估计 | Hard Real-time |
| `data_recorder` | `/export` | 数据录制与导出 | Background |
| `visualization_manager` | `/viz` | RViz可视化管理 | Soft Real-time |

### 2.2 节点详细架构 / Detailed Node Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Gripper 1 Subsystem                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  encoder_node   │    │     imu_node    │    │stereo_camera_node│        │
│  │                 │    │                 │    │                 │        │
│  │ - USB/UART读取  │    │ - I2C/SPI读取   │    │ - V4L2捕获      │        │
│  │ - 角度解析      │    │ - 9-DOF融合     │    │ - 立体校正      │        │
│  │ - 偏移校准      │    │ - 校准滤波      │    │ - 左右目同步    │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
│           │                     │                     │                   │
│           ▼                     ▼                     ▼                   │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                    gripper_state_manager                         │       │
│  │  - 传感器数据融合                                                 │       │
│  │  - 夹爪开合度计算                                                 │       │
│  │  - 状态机管理                                                     │       │
│  │  - /gripper1/state [ego_gripper/GripperState]                    │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                │                                             │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐       │
│  │                       pose_estimator                              │       │
│  │  - IMU姿态解算 (四元数/欧拉角)                                     │       │
│  │  - 位置积分 (速度→位置)                                            │       │
│  │  - 零速度更新 (ZUPT)                                              │       │
│  │  - /gripper1/pose [geometry_msgs/PoseStamped]                    │       │
│  │  - /gripper1/pose_with_covariance [geometry_msgs/PoseWithCov]    │       │
│  └─────────────────────────────────────────────────────────────────┘       │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 话题通信设计 / Topic Communication Design

### 3.1 话题列表 / Topic List

#### Gripper 1 Topics

| 话题名 | 消息类型 | 频率 | 方向 | 描述 |
|--------|----------|------|------|------|
| `/gripper1/encoder/raw` | `sensor_msgs/JointState` | 100Hz | Node→Bus | 原始编码器角度 |
| `/gripper1/encoder/filtered` | `sensor_msgs/JointState` | 100Hz | Node→Bus | 滤波后编码器角度 |
| `/gripper1/encoder/distance` | `std_msgs/Float32` | 100Hz | Node→Bus | 推导后的开合距离 |
| `/gripper1/imu/raw` | `sensor_msgs/Imu` | 200Hz | Node→Bus | IMU原始数据 |
| `/gripper1/imu/mag` | `sensor_msgs/MagneticField` | 50Hz | Node→Bus | 磁力计数据 |
| `/gripper1/stereo/left/image` | `sensor_msgs/Image` | 30Hz | Node→Bus | 左目图像 |
| `/gripper1/stereo/right/image` | `sensor_msgs/Image` | 30Hz | Node→Bus | 右目图像 |
| `/gripper1/stereo/left/camera_info` | `sensor_msgs/CameraInfo` | 30Hz | Node→Bus | 左目相机内参 |
| `/gripper1/stereo/right/camera_info` | `sensor_msgs/CameraInfo` | 30Hz | Node→Bus | 右目相机内参 |
| `/gripper1/fisheye/image` | `sensor_msgs/Image` | 30Hz | Node→Bus | 鱼眼图像 |
| `/gripper1/fisheye/camera_info` | `sensor_msgs/CameraInfo` | 30Hz | Node→Bus | 鱼眼相机内参 |
| `/gripper1/state` | `ego_gripper/GripperState` | 100Hz | Manager→Bus | 融合后夹爪状态(含开合距离) |
| `/gripper1/pose` | `geometry_msgs/PoseStamped` | 100Hz | Estimator→Bus | 夹爪空间位姿 |
| `/gripper1/twist` | `geometry_msgs/TwistStamped` | 100Hz | Estimator→Bus | 夹爪运动速度 |

#### Gripper 2 Topics

| 话题名 | 消息类型 | 频率 | 方向 | 描述 |
|--------|----------|------|------|------|
| `/gripper2/encoder/raw` | `sensor_msgs/JointState` | 100Hz | Node→Bus | 原始编码器角度 |
| `/gripper2/encoder/filtered` | `sensor_msgs/JointState` | 100Hz | Node→Bus | 滤波后编码器角度 |
| `/gripper2/encoder/distance` | `std_msgs/Float32` | 100Hz | Node→Bus | 推导后的开合距离 |
| `/gripper2/imu/raw` | `sensor_msgs/Imu` | 200Hz | Node→Bus | IMU原始数据 |
| `/gripper2/imu/mag` | `sensor_msgs/MagneticField` | 50Hz | Node→Bus | 磁力计数据 |
| `/gripper2/stereo/left/image` | `sensor_msgs/Image` | 30Hz | Node→Bus | 左目图像 |
| `/gripper2/stereo/right/image` | `sensor_msgs/Image` | 30Hz | Node→Bus | 右目图像 |
| `/gripper2/stereo/left/camera_info` | `sensor_msgs/CameraInfo` | 30Hz | Node→Bus | 左目相机内参 |
| `/gripper2/stereo/right/camera_info` | `sensor_msgs/CameraInfo` | 30Hz | Node→Bus | 右目相机内参 |
| `/gripper2/fisheye/image` | `sensor_msgs/Image` | 30Hz | Node→Bus | 鱼眼图像 |
| `/gripper2/fisheye/camera_info` | `sensor_msgs/CameraInfo` | 30Hz | Node→Bus | 鱼眼相机内参 |
| `/gripper2/state` | `ego_gripper/GripperState` | 100Hz | Manager→Bus | 融合后夹爪状态(含开合距离) |
| `/gripper2/pose` | `geometry_msgs/PoseStamped` | 100Hz | Estimator→Bus | 夹爪空间位姿 |
| `/gripper2/twist` | `geometry_msgs/TwistStamped` | 100Hz | Estimator→Bus | 夹爪运动速度 |

#### System Topics

| 话题名 | 消息类型 | 频率 | 方向 | 描述 |
|--------|----------|------|------|------|
| `/system/control/record` | `std_msgs/Bool` | Event | Bus→Node | 录制控制 |
| `/system/control/export` | `std_msgs/String` | Event | Bus→Node | 导出触发 |
| `/system/status/recording` | `std_msgs/Bool` | 1Hz | Recorder→Viz | 录制状态 |
| `/system/status/storage` | `diagnostic_msgs/DiagnosticStatus` | 1Hz | Recorder→Viz | 存储状态 |

### 3.2 自定义消息类型 / Custom Message Types

#### GripperState.msg

```yaml
# ego_gripper/GripperState.msg
std_msgs/Header header

uint8 GRIPPER_CLOSED = 0
uint8 GRIPPER_OPEN = 1
uint8 GRIPPER_MOVING = 2
uint8 gripper_status

uint8 gripper_id

float32 encoder_angle    # 编码器原始角度 (rad)
float32 open_distance    # 夹爪开合距离 (mm)，由编码器角度推导
float32 target_distance  # 目标开合距离 (mm)
float32 velocity         # 运动速度 (mm/s)

uint16 error_flags       # 错误标志位

bool is_calibrated      # 是否已校准
bool is_home             # 是否在原点
```

#### GripperControl.msg

```yaml
# ego_gripper/GripperControl.msg
std_msgs/Header header

uint8 CONTROL_POSITION = 0
uint8 CONTROL_VELOCITY = 1
uint8 CONTROL_TORQUE = 2
uint8 control_mode

uint8 gripper_id

float32 target           # 目标值 (角度/速度/扭矩)
float32 max_velocity     # 最大速度限制
float32 max_torque       # 最大扭矩限制

bool stop_flag           # 紧急停止
bool reset_flag          # 重置标志
```

---

## 4. 数据流图 / Data Flow Diagram

### 4.1 完整数据流

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW DIAGRAM                               │
└──────────────────────────────────────────────────────────────────────────────┘

[ENCODER] ──────► [ENCODER_NODE] ──────► ┐
                                          │
[IMU] ─────────► [IMU_NODE] ─────────────►┼─► [GRIPPER_STATE] ──► [VISUALIZATION]
                                          │       MANAGER              │
[STEREO] ─────► [STEREO_CAMERA_NODE] ────►┤                            │
                                          │                            ▼
[FISHEYE] ────► [FISHEYE_CAMERA_NODE] ──►┤                    ┌───────────────┐
                                          │                    │  RVIZ2        │
[IMU] ─────────► [POSE_ESTIMATOR] ──────►┴───────────────────►│  3D Display   │
                                                               │  + Image View │
                                                               └───────────────┘
                                                                     ▲
                                                                     │
                                         ┌───────────────────────────┘
                                         │
                                         ▼
                                  ┌───────────────┐
                                  │ DATA_RECORDER │
                                  │               │
                                  │ - ROSBAG     │
                                  │ - HDF5       │
                                  │ - Raw Files  │
                                  └───────────────┘
                                         │
                                         ▼
                                  ┌───────────────┐
                                  │ EXPORT_NODE   │
                                  │               │
                                  │ - CSV Export  │
                                  │ - Video Mux   │
                                  │ - Sync Merge  │
                                  └───────────────┘
```

### 4.2 实时数据流 (100Hz Control Loop)

```
                    ┌─────────────────────────────────────────────┐
                    │           100Hz Real-time Loop              │
                    └─────────────────────────────────────────────┘

    Time ─────────────────────────────────────────────────────────►

    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Encoder  │    │   IMU    │    │  State   │    │   Pose   │
    │  Read    │───►│  Read    │───►│  Fusion  │───►│ Estimate │
    │  (1ms)   │    │  (0.5ms) │    │  (2ms)   │    │  (3ms)   │
    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │  Publish     │
                                         │  (0.5ms)     │
                                         └──────────────┘
```

### 4.3 图像数据流 (30Hz)

```
┌─────────────────────────────────────────────────────────────────┐
│                     Image Pipeline (30Hz)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Stereo Camera]                                                 │
│       │                                                          │
│       ├──[LEFT]──► [Debayer] ─► [Rectify] ─► [Crop] ─► [Publish]│
│       │                                                         │
│       └──[RIGHT]► [Debayer] ─► [Rectify] ─► [Crop] ─► [Publish]│
│                                                                  │
│  [Fisheye Camera]                                                │
│       │                                                          │
│       └──► [Debayer] ─► [Undistort] ─► [FOV裁剪] ─► [Publish]  │
│                                                                  │
│  [Visualization]                                                 │
│       │                                                          │
│       ├──► [stereo_view] ──► /gripperX/stereo/visualization     │
│       │                                                          │
│       └──► [fisheye_view] ──► /gripperX/fisheye/visualization   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 节点功能职责 / Node Functional Responsibilities

### 5.1 传感器驱动节点 / Sensor Driver Nodes

#### encoder_node

```python
# 功能职责
- 与编码器通信 (USB2.0 HID)
- 解析角度数据 (分辨率: 12-bit / 4096 ticks per revolution)
- 角度 → 开合距离转换 (根据夹爪机械结构标定转换系数)
- 校准偏移量 (offset calibration)
- 低通滤波 (LPF cutoff: 50Hz)
- 发布原始角度和计算后的开合距离

# 角度-距离转换公式:
# open_distance = k * |encoder_angle - encoder_home| + offset
# 其中 k 为标定系数 (mm/rad)，需通过实验测定

# 输入: USB2.0 接口
# 输出: /gripperX/encoder/raw, /gripperX/encoder/filtered, /gripperX/encoder/distance
# 资源: CPU 5%, Memory 50MB
```

#### imu_node

```python
# 功能职责
- IMU寄存器配置 (200Hz采样率)
- 原始数据读取 (USB2.0 串口/CDC)
- 数据校准 (零偏校准、尺度因子校准)
- 异常值剔除 (阈值检测)

# 输入: 硬件接口 (I2C/SPI)
# 输出: /gripperX/imu/raw, /gripperX/imu/mag, /gripperX/imu/temp
# 资源: CPU 8%, Memory 30MB
```

#### stereo_camera_node

```python
# 功能职责
- 双目相机初始化 (V4L2 / GStreamer)
- 左右目图像同步采集
- Bayer到RGB转换
- 立体校正 (Stereo Rectification)
- 硬件时间戳同步
- 多线程图像获取

# 输入: USB3.0 / CSI接口
# 输出: /gripperX/stereo/left/image, /gripperX/stereo/right/image
# 参数: exposure, gain, white_balance, stereo_baseline
# 资源: CPU 25%, Memory 200MB
```

#### fisheye_camera_node

```python
# 功能职责
- 鱼眼镜头初始化
- 图像采集与预处理
- 鱼眼畸变校正 (OpenCV fisheye undistort)
- 感兴趣区域(ROI)提取
- 宽视场可视化

# 输入: USB3.0 / CSI接口
# 输出: /gripperX/fisheye/image, /gripperX/fisheye/camera_info
# 参数: distortion_k1-k4, fov
# 资源: CPU 15%, Memory 150MB
```

### 5.2 数据处理节点 / Data Processing Nodes

#### gripper_state_manager

```python
# 功能职责
- 多传感器数据融合
- 夹爪开合距离计算 (mm)，基于encoder角度转换
- 运动状态机 (OPEN/CLOSED/MOVING/ERROR)
- 异常检测与报警
- 服务提供 (get_state, reset, calibrate)
- 参数服务器管理

# 输入: /gripperX/encoder/distance, /gripperX/imu/raw
# 输出: /gripperX/state
# 服务: /gripperX/calibrate, /gripperX/reset, /gripperX/get_info
# 资源: CPU 10%, Memory 80MB
```

#### pose_estimator

```python
# 功能职责
- IMU姿态解算 (Madgwick / Mahony filter)
- 四元数 ↔ 欧拉角转换
- 位置积分 (速度积分→位置)
- 零速度更新 (ZUPT) 检测
- 协方差传播
- 长时间漂移补偿

# 算法选择:
#   - Madgwick: 计算量小，适合嵌入式
#   - Mahony: 精度更高，参数可调
#   - EKF: 可融合多传感器 (推荐)

# 输入: /gripperX/imu/raw, /gripperX/state
# 输出: /gripperX/pose, /gripperX/twist
# 资源: CPU 12%, Memory 60MB
```

### 5.3 可视化与存储节点 / Visualization & Storage Nodes

#### visualization_manager

```python
# 功能职责
- RViz面板管理
- 3D夹爪模型显示
- 位姿轨迹绘制
- 图像窗口管理
- 实时数据仪表盘
- 话题时间同步显示

# 子模块:
#   - pose_visualizer: 显示夹爪3D位姿
#   - image_viewer: 双目/鱼眼图像显示
#   - data_dashboard: 数值监控仪表
#   - trajectory_recorder: 轨迹记录

# 输入: 所有/gripperX/* 话题
# 资源: CPU 20%, Memory 300MB
```

#### data_recorder

```python
# 功能职责
- ROSBAG录制 (所有话题)
- HDF5结构化存储
- 图像压缩录制 (FFV1/LZ4)
- 录制状态管理
- 自动分段 (按时间/大小)
- 磁盘空间监控

# 存储格式:
#   - ROSBAG: 原生ROS消息，适合回放
#   - HDF5: 结构化数据，适合分析
#   - MP4: 压缩视频，独立存储

# 输入: 所有/gripperX/* 话题, /system/control/record
# 输出: /system/status/recording, /system/status/storage
# 资源: CPU 30%, Memory 500MB (buffer)
```

#### export_node

```python
# 功能职责
- 数据格式转换 (ROS2 → CSV/JSON)
- 视频合成 (左右目/鱼眼合并)
- 时间戳同步对齐
- 元数据生成
- 数据完整性校验

# 输出格式:
#   - EgoState.json: 所有状态数据
#   - trajectory.csv: 位姿轨迹
#   - video/: 合成视频

# 服务: /export/start, /export/cancel, /export/status
```

---

## 6. 技术选型 / Technology Stack

### 6.1 核心框架

| 组件 | 选择 | 版本 | 说明 |
|------|------|------|------|
| ROS2 Distribution | Humble Hawksbill | 22.04 | 长期支持版 |
| DDS Implementation | CycloneDDS | Latest | Jetson优化 |
| Build System | colcon | 0.12+ | ROS2构建工具 |
| Package Manager | apt | 22.04 | 系统包管理 |

### 6.2 传感器驱动

| 传感器 | 驱动方案 | 库 | 说明 |
|--------|----------|-----|------|
| 编码器 | USB HID / UART | hidapi, pyserial | 视编码器型号 |
| IMU | I2C/SPI | rt_imu_ros2, imu_tools | MPU9250/BMI088 |
| 双目相机 | USB3.0 | libuvc, gscam2 | 推荐IDS/FLIR |
| 鱼眼相机 | USB3.0/CSI | v4l2_camera | 推荐Basler/IDS |

### 6.3 可视化库

| 用途 | 库 | 说明 |
|------|-----|------|
| 3D可视化 | rviz2 + rviz_visual_tools | RViz原生支持 |
| 图像显示 | image_view, rqt_image_view | ROS2原生 |
| 仪表盘 | rqt_multiplot, rqt_plot | 数据绘图 |
| 自定义面板 | rviz_python_panel | Python扩展 |

#### Qt自定义可视化（推荐）

Qt可视化布局：
```
┌─────────────────────────────────────────────────────────────┐
│                    Qt Application Window                    │
├───────────────┬───────────────┬───────────────────────────┤
│  Gripper1 RGB │ Gripper2 RGB │                           │
│    (Left)    │    (Left)    │                           │
├───────────────┼───────────────┤                           │
│ Gripper1 RGB  │ Gripper2 RGB │                           │
│   (Right)     │   (Right)    │                           │
├───────────────┼───────────────┼───────────────────────────┤
│Gripper1 Fisheye│Gripper2 Fisheye│                       │
│   (Left)      │    (Left)     │     3D Motion View     │
├───────────────┼───────────────┤      (Combined)         │
│Gripper1 Fisheye│Gripper2 Fisheye│                       │
│   (Right)     │   (Right)     │                       │
└───────────────┴───────────────┴───────────────────────────┘
```

Qt可视化伪代码：
```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from geometry_msgs.msg import PoseStamped
from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QLabel
from PyQt5.QtCore import QTimer
from cv_bridge import CvBridge

class GripperVisualizer(Node):
    def __init__(self):
        super().__init__('gripper_visualizer')

        self.bridge = CvBridge()

        # ========== 订阅话题 ==========
        # RGB图像
        self.create_subscription(Image,
            '/gripper1/stereo/left/image', self.cb_g1_rgb_l, 10)
        self.create_subscription(Image,
            '/gripper1/stereo/right/image', self.cb_g1_rgb_r, 10)
        self.create_subscription(Image,
            '/gripper2/stereo/left/image', self.cb_g2_rgb_l, 10)
        self.create_subscription(Image,
            '/gripper2/stereo/right/image', self.cb_g2_rgb_r, 10)

        # 鱼眼图像
        self.create_subscription(Image,
            '/gripper1/fisheye/image', self.cb_g1_fish, 10)
        self.create_subscription(Image,
            '/gripper2/fisheye/image', self.cb_g2_fish, 10)

        # 位姿（3D运动）
        self.create_subscription(PoseStamped,
            '/gripper1/pose', self.cb_g1_pose, 10)
        self.create_subscription(PoseStamped,
            '/gripper2/pose', self.cb_g2_pose, 10)

        # ========== Qt界面 ==========
        self.app = QApplication([])
        self.window = QMainWindow()
        self.window.setWindowTitle('Ego-Pick Visualizer')
        self.window.resize(1280, 720)

        # 创建图像显示标签
        self.labels = {
            'g1_rgb_l': QLabel(),
            'g1_rgb_r': QLabel(),
            'g2_rgb_l': QLabel(),
            'g2_rgb_r': QLabel(),
            'g1_fish': QLabel(),
            'g2_fish': QLabel(),
        }

        # 3D可视化（使用Open3D或matplotlib）
        self.ax_3d = None  # 3D坐标轴

        # 定时器刷新UI
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(33)  # ~30Hz

    def update_ui(self):
        """更新所有图像显示"""
        for name, img in self.current_images.items():
            if img is not None:
                h, w = img.shape[:2]
                bytes_per_line = 3 * w
                qt_img = QImage(img.data, w, h,
                               bytes_per_line, QImage.Format_RGB888)
                self.labels[name].setPixmap(QPixmap.fromImage(qt_img))

        # 更新3D轨迹
        self.update_3d_view()

    def update_3d_view(self):
        """更新3D运动视图"""
        if self.pose_history_g1 and self.pose_history_g2:
            # 绘制两个夹爪的3D轨迹
            pass

    def cb_g1_rgb_l(self, msg):
        self.current_images['g1_rgb_l'] = self.bridge.imgmsg_to_cv2(msg)

    # ... 其他回调类似 ...


def main(args=None):
    rclpy.init(args=args)
    visualizer = GripperVisualizer()

    # 在单独线程运行ROS2
    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(visualizer)

    # 运行Qt应用
    import threading
    ros_thread = threading.Thread(target=executor.spin)
    ros_thread.start()

    visualizer.app.exec_()

    visualizer.destroy_node()
    rclpy.shutdown()


# ========== 3D运动视图（Open3D） ==========
import open3d as o3d

class MotionVisualizer3D:
    def __init__(self):
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window('3D Motion')

        # 夹爪1轨迹线
        self.line_g1 = o3d.geometry.LineSet()
        # 夹爪2轨迹线
        self.line_g2 = o3d.geometry.LineSet()

        # 添加坐标系
        self.coord = o3d.geometry.TriangleMesh.create_coordinate_frame()

    def add_pose(self, pose, gripper_id):
        """添加新的位姿点到轨迹"""
        # 提取位置
        pos = [pose.position.x, pose.position.y, pose.position.z]
        # 添加到对应夹爪的轨迹点
        # 更新线段集合

    def update(self):
        """刷新3D视图"""
        self.vis.update_geometry(self.line_g1)
        self.vis.update_geometry(self.line_g2)
        self.vis.poll_events()
        self.vis.update_renderer()
```

Qt依赖包：
```yaml
dependencies:
  - rclpy
  - sensor_msgs
  - geometry_msgs
  - image_transport
  - cv_bridge
  - PyQt5  # 或 PyQt6
  - open3d  # 3D可视化（可选）
  - trimesh  # STEP模型加载
```

---

### 6.4 STEP模型加载与IMU姿态可视化

#### STEP模型加载

STEP文件 → Open3D三角网格 → 应用IMU四元数姿态

```python
import trimesh
import numpy as np
from scipy.spatial.transform import Rotation as R

def load_step_model(step_path):
    """加载STEP模型并转为Open3D网格"""
    # 方法1: trimesh直接加载
    mesh = trimesh.load_mesh(step_path)

    # 方法2: 若trimesh不支持，用OCC(OpenCASCADE)
    # 需要安装: pip install cadquery-occ蛭

    # 转为numpy数组
    vertices = np.array(mesh.vertices)
    faces = np.array(mesh.faces)

    # 转为Open3D格式
    import open3d as o3d
    o3d_mesh = o3d.geometry.TriangleMesh()
    o3d_mesh.vertices = o3d.utility.Vector3dVector(vertices)
    o3d_mesh.triangles = o3d.utility.Vector3iVector(faces)
    o3d_mesh.compute_vertex_normals()

    return o3d_mesh


class GripperModel:
    def __init__(self, step_path):
        self.mesh = load_step_model(step_path)
        self.mesh.paint_uniform_color([0.8, 0.2, 0.2])  # 红色

    def set_pose(self, position, quaternion):
        """设置模型姿态（来自IMU）

        Args:
            position: [x, y, z] 位置
            quaternion: [x, y, z, w] 四元数
        """
        # 创建变换矩阵
        T = np.eye(4)

        # 设置位置
        T[:3, 3] = position

        # 设置旋转（四元数 → 旋转矩阵）
        rot = R.from_quat(quaternion)  # scipy
        T[:3, :3] = rot.as_matrix()

        # 应用变换
        self.mesh.transform(T)

    def reset_pose(self, step_path):
        """重置模型（重新加载）"""
        self.mesh = load_step_model(step_path)
```

#### IMU姿态订阅与更新

```python
from sensor_msgs.msg import Imu

class GripperIMUVisualizer:
    def __init__(self, step_path_g1, step_path_g2):
        # 加载模型
        self.gripper1 = GripperModel(step_path_g1)
        self.gripper2 = GripperModel(step_path_g2)

        # Open3D可视化窗口
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window('Gripper 3D View', 1280, 720)

        # 添加坐标系
        coord = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.1)
        self.vis.add_geometry(coord)

        # 添加夹爪模型
        self.vis.add_geometry(self.gripper1.mesh)
        self.vis.add_geometry(self.gripper2.mesh)

        # ROS2订阅
        self.sub_imu1 = self.create_subscription(Imu,
            '/gripper1/imu/data', self.cb_imu1, 10)
        self.sub_imu2 = self.create_subscription(Imu,
            '/gripper2/imu/data', self.cb_imu2, 10)

        # 当前位姿
        self.pose1 = [0, 0, 0]
        self.pose2 = [0, 0, 0]
        self.quat1 = [0, 0, 0, 1]
        self.quat2 = [0, 0, 0, 1]

    def cb_imu1(self, msg):
        """IMU回调（需要已积分的位姿）"""
        # 从IMU原始数据积分得到位姿（见pose_estimator）
        # 这里直接使用pose_estimator发布的位姿
        self.pose1 = [msg.orientation.x,
                      msg.orientation.y,
                      msg.orientation.z]
        self.quat1 = [msg.orientation.x,
                       msg.orientation.y,
                       msg.orientation.z,
                       msg.orientation.w]

    def update(self):
        """更新3D显示"""
        # 重新加载并应用新姿态
        self.gripper1.mesh = load_step_model(self.gripper1.step_path)
        self.gripper1.set_pose(self.pose1, self.quat1)

        self.gripper2.mesh = load_step_model(self.gripper2.step_path)
        self.gripper2.set_pose(self.pose2, self.quat2)

        # 更新几何体
        self.vis.update_geometry(self.gripper1.mesh)
        self.vis.update_geometry(self.gripper2.mesh)

        # 刷新
        self.vis.poll_events()
        self.vis.update_renderer()
```

#### 完整集成

```python
class EgoPickVisualizer(Node):
    def __init__(self):
        super().__init__('ego_pick_visualizer')

        # ========== 1. 图像订阅 ==========
        self.image_subs = {
            'g1_rgb_l': Image,
            'g1_rgb_r': Image,
            'g2_rgb_l': Image,
            'g2_rgb_r': Image,
            'g1_fish': Image,
            'g2_fish': Image,
        }
        # ... 订阅代码同前 ...

        # ========== 2. STEP模型加载 ==========
        self.gripper1_model = GripperModel('path/to/gripper1.step')
        self.gripper2_model = GripperModel('path/to/gripper2.step')

        # ========== 3. 位姿订阅（IMU积分结果）==========
        self.create_subscription(PoseStamped,
            '/gripper1/pose', self.cb_pose1, 10)
        self.create_subscription(PoseStamped,
            '/gripper2/pose', self.cb_pose2, 10)

        # ========== 4. Open3D 3D窗口 ==========
        self.vis3d = o3d.visualization.Visualizer()
        self.vis3d.create_window('3D Motion', 640, 480)

        # 添加地面
        ground = o3d.geometry.TriangleMesh.create_box(2, 2, 0.01)
        ground.translate([0, 0, -0.01])
        ground.paint_uniform_color([0.9, 0.9, 0.9])
        self.vis3d.add_geometry(ground)

        # 添加坐标系
        self.vis3d.add_geometry(
            o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.1))

        # 添加夹爪模型
        self.vis3d.add_geometry(self.gripper1_model.mesh)
        self.vis3d.add_geometry(self.gripper2_model.mesh)

        # 夹爪颜色区分
        self.gripper1_model.mesh.paint_uniform_color([1, 0.2, 0.2])  # 红色
        self.gripper2_model.mesh.paint_uniform_color([0.2, 0.2, 1])  # 蓝色

        # ========== 5. Qt图像窗口 ==========
        self.app = QApplication([])
        self.window = QMainWindow()
        layout = QGridLayout()

        # 2x3 图像网格
        layout.addWidget(self.labels['g1_rgb_l'], 0, 0)
        layout.addWidget(self.labels['g1_rgb_r'], 0, 1)
        layout.addWidget(self.labels['g2_rgb_l'], 1, 0)
        layout.addWidget(self.labels['g2_rgb_r'], 1, 1)
        layout.addWidget(self.labels['g1_fish'], 2, 0)
        layout.addWidget(self.labels['g2_fish'], 2, 1)

        # 3D视图放在右侧
        self.o3d_widget = self.create_o3d_widget()  # 需要包装Open3D窗口
        layout.addWidget(self.o3d_widget, 0, 2, 3, 1)

        # ========== 6. 刷新定时器 ==========
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all)
        self.timer.start(33)  # 30Hz

    def update_all(self):
        """刷新所有"""
        # 刷新图像
        self.update_images()

        # 刷新3D
        self.gripper1_model.set_pose(self.pose1, self.quat1)
        self.gripper2_model.set_pose(self.pose2, self.quat2)
        self.vis3d.update_geometry(self.gripper1_model.mesh)
        self.vis3d.update_geometry(self.gripper2_model.mesh)
        self.vis3d.poll_events()
        self.vis3d.update_renderer()
```

#### 3D视图嵌入Qt窗口

Open3D的VisualizerWindow不能直接嵌入Qt，需要用 widget 包装：

```python
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWinExtras import QtWin

# Open3D渲染到QWidget的hack方法
# 方法1: 使用 offscreen rendering
def create_o3d_offscreen(self):
    """创建离屏渲染的O3D visualizer"""
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False)  # 不可见

    # 渲染到 numpy array
    def render():
        vis.poll_events()
        vis.update_renderer()
        img = vis.capture_screen_float_buffer()
        return (np.asarray(img) * 255).astype(np.uint8)

    return render

# 方法2: 使用 o3d.visualization.ViewControl
# 更流畅但需要平台特定代码
```

---

### 6.5 图像处理

| 用途 | 库 | 说明 |
|------|-----|------|
| 图像基础 | OpenCV 4.8+ | 畸变校正, 滤波 |
| 立体匹配 | OpenCV StereoBM/SGBM | 深度估计 |
| 鱼眼校正 | OpenCV fisheye模块 | 畸变校正 |
| GPU加速 | CUDA + OpenCV CUDA | Jetson优化 |

### 6.6 数据处理

| 用途 | 库 | 说明 |
|------|-----|------|
| IMU滤波 | imu_filter_madgwick | 姿态解算 |
| EKF融合 | robot_localization | 多传感器融合 |
| 时间同步 | message_filters | 话题同步 |
| 数据存储 | rosbag2 + h5py | 录制存储 |

### 6.7 推荐ROS2包

```yaml
# 必需包
dependencies:
  - rclpy (ROS2 Python客户端)
  - sensor_msgs
  - geometry_msgs
  - image_transport
  - image_geometry
  - cv_bridge (OpenCV桥接)
  - message_filters (时间同步)
  - tf2_ros (坐标变换)
  - robot_localization (EKF)
  - imu_filter_madgwick
  - vision_msgs

# 推荐包
  - rosbag2_recorder
  - rviz2
  - rqt_graph
  - rqt_image_view
  - rqt_plot

# 可选包
  - usb_cam (V4L2相机驱动)
  - stereo_image_proc (立体校正)
  - image_proc (单目校正)
```

---

## 7. 性能优化建议 / Performance Optimization

### 7.1 实时性优化

#### 硬实时要求节点 (IMU, Pose Estimator)

```bash
# 1. 使用cyclonedds配置
# /etc/cyclonedds.xml
<Domain>
  <General>
    <NetworkInterfaceAddress>auto</NetworkInterfaceAddress>
    <AllowMulticast>false</AllowMulticast>
  </General>
  <Partitioning>
    <NetworkPartition>
      <Name>rt_control</Name>
      <AddressPartition>
        <Address>239.0.0.1</Address>
      </AddressPartition>
    </NetworkPartition>
  </Partitioning>
</Domain>

# 2. QoS配置
- reliability: RELIABLE (IMU)
- durability: VOLATILE
- history: KEEP_LAST (depth: 100)
- deadline: 5ms (IMU 200Hz)
```

#### 调度策略

```python
# 设置实时优先级
import rclpy
rclpy.init()
node = rclpy.create_node('imu_node')

# 获取调度策略
sched = os.sched_getscheduler()
param = rclpy.node.Node.get_parameter('sched_priority')
```

### 7.2 图像处理优化

#### CUDA加速

```python
# 使用GStreamer + CUDA流水线
GST_PIPELINE = (
    "nvv4l2camerasrc device=/dev/video0 ! "
    "video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1 ! "
    "nvvidconv ! "
    "video/x-raw(memory:NVMM),format=I420 ! "
    "nvvidconv ! "
    "video/x-raw,format=BGRx ! "
    "appsink"
)
```

#### 多线程图像获取

```python
# 异步图像回调
import threading
from collections import deque

class StereoCameraNode:
    def __init__(self):
        self.frame_queue = deque(maxlen=10)
        self.lock = threading.Lock()

    def image_callback(self, left, right):
        with self.lock:
            self.frame_queue.append((left, right))

    def processing_loop(self):
        while rclpy.ok():
            with self.lock:
                if self.frame_queue:
                    left, right = self.frame_queue.popleft()
                    # 处理图像
```

### 7.3 内存优化

#### 图像压缩发布

```python
# 图像压缩传输
from image_transport import CompressedPublisher

self.compressed_pub = CompressedPublisher(
    'compressed_image',
    self.qos_profile
)
# 压缩质量: 85% JPEG
# 节省带宽: 90%
```

#### Zero-Copy共享内存

```python
# 使用共享内存传递大图像
# 将图像数据存储在共享内存中
# 避免复制

from tracetools_image_pipeline import SHMImagePub

# 只传输指针而非数据
```

### 7.4 带宽优化

#### 话题压缩

```bash
# image_transport压缩插件
ros2 run image_transport_plugins ros2_image_transport_republish \
    --ros-args \
    -r input:=/gripper1/stereo/left/image_raw \
    -r output:=/gripper1/stereo/left/image_compressed
```

#### 话题过滤

```python
# 只发布必要的图像
self.left_pub = self.create_publisher(
    Image,
    '/gripper1/stereo/left/image',
    10
)

# 对于可视化，使用低分辨率
# 对于录制，发布全分辨率
```

### 7.5 资源分配 (Jetson NX)

```
┌─────────────────────────────────────────────────────────┐
│                 Jetson NX Resource Allocation            │
├─────────────────────────────────────────────────────────┤
│  CPU Core 0: IMU Node (实时)                            │
│  CPU Core 1: Encoder Node                               │
│  CPU Core 2: Pose Estimator (实时)                     │
│  CPU Core 3: State Manager                              │
│  CPU Core 4: Visualization Manager                      │
│  CPU Core 5: Data Recorder                               │
├─────────────────────────────────────────────────────────┤
│  GPU: CUDA图像处理 (Stereo/Fisheye)                      │
│  Memory: 8GB DDR4                                        │
│  Storage: NVMe SSD (推荐500GB+)                          │
└─────────────────────────────────────────────────────────┘
```

---

## 8. 目录结构 / Directory Structure

```
ego_pick/
├── src/
│   ├── ego_gripper/
│   │   ├── ego_gripper/
│   │   │   ├── __init__.py
│   │   │   ├── gripper_state_manager.py
│   │   │   ├── pose_estimator.py
│   │   │   ├── encoder_node.py
│   │   │   ├── imu_node.py
│   │   │   ├── stereo_camera_node.py
│   │   │   ├── fisheye_camera_node.py
│   │   │   └── visualization_manager.py
│   │   ├── msg/
│   │   │   ├── GripperState.msg
│   │   │   └── GripperControl.srv
│   │   ├── launch/
│   │   │   ├── gripper1.launch.py
│   │   │   ├── gripper2.launch.py
│   │   │   └── bringup.launch.py
│   │   ├── config/
│   │   │   ├── gripper1_params.yaml
│   │   │   ├── gripper2_params.yaml
│   │   │   ├── stereo_calibration.yaml
│   │   │   └── fisheye_calibration.yaml
│   │   ├── urdf/
│   │   │   ├── gripper.urdf.xacro
│   │   │   └── dual_gripper.urdf.xacro
│   │   ├── rviz/
│   │   │   └── ego_visualization.rviz
│   │   ├── scripts/
│   │   │   ├── data_recorder.py
│   │   │   └── export_node.py
│   │   ├── test/
│   │   │   ├── test_encoder.py
│   │   │   ├── test_imu.py
│   │   │   └── test_integration.py
│   │   └── package.xml
│   │
│   ├── ego_msgs/                   # 自定义消息包
│   │   ├── msg/
│   │   │   ├── GripperState.msg
│   │   │   ├── EgoTrajectory.msg
│   │   │   └── StereoPair.msg
│   │   ├── srv/
│   │   │   ├── Calibrate.srv
│   │   │   └── Export.srv
│   │   └── package.xml
│   │
│   └── ego_utils/                  # 工具包
│       ├── ego_utils/
│       │   ├── calibration.py
│       │   ├── visualization.py
│       │   └── data_processing.py
│       └── package.xml
│
├── docs/
│   ├── architecture.md
│   ├── api_reference.md
│   └── calibration_guide.md
│
├── scripts/
│   ├── setup_jetson.sh
│   ├── install_dependencies.sh
│   └── record_session.sh
│
├── config/
│   ├── cyclonedds.xml
│   └── realsense_params.yaml
│
├── CMakeLists.txt
├── package.xml
└── README.md
```

---

## 9. 启动文件 / Launch Files

### 9.1 主启动文件 (bringup.launch.py)

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # 获取包路径
    pkg_share = get_package_share_directory('ego_gripper')

    # Gripper 1 节点组
    gripper1_nodes = [
        Node(
            package='ego_gripper',
            executable='encoder_node',
            name='encoder_node_g1',
            namespace='/gripper1',
            parameters=[pkg_share + '/config/gripper1_params.yaml'],
            remappings=[('/raw', '/encoder/raw')]
        ),
        Node(
            package='ego_gripper',
            executable='imu_node',
            name='imu_node_g1',
            namespace='/gripper1',
            parameters=[pkg_share + '/config/gripper1_params.yaml'],
            remappings=[('/raw', '/imu/raw')]
        ),
        # ... 其他节点
    ]

    # Gripper 2 节点组
    gripper2_nodes = [
        # ... 类似配置
    ]

    # 可视化节点
    viz_nodes = [
        Node(
            package='ego_gripper',
            executable='visualization_manager',
            name='viz_manager',
            namespace='/viz',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', pkg_share + '/rviz/ego_visualization.rviz']
        )
    ]

    # 数据录制节点
    recorder_node = Node(
        package='ego_gripper',
        executable='data_recorder',
        name='data_recorder',
        namespace='/export',
        parameters=[{
            'storage_path': '/data/ego_pick',
            'max_storage_size_gb': 400,
            'compression': 'lz4'
        }]
    )

    return LaunchDescription([
        *gripper1_nodes,
        *gripper2_nodes,
        *viz_nodes,
        recorder_node
    ])
```

---

## 10. 配置文件 / Configuration Files

### 10.1 夹爪参数配置 (gripper1_params.yaml)

```yaml
/gripper1:
  encoder_node:
    ros__parameters:
      device: '/dev/ttyUSB0'
      baudrate: 115200
      resolution: 4096  # ticks per revolution
      offset_rad: 0.0
      distance_coefficient: 50.0  # mm/rad，角度转距离的标定系数
      lpf_cutoff_hz: 50.0
      publish_rate: 100

  imu_node:
    ros__parameters:
      device: '/dev/ttyUSB1'
      baudrate: 115200
      sample_rate: 200
      gyro_range: 250  # dps
      accel_range: 2   # g
      mag_range: 4900  # μT
      publish_rate: 200

  gripper_state_manager:
    ros__parameters:
      gripper_id: 1
      max_open_distance: 50.0  # mm，最大开合距离
      min_open_distance: 0.0   # mm，最小开合距离
      velocity_threshold: 0.5   # mm/s
      publish_rate: 100

  pose_estimator:
    ros__parameters:
      algorithm: 'madgwick'
      beta: 0.1
      zupt_threshold: 0.05
      gravity: 9.81
      publish_rate: 100

  stereo_camera_node:
    ros__parameters:
      device: '/dev/video2'
      resolution: [1280, 720]
      framerate: 30
      stereo_baseline_m: 0.12
      auto_exposure: true
      target_fps: 30

  fisheye_camera_node:
    ros__parameters:
      device: '/dev/video4'
      resolution: [640, 480]
      framerate: 30
      fov_deg: 180
      distortion_k1: -0.3
      distortion_k2: 0.1
```

---

## 11. 服务接口 / Service Interfaces

### 11.1 夹爪控制服务

| 服务名 | 类型 | 请求 | 响应 | 描述 |
|--------|------|------|------|------|
| `/gripperX/calibrate` | `Calibrate.srv` | mode, timeout | success, message | 校准服务 |
| `/gripperX/reset` | `Reset.srv` | - | success, message | 重置服务 |
| `/gripperX/set_position` | `SetPosition.srv` | angle, speed | success, message | 位置控制 |
| `/gripperX/get_info` | `GetInfo.srv` | - | info | 获取夹爪信息 |
| `/export/start` | `Export.srv` | format, path | job_id | 启动导出 |
| `/export/status` | `ExportStatus.srv` | job_id | status, progress | 导出状态 |

---

## 12. 错误处理与监控 / Error Handling & Monitoring

### 12.1 错误标志定义

```python
ERROR_NONE = 0x0000
ERROR_ENCODER_COMM = 0x0001  # 编码器通信错误
ERROR_ENCODER_TIMEOUT = 0x0002  # 编码器超时
ERROR_IMU_COMM = 0x0004  # IMU通信错误
ERROR_IMU_DATA = 0x0008  # IMU数据异常
ERROR_CAMERA_LEFT = 0x0010  # 左相机错误
ERROR_CAMERA_RIGHT = 0x0020  # 右相机错误
ERROR_CAMERA_FISHEYE = 0x0040  # 鱼眼相机错误
ERROR_STORAGE_FULL = 0x0080  # 存储满
```

### 12.2 诊断主题

```python
# /system/diagnostics
diagnostic_msgs/DiagnosticStatus

level: 0=OK, 1=WARN, 2=ERROR
name: "gripper1_state_manager"
message: "Running normally"
hardware_id: "gripper1-001"
values:
  - key: "Encoder_FPS" value: "99.8"
  - key: "IMU_FPS" value: "199.5"
  - key: "Camera_FPS" value: "29.7"
  - key: "Memory_Usage" value: "2.3GB"
  - key: "Storage_Free" value: "320GB"
```

---

## 13. 测试计划 / Testing Plan

### 13.1 单元测试

```bash
# 运行所有单元测试
colcon test --packages-select ego_gripper --ctest-args -V

# 测试覆盖
- encoder_node: 角度解析, 滤波, 边界检测
- imu_node: 数据读取, 校验, 异常检测
- pose_estimator: 四元数运算, 积分, ZUPT
```

### 13.2 集成测试

```bash
# 启动完整系统
ros2 launch ego_gripper bringup.launch.py

# 验证
rostopic hz /gripper1/state
rostopic hz /gripper1/pose
rostopic hz /gripper1/stereo/left/image
```

---

## 14. 总结 / Summary

### 14.1 架构特点

1. **模块化设计**: 每个传感器独立节点，便于调试和维护
2. **实时性保证**: IMU和编码器使用硬实时调度
3. **可扩展性**: 命名空间设计支持多夹爪扩展
4. **可视化完整**: RViz集成3D/图像/数据多维度显示
5. **数据完整性**: 多格式录制保证数据可追溯

### 14.2 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| IMU延迟 | <5ms | 200Hz采样 |
| 图像延迟 | <50ms | 30Hz刷新 |
| 位姿更新 | <10ms | 100Hz控制 |
| 录制吞吐 | >100MB/s | NVMe SSD |

### 14.3 后续优化方向

1. 使用EKF替代Madgwick提升精度
2. 引入GPU加速图像处理
3. 实现云边协同数据处理
4. 添加Web可视化界面
5. 支持ROS2 ActionServer实现复杂控制

---

*文档版本: 1.0*
*创建日期: 2026/04/25*
*维护者: Ego-Pick Team*
