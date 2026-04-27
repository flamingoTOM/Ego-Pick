# ROS1 到 ROS2 迁移指南

> 本文档帮助你从 ROS1 快速迁移到 ROS2，以 ROS2 Humble 为例。

---

## 1. 初始化环境

### ROS1
```bash
source /opt/ros/noetic/setup.bash   # 需要手动source
roscore                                    # 启动master
```

### ROS2
```bash
source /opt/ros/humble/setup.bash    # 也是手动source，但不需要master
ros2 run <package_name> <node_name>  # 直接运行节点，不需要roscore
```

**核心区别**: ROS2 没有 master，所有节点平等通信，采用 DDS 中间件。

---

## 2. 工作空间创建

### ROS1 & ROS2 相同
```bash
mkdir -p ~/ego_ws/src
cd ~/ego_ws
catkin_make              # ROS1
# 或者
colcon build             # ROS2
```

### ROS2 额外支持
```bash
colcon build --symlink-install  # 符号链接安装，修改代码不用重新编译
```

---

## 3. 编译系统

### ROS1 (catkin)
```bash
cd ~/ego_ws
catkin_make                    # 编译整个工作空间
catkin_make install           # 安装到install目录

# 或使用 catkin_tools
catkin build
```

### ROS2 (colcon)
```bash
cd ~/ego_ws
colcon build                   # 编译
colcon build --packages-select my_package  # 只编译指定包
colcon build --symlink-install # 符号链接，修改代码后不用重新编译
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release  # CMake参数
```

**重要区别**: ROS2 的 `colcon build` 自动处理 CMake 和 Python 包的编译，不需要像 ROS1 那样区分 `catkin_make_isolated`。

---

## 4. Package 结构

### ROS1
```
my_package/
├── CMakeLists.txt
├── package.xml
├── src/
├── include/
├── scripts/
├── launch/
├── config/
└── msg/
```

### ROS2
```
my_package/
├── CMakeLists.txt          # 或 package.xml (纯Python包)
├── package.xml
├── src/
├── include/
├── scripts/
├── launch/
├── config/
├── msg/
├── srv/
└── action/                 # ROS2 支持 action
```

主要变化：ROS2 的 `msg` 和 `srv` 文件位置没变，但内部语法略有调整（时间类型等）。

---

## 5. Launch 文件

### ROS1 (XML)
```xml
<launch>
  <node name="talker" pkg="rospy_tutorials" type="talker" output="screen"/>
  <node name="listener" pkg="rospy_tutorials" type="listener" output="screen"/>

  <!-- 参数设置 -->
  <param name="param_name" value="value"/>

  <!-- 命名空间 -->
  <ns name="my_namespace">
    <node name="node_in_ns" pkg="pkg" type="type"/>
  </ns>
</launch>
```

### ROS2 (Python，推荐) 或 XML
```python
# launch/talker_listener.launch.py (Python方式，推荐)
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='demo_nodes_cpp',
            executable='talker',
            name='talker',
            output='screen',
            parameters=[{'param_name': 'value'}]  # 参数直接内联
        ),
        Node(
            package='demo_nodes_cpp',
            executable='listener',
            name='listener',
            output='screen',
            namespace='my_namespace'             # 命名空间直接指定
        ),
    ])
```

```xml
<!-- launch/talker_listener.launch.xml (XML方式) -->
<launch>
  <node pkg="demo_nodes_cpp" exec="talker" name="talker" output="screen"/>
  <node pkg="demo_nodes_cpp" exec="listener" name="listener" output="screen"/>
</launch>
```

**关键区别**:
| 特性 | ROS1 | ROS2 |
|------|------|------|
| 推荐格式 | XML | Python |
| 参数传递 | `<param>` | `parameters=[{}]` |
| 命名空间 | `<ns>` | `namespace=` |
| 条件启动 | 不原生支持 | 支持 `IfCondition` |

**运行Launch**:
```bash
# ROS1
roslaunch <package> <launch_file.launch>

# ROS2
ros2 launch <package> <launch_file.launch.py>
```

---

## 6. 常用命令对比

