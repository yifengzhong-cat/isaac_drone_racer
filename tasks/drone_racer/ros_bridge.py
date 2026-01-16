# Copyright (c) 2025, Kousheek Chakraborty
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# This project uses the IsaacLab framework (https://github.com/isaac-sim/IsaacLab),
# which is licensed under the BSD-3-Clause License.

"""
ROS Bridge for publishing sensor data from Isaac Drone Racer to ROS topics.

This module provides a bridge to publish IMU, depth camera, and lidar data
to ROS topics for integration with ROS-based navigation and perception systems.

Requirements:
    - rclpy (ROS 2 Python client library)
    - sensor_msgs
    - std_msgs
    
To use this bridge:
    1. Install ROS 2 (Humble or newer recommended)
    2. Source your ROS 2 installation: source /opt/ros/humble/setup.bash
    3. Install Python ROS packages: pip install rclpy sensor_msgs std_msgs
    4. Enable sensors in your environment configuration
    5. Initialize the bridge with your environment
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image, Imu, LaserScan, PointCloud2, PointField
    from std_msgs.msg import Header
    
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False
    print("Warning: ROS 2 packages not available. Install rclpy and sensor_msgs to use ROS bridge.")

if TYPE_CHECKING:
    from isaaclab.envs import ManagerBasedRLEnv


class DroneRacerROSBridge:
    """ROS Bridge for publishing drone sensor data.
    
    This class creates ROS publishers for:
    - IMU data (/drone/imu)
    - Depth camera images (/drone/depth/image_raw)
    - Lidar point cloud (/drone/scan)
    - RGB camera images (/drone/camera/image_raw)
    
    Args:
        env: The Isaac Lab environment instance
        node_name: Name for the ROS node (default: "isaac_drone_racer_bridge")
        publish_rate: Rate at which to publish sensor data in Hz (default: 30)
    """
    
    def __init__(self, env: ManagerBasedRLEnv, node_name: str = "isaac_drone_racer_bridge", publish_rate: int = 30):
        if not ROS_AVAILABLE:
            raise ImportError(
                "ROS 2 packages not available. Please install:\n"
                "  pip install rclpy sensor_msgs std_msgs\n"
                "Or install ROS 2 from: https://docs.ros.org/en/humble/Installation.html"
            )
        
        self.env = env
        self.publish_rate = publish_rate
        
        # Initialize ROS node
        if not rclpy.ok():
            rclpy.init()
        
        self.node = Node(node_name)
        
        # Create publishers
        self.imu_pub = self.node.create_publisher(Imu, '/drone/imu', 10)
        self.depth_pub = self.node.create_publisher(Image, '/drone/depth/image_raw', 10)
        self.lidar_pub = self.node.create_publisher(LaserScan, '/drone/scan', 10)
        self.camera_pub = self.node.create_publisher(Image, '/drone/camera/image_raw', 10)
        
        self.node.get_logger().info(f"Isaac Drone Racer ROS Bridge initialized at {publish_rate} Hz")
        self.node.get_logger().info("Publishing topics:")
        self.node.get_logger().info("  - /drone/imu (sensor_msgs/Imu)")
        self.node.get_logger().info("  - /drone/depth/image_raw (sensor_msgs/Image)")
        self.node.get_logger().info("  - /drone/scan (sensor_msgs/LaserScan)")
        self.node.get_logger().info("  - /drone/camera/image_raw (sensor_msgs/Image)")
    
    def publish_imu(self, env_idx: int = 0) -> None:
        """Publish IMU data for a specific environment.
        
        Args:
            env_idx: Index of the environment to publish data from (default: 0)
        """
        if "imu" not in self.env.scene.sensors:
            return
        
        imu_sensor = self.env.scene.sensors["imu"]
        
        msg = Imu()
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = "drone_imu"
        
        # Angular velocity
        ang_vel = imu_sensor.data.ang_vel_b[env_idx].cpu().numpy()
        msg.angular_velocity.x = float(ang_vel[0])
        msg.angular_velocity.y = float(ang_vel[1])
        msg.angular_velocity.z = float(ang_vel[2])
        
        # Linear acceleration
        lin_acc = imu_sensor.data.lin_acc_b[env_idx].cpu().numpy()
        msg.linear_acceleration.x = float(lin_acc[0])
        msg.linear_acceleration.y = float(lin_acc[1])
        msg.linear_acceleration.z = float(lin_acc[2])
        
        # Orientation
        quat = imu_sensor.data.quat_w[env_idx].cpu().numpy()
        msg.orientation.w = float(quat[0])
        msg.orientation.x = float(quat[1])
        msg.orientation.y = float(quat[2])
        msg.orientation.z = float(quat[3])
        
        self.imu_pub.publish(msg)
    
    def publish_depth_image(self, env_idx: int = 0) -> None:
        """Publish depth camera image for a specific environment.
        
        Args:
            env_idx: Index of the environment to publish data from (default: 0)
        """
        if "depth_camera" not in self.env.scene.sensors:
            return
        
        depth_camera = self.env.scene.sensors["depth_camera"]
        
        msg = Image()
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = "drone_depth_camera"
        
        # Get depth image (distance_to_camera) - shape is (num_envs, height, width, 1)
        depth_data = depth_camera.data.output["distance_to_camera"][env_idx].cpu().numpy()
        
        # Remove the channel dimension if present (height, width, 1) -> (height, width)
        if depth_data.ndim == 3 and depth_data.shape[2] == 1:
            depth_data = depth_data.squeeze(axis=2)
        
        msg.height = depth_data.shape[0]
        msg.width = depth_data.shape[1]
        msg.encoding = "32FC1"  # 32-bit float, single channel
        msg.is_bigendian = 0
        msg.step = msg.width * 4  # 4 bytes per pixel (float32)
        
        # Convert to bytes (flatten for proper image format)
        msg.data = depth_data.astype(np.float32).tobytes()
        
        self.depth_pub.publish(msg)
    
    def publish_lidar_scan(self, env_idx: int = 0) -> None:
        """Publish lidar scan data for a specific environment.
        
        Args:
            env_idx: Index of the environment to publish data from (default: 0)
        """
        if "lidar" not in self.env.scene.sensors:
            return
        
        lidar_sensor = self.env.scene.sensors["lidar"]
        
        msg = LaserScan()
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = "drone_lidar"
        
        # Get range data as numpy array
        ranges = lidar_sensor.data.ray_distance[env_idx].cpu().numpy()
        
        # Configure scan parameters (assumes horizontal 360-degree scan)
        msg.angle_min = -np.pi
        msg.angle_max = np.pi
        msg.angle_increment = 2 * np.pi / len(ranges)
        msg.time_increment = 0.0
        msg.scan_time = 1.0 / self.publish_rate
        msg.range_min = 0.1
        msg.range_max = 20.0
        
        # Pass numpy array directly (ROS accepts it efficiently)
        msg.ranges = ranges.astype(np.float64).tolist()
        
        self.lidar_pub.publish(msg)
    
    def publish_camera_image(self, env_idx: int = 0) -> None:
        """Publish RGB camera image for a specific environment.
        
        Args:
            env_idx: Index of the environment to publish data from (default: 0)
        """
        if "tiled_camera" not in self.env.scene.sensors:
            return
        
        camera = self.env.scene.sensors["tiled_camera"]
        
        msg = Image()
        msg.header = Header()
        msg.header.stamp = self.node.get_clock().now().to_msg()
        msg.header.frame_id = "drone_camera"
        
        # Get RGB image
        rgb_data = camera.data.output["rgb"][env_idx].cpu().numpy()
        
        msg.height = rgb_data.shape[0]
        msg.width = rgb_data.shape[1]
        msg.encoding = "rgb8"  # 8-bit RGB
        msg.is_bigendian = 0
        msg.step = msg.width * 3  # 3 bytes per pixel (RGB)
        
        # Convert to uint8 and bytes
        msg.data = (rgb_data * 255).astype(np.uint8).tobytes()
        
        self.camera_pub.publish(msg)
    
    def publish_all(self, env_idx: int = 0) -> None:
        """Publish all available sensor data for a specific environment.
        
        Args:
            env_idx: Index of the environment to publish data from (default: 0)
        """
        self.publish_imu(env_idx)
        self.publish_depth_image(env_idx)
        self.publish_lidar_scan(env_idx)
        self.publish_camera_image(env_idx)
    
    def spin_once(self) -> None:
        """Process ROS callbacks once."""
        rclpy.spin_once(self.node, timeout_sec=0)
    
    def shutdown(self) -> None:
        """Shutdown the ROS node."""
        self.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


def create_ros_bridge(env: ManagerBasedRLEnv, **kwargs) -> DroneRacerROSBridge | None:
    """Factory function to create a ROS bridge if ROS is available.
    
    Args:
        env: The Isaac Lab environment instance
        **kwargs: Additional arguments to pass to DroneRacerROSBridge
    
    Returns:
        DroneRacerROSBridge instance if ROS is available, None otherwise
    """
    if not ROS_AVAILABLE:
        print("ROS 2 not available. Skipping ROS bridge creation.")
        return None
    
    return DroneRacerROSBridge(env, **kwargs)
