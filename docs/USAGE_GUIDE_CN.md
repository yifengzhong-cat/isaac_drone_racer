# 使用指南 / User Guide

## 快速开始 / Quick Start

本指南将帮助您快速上手使用新添加的功能。

### 1. 基本使用（不使用ROS）

如果您只想使用原有功能（无需传感器和ROS），代码无需修改：

```bash
# 训练
python3 scripts/rl/train.py --task Isaac-Drone-Racer-v0 --headless --num_envs 4096

# 运行
python3 scripts/rl/play.py --task Isaac-Drone-Racer-Play-v0 --num_envs 1
```

**说明**：传感器默认是禁用的，所以现有代码可以直接运行，不受影响。

---

### 2. 启用传感器（不使用ROS）

如果您想使用新添加的深度相机和激光雷达，但不需要ROS集成：

#### 方法1：创建自定义配置类

```python
from tasks.drone_racer import DroneRacerEnvCfg
import gymnasium as gym

# 创建自定义配置
class MyEnvCfg(DroneRacerEnvCfg):
    def __post_init__(self):
        """自定义post_init，保持传感器启用"""
        # 不禁用传感器
        # self.scene.depth_camera = None  # 注释掉这一行以启用深度相机
        # self.scene.lidar = None  # 注释掉这一行以启用激光雷达
        # self.scene.imu = None  # 注释掉这一行以启用IMU
        
        # 启用传感器观测组
        # self.observations.sensor = None  # 注释掉以启用传感器观测
        
        # 其他配置保持不变
        self.observations.critic = None
        self.events.reset_base = None
        self.commands.target.randomise_start = True
        self.decimation = 4
        self.episode_length_s = 20
        self.viewer.eye = (-10.0, -10.0, 10.0)
        self.viewer.lookat = (0.0, 0.0, 0.0)
        self.sim.dt = 1 / 400
        self.sim.render_interval = self.decimation

# 使用自定义配置创建环境
env = gym.make("Isaac-Drone-Racer-v0", cfg=MyEnvCfg())
```

#### 方法2：直接修改配置文件

编辑 `tasks/drone_racer/drone_racer_env_cfg.py`，注释掉禁用传感器的代码：

```python
def __post_init__(self) -> None:
    """Post initialization."""
    
    # 注释掉下面的行以启用传感器
    # self.scene.imu = None
    # self.scene.depth_camera = None
    # self.scene.lidar = None
    
    # 注释掉下面的行以启用传感器观测
    # self.observations.sensor = None
    
    # ... 其他代码保持不变
```

---

### 3. 使用ROS集成

如果您想将传感器数据发布到ROS 2，请按照以下步骤操作。

#### 步骤1：安装ROS 2

```bash
# Ubuntu 22.04 推荐安装 ROS 2 Humble
sudo apt update
sudo apt install ros-humble-desktop

# 安装Python ROS包
pip install rclpy sensor_msgs std_msgs
```

#### 步骤2：运行示例脚本

我们提供了一个完整的示例脚本 `scripts/rl/play_with_ros.py`：

```bash
# 确保已source ROS 2环境
source /opt/ros/humble/setup.bash

# 运行示例（会自动启用传感器并发布到ROS话题）
python3 scripts/rl/play_with_ros.py --task Isaac-Drone-Racer-Play-v0 --num_envs 1
```

#### 步骤3：在另一个终端查看ROS话题

```bash
# 新开一个终端
source /opt/ros/humble/setup.bash

# 查看可用的话题
ros2 topic list

# 应该能看到以下话题：
# /drone/imu
# /drone/depth/image_raw
# /drone/scan
# /drone/camera/image_raw

# 查看话题数据
ros2 topic echo /drone/imu

# 或者使用RViz2可视化
rviz2
```

#### 步骤4：在您自己的代码中使用ROS桥接

