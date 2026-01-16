#!/usr/bin/env python3
# Copyright (c) 2025, Kousheek Chakraborty
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# This project uses the IsaacLab framework (https://github.com/isaac-sim/IsaacLab),
# which is licensed under the BSD-3-Clause License.

"""
Play trained policy with ROS bridge enabled.

This script demonstrates how to run a trained drone racing policy while
publishing sensor data to ROS 2 topics for integration with ROS-based systems.

Usage:
    python scripts/rl/play_with_ros.py --task Isaac-Drone-Racer-Play-v0 --num_envs 1

Requirements:
    - ROS 2 (Humble or newer)
    - rclpy, sensor_msgs, std_msgs: pip install rclpy sensor_msgs std_msgs
    - Source ROS 2: source /opt/ros/humble/setup.bash
"""

import argparse

from isaaclab.app import AppLauncher

# Create arg parser
parser = argparse.ArgumentParser(description="Play drone racing policy with ROS bridge")
parser.add_argument("--cpu", action="store_true", default=False, help="Use CPU pipeline.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default="Isaac-Drone-Racer-Play-v0", help="Name of the task.")
parser.add_argument("--publish_rate", type=int, default=30, help="ROS publishing rate in Hz.")
parser.add_argument("--disable_ros", action="store_true", default=False, help="Disable ROS bridge.")
args_cli = parser.parse_args()

# Launch Isaac Sim app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# Import modules after app launch
import gymnasium as gym
import torch

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils.parse_cfg import parse_env_cfg

from tasks.drone_racer.ros_bridge import create_ros_bridge


def main():
    """Main function to run the trained policy with ROS bridge."""
    
    # Parse configuration
    env_cfg = parse_env_cfg(args_cli.task, use_gpu=not args_cli.cpu, num_envs=args_cli.num_envs)
    
    # Enable sensors for ROS publishing
    # Store reference to scene configuration before post_init modifies it
    scene_sensors = {
        'imu': env_cfg.scene.imu if hasattr(env_cfg.scene, 'imu') else None,
        'depth_camera': env_cfg.scene.depth_camera if hasattr(env_cfg.scene, 'depth_camera') else None,
        'lidar': env_cfg.scene.lidar if hasattr(env_cfg.scene, 'lidar') else None,
        'tiled_camera': env_cfg.scene.tiled_camera if hasattr(env_cfg.scene, 'tiled_camera') else None,
    }
    
    # Override the post_init to keep sensors enabled
    original_post_init = type(env_cfg).__post_init__
    
    def enabled_sensors_post_init(self):
        """Modified post_init that keeps sensors enabled."""
        # Call original post_init with self
        original_post_init(self)
        
        # Re-enable sensors that were disabled in original post_init
        for sensor_name, sensor_cfg in scene_sensors.items():
            if sensor_cfg is not None and hasattr(self.scene, sensor_name):
                setattr(self.scene, sensor_name, sensor_cfg)
    
    # Replace the post_init method with bound method
    type(env_cfg).__post_init__ = enabled_sensors_post_init
    
    # Re-initialize to apply sensor changes
    env_cfg.__post_init__()
    
    # Create environment
    print(f"[INFO] Creating environment: {args_cli.task}")
    env = gym.make(args_cli.task, cfg=env_cfg)
    
    # Initialize ROS bridge
    ros_bridge = None
    if not args_cli.disable_ros:
        print("[INFO] Initializing ROS bridge...")
        ros_bridge = create_ros_bridge(env, publish_rate=args_cli.publish_rate)
        if ros_bridge:
            print(f"[INFO] ROS bridge initialized at {args_cli.publish_rate} Hz")
        else:
            print("[WARN] ROS bridge not available. Running without ROS.")
    else:
        print("[INFO] ROS bridge disabled by user.")
    
    # Reset environment
    obs, _ = env.reset()
    
    # Simulation loop
    print("[INFO] Starting simulation loop...")
    try:
        while simulation_app.is_running():
            with torch.inference_mode():
                # Sample random action (replace with your trained policy)
                # For trained policy: action = policy.predict(obs)
                action = torch.randn_like(env.action_space.sample())
                
                # Step environment
                obs, reward, terminated, truncated, info = env.step(action)
                
                # Publish sensor data to ROS
                if ros_bridge is not None:
                    # Publish data from first environment
                    ros_bridge.publish_all(env_idx=0)
                    ros_bridge.spin_once()
                
                # Reset environment if done
                if terminated.any() or truncated.any():
                    obs, _ = env.reset()
    
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
    
    finally:
        # Cleanup
        if ros_bridge is not None:
            print("[INFO] Shutting down ROS bridge...")
            ros_bridge.shutdown()
        
        env.close()
        print("[INFO] Simulation closed.")


if __name__ == "__main__":
    main()
    simulation_app.close()
