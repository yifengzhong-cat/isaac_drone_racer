# ROS Integration Guide

This guide explains how to use the ROS bridge to integrate Isaac Drone Racer with ROS 2 for sensor data publishing.

## Overview

The ROS bridge enables real-time publishing of sensor data from the Isaac Drone Racer simulation to ROS 2 topics, allowing integration with ROS-based navigation, perception, and control systems.

## Supported Sensors

The following sensors are integrated with ROS:

| Sensor | ROS Topic | Message Type | Description |
|--------|-----------|--------------|-------------|
| IMU | `/drone/imu` | `sensor_msgs/Imu` | Orientation, angular velocity, linear acceleration |
| Depth Camera | `/drone/depth/image_raw` | `sensor_msgs/Image` | Depth image with distance values |
| Lidar | `/drone/scan` | `sensor_msgs/LaserScan` | 360-degree laser scan data |
| RGB Camera | `/drone/camera/image_raw` | `sensor_msgs/Image` | RGB fisheye camera image |

## Prerequisites

### 1. Install ROS 2

Follow the official ROS 2 installation guide for your platform:
- Ubuntu: https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html
- Other platforms: https://docs.ros.org/en/humble/Installation.html

Recommended version: **ROS 2 Humble** or newer

### 2. Install Python ROS Packages

```bash
pip install rclpy sensor_msgs std_msgs
```

### 3. Source ROS 2 Environment

```bash
source /opt/ros/humble/setup.bash
```

## Usage

### Basic Usage

1. **Enable Sensors in Environment Configuration**

To use ROS bridge, enable sensors in your configuration. You can override the post_init method or create a custom configuration.

2. **Create and Use the ROS Bridge**

```python
from tasks.drone_racer.ros_bridge import create_ros_bridge

# Create environment
env = gym.make("Isaac-Drone-Racer-v0", cfg=env_cfg)

# Initialize ROS bridge
ros_bridge = create_ros_bridge(env, publish_rate=30)

if ros_bridge is not None:
    # In your main loop
    while simulation_running:
        obs, reward, done, info = env.step(action)
        ros_bridge.publish_all(env_idx=0)
        ros_bridge.spin_once()
    
    # Cleanup
    ros_bridge.shutdown()
```

### Advanced Usage

#### Publishing Specific Sensors

```python
ros_bridge.publish_imu(env_idx=0)
ros_bridge.publish_depth_image(env_idx=0)
ros_bridge.publish_lidar_scan(env_idx=0)
ros_bridge.publish_camera_image(env_idx=0)
```

## Visualizing with RViz

1. Start the simulation with ROS bridge
2. Launch RViz: `rviz2`
3. Add visualizations for topics: `/drone/imu`, `/drone/depth/image_raw`, `/drone/scan`, `/drone/camera/image_raw`

## Configuration

Sensor parameters can be configured in `tasks/drone_racer/drone_racer_env_cfg.py`:

- Depth camera: resolution, clipping range, focal length
- Lidar: channels, FOV, resolution, max distance
- IMU: sensor placement and frame

## Troubleshooting

- **ROS Not Available**: Ensure ROS 2 is installed and sourced
- **No Data Published**: Check that sensors are enabled in configuration
- **Frame Errors**: Bridge publishes data but not transforms; add static transforms if needed

## License

BSD-3-Clause License (same as Isaac Drone Racer project)