```python
from tasks.drone_racer.ros_bridge import create_ros_bridge
import gymnasium as gym

# 1. 创建环境（需要启用传感器，参考上面的方法）
env = gym.make("Isaac-Drone-Racer-v0", cfg=my_sensor_enabled_cfg)

# 2. 创建ROS桥接
ros_bridge = create_ros_bridge(env, publish_rate=30)  # 30Hz发布频率

if ros_bridge is not None:
    print("ROS桥接初始化成功！")
    
    # 3. 在您的仿真循环中
    obs = env.reset()
    
    while True:
        # 执行动作
        action = your_policy.get_action(obs)
        obs, reward, done, info = env.step(action)
        
        # 发布传感器数据到ROS话题
        ros_bridge.publish_all(env_idx=0)  # 发布第一个环境的数据
        ros_bridge.spin_once()  # 处理ROS回调
        
        if done:
            obs = env.reset()
    
    # 4. 清理
    ros_bridge.shutdown()
else:
    print("ROS不可用，继续运行但不发布传感器数据")

env.close()
```

---

### 4. Hello Kitty门纹理

新的Hello Kitty主题纹理已经自动应用到所有竞速门上。不需要任何代码修改，运行仿真时就能看到：

```bash
# 运行仿真（不使用headless模式以查看视觉效果）
python3 scripts/rl/play.py --task Isaac-Drone-Racer-Play-v0 --num_envs 1
```

纹理特点：
- 粉色基调配合深粉色轮廓
- 8个红色蝴蝶结装饰
- Hello Kitty风格的可爱设计

---

## 常见问题 / FAQ

### Q1: 为什么我运行代码后没有看到传感器数据？
**A**: 传感器默认是禁用的。请按照"启用传感器"部分的说明启用它们。

### Q2: ROS桥接报错 "ROS 2 packages not available"
**A**: 需要先安装ROS 2和Python ROS包：
```bash
pip install rclpy sensor_msgs std_msgs
source /opt/ros/humble/setup.bash
```

### Q3: 如何只启用某些传感器而不是全部？
**A**: 在自定义配置的 `__post_init__` 方法中，只注释掉您需要的传感器对应的禁用代码。例如，只启用深度相机：
```python
def __post_init__(self):
    self.scene.imu = None  # 保持IMU禁用
    # self.scene.depth_camera = None  # 注释掉以启用深度相机
    self.scene.lidar = None  # 保持激光雷达禁用
    # ...
```

### Q4: 传感器数据格式是什么？
**A**: 
- **深度相机**: `(num_envs, height=480, width=640, 1)` 的tensor，单位是米
- **激光雷达**: `(num_envs, num_rays)` 的tensor，包含距离测量值
- **IMU**: 角速度、线性加速度、姿态四元数

### Q5: 可以修改传感器参数吗？
**A**: 可以！在 `tasks/drone_racer/drone_racer_env_cfg.py` 中修改传感器配置：
```python
# 例如修改深度相机分辨率
depth_camera: TiledCameraCfg = TiledCameraCfg(
    # ...
    width=1280,  # 原来是640
    height=960,  # 原来是480
)

# 例如修改激光雷达通道数
lidar: RayCasterCfg = RayCasterCfg(
    # ...
    pattern_cfg=patterns.LidarPatternCfg(
        channels=32,  # 原来是16
        # ...
    ),
)
```

### Q6: Hello Kitty纹理可以恢复成原来的样子吗？
**A**: 当然可以！原始纹理已经被替换，但您可以创建自己的纹理图片，命名为 `bitmap.png` 并放在 `assets/gate/textures/` 目录下。

---

## 更多信息 / More Information

- **完整ROS文档**: `docs/ROS_INTEGRATION.md`
- **技术细节**: `docs/IMPROVEMENTS.md`
- **架构说明**: `docs/VISUAL_SUMMARY.md`
- **完成总结**: `docs/COMPLETION_SUMMARY.md`

---

## 示例代码总结

### 最简单的使用（保持原样，不使用新功能）
```bash
python3 scripts/rl/train.py --task Isaac-Drone-Racer-v0 --headless --num_envs 4096
```

### 使用ROS集成（推荐）
```bash
source /opt/ros/humble/setup.bash
python3 scripts/rl/play_with_ros.py --task Isaac-Drone-Racer-Play-v0 --num_envs 1
```

### 自定义传感器配置
查看 `scripts/rl/play_with_ros.py` 中的完整示例代码。

---

如有任何问题，请查看详细文档或提出issue！