| 功能 | ROS1 | ROS2 |
|------|------|------|
| 列出包 | `rospack list` | `ros2 pkg list` |
| 列出节点 | `rosnode list` | `ros2 node list` |
| 列出话题 | `rostopic list` | `ros2 topic list` |
| 列出服务 | `rosservice list` | `ros2 service list` |
| 查看话题详情 | `rostopic info /chatter` | `ros2 topic info /chatter` |
| Echo话题 | `rostopic echo /chatter` | `ros2 topic echo /chatter` |
| 发布话题 | `rostopic pub /chatter std_msgs/String "data: hello"` | `ros2 topic pub /chatter std_msgs/msg/String "data: hello"` |
| 调用服务 | `rosservice call /add "a: 1 b: 2"` | `ros2 service call /add example_interfaces/srv/AddTwoInts "a: 1 b: 2"` |
| 查看包信息 | `rospack info <pkg>` | `ros2 pkg info <pkg>` |
| 列出launch | `roslaunch -p` | `ros2 launch-list` |
| 列出动作 | `rostopic list /action` | `ros2 action list` |

---

## 7. 话题/服务/动作 语法

### ROS1
```bash
rostopic pub /chatter std_msgs/String "data: 'hello'" -1
rosservice call /add "a: 1 b: 2"
```

### ROS2
```bash
ros2 topic pub /chatter std_msgs/msg/String "{data: 'hello'}"
ros2 service call /add example_interfaces/srv/AddTwoInts "{a: 1, b: 2}"
```

注意 ROS2 使用 `{key: value}` JSON风格而不是 `key: value` 单行字符串。

---

## 8. 参数操作

### ROS1
```bash
rosparam set /param_name value
rosparam get /param_name
rosparam list
```

### ROS2
```bash
ros2 param set /node_name param_name value
ros2 param get /node_name param_name
ros2 param list
```

---

## 9. 包依赖写法

### package.xml (ROS1 vs ROS2 基本相同)
```xml
<package format="3">
  <name>my_package</name>
  <version>1.0.0</version>
  <description>My package</description>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>ament_python</buildtool_depend>  <!-- ROS2支持Python包 -->

  <depend>rclcpp</depend>         <!-- ROS2: 运行时依赖 -->
  <depend>std_msgs</depend>

  <exec_depend>rospy</exec_depend>

  <test_depend>ament_lint_auto</test_depend>
</package>
```

---

## 10. 关键概念差异总结

| 类别 | ROS1 | ROS2 |
|------|------|------|
| Master | 有 (roscore) | 无 (DDS) |
| 编译工具 | catkin_make / catkin_tools | colcon |
| 构建类型 | catkin | ament (CMake/Python) |
| Launch格式 | XML | Python (推荐) 或 XML |
| 命名空间 | `<ns>` | `namespace=` 参数 |
| 参数类型 | 字典混合 | 结构化参数 |
| 语言支持 | C++/Python/Lisp | C++/Python/Rust |
| 跨平台 | Linux为主 | Linux/Windows/macOS |
| 实时性 | 无官方支持 | 计划支持 (RMW) |
| 安全性 | 无 | SROS2 原生支持 |
| 生命周期 | 无 | 节点生命周期管理 |

---

## 11. 快速入门命令清单

```bash
# 1. Source 环境
source /opt/ros/humble/setup.bash

# 2. 创建工作空间
mkdir -p ~/ego_ws/src
cd ~/ego_ws

# 3. 克隆或创建包
cd src
git clone <repo>

# 4. 编译
colcon build

# 5. Source 工作空间 (可选，写入 ~/.bashrc)
source install/setup.bash

# 6. 运行节点
ros2 run <package> <executable>

# 7. 运行launch
ros2 launch <package> <launch_file.launch.py>

# 8. 常用调试
ros2 topic list
ros2 node list
ros2 topic echo /topic_name
rqt_graph                    # 可视化节点图 (ROS2也可用)
```

---

## 12. 资源链接

- [ROS2 Humble 官方文档](https://docs.ros.org/en/humble/)
- [ROS2 中文文档](https://docs.ros.org/en/humble/Tutorials.html)
- [ROS1 到 ROS2 迁移指南](https://docs.ros.org/en/humble/How-To-Guides/Migrating-from-ROS1.html)

---

*文档创建于 2026/04/27*
