# Copyright (c) 2025, Kousheek Chakraborty
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# This project uses the IsaacLab framework (https://github.com/isaac-sim/IsaacLab),
# which is licensed under the BSD-3-Clause License.

"""
Unit tests for sensor observation functions.

These tests verify that sensor observation functions have correct signatures
and return types without requiring a full Isaac Sim environment.
"""

import pytest
import torch
from unittest.mock import Mock, MagicMock

from tasks.drone_racer.mdp.observations import (
    depth_image,
    lidar_distance,
    imu_ang_vel,
    imu_lin_acc,
    imu_orientation,
    image,
)


@pytest.fixture
def mock_env():
    """Create a mock environment with sensor data."""
    env = Mock()
    env.num_envs = 2
    
    # Mock depth camera
    depth_camera = Mock()
    depth_camera.data.output = {
        "distance_to_camera": torch.rand(2, 480, 640, 1)
    }
    
    # Mock lidar
    lidar = Mock()
    lidar.data.ray_distance = torch.rand(2, 360)
    
    # Mock IMU
    imu = Mock()
    imu.data.ang_vel_b = torch.rand(2, 3)
    imu.data.lin_acc_b = torch.rand(2, 3)
    imu.data.quat_w = torch.rand(2, 4)
    
    # Mock RGB camera
    camera = Mock()
    camera.data.output = {
        "rgb": torch.rand(2, 1000, 1000, 3)
    }
    
    # Mock scene sensors
    env.scene.sensors = {
        "depth_camera": depth_camera,
        "lidar": lidar,
        "imu": imu,
        "tiled_camera": camera,
    }
    
    return env


def test_depth_image_returns_correct_shape(mock_env):
    """Test that depth_image returns tensor with correct shape."""
    from isaaclab.managers import SceneEntityCfg
    
    result = depth_image(mock_env, sensor_cfg=SceneEntityCfg("depth_camera"))
    
    assert isinstance(result, torch.Tensor)
    assert result.shape == (2, 480, 640, 1)


def test_lidar_distance_returns_correct_shape(mock_env):
    """Test that lidar_distance returns tensor with correct shape."""
    from isaaclab.managers import SceneEntityCfg
    
    result = lidar_distance(mock_env, sensor_cfg=SceneEntityCfg("lidar"))
    
    assert isinstance(result, torch.Tensor)
    assert result.shape == (2, 360)


def test_imu_ang_vel_returns_correct_shape(mock_env):
    """Test that imu_ang_vel returns tensor with correct shape."""
    from isaaclab.managers import SceneEntityCfg
    
    result = imu_ang_vel(mock_env, sensor_cfg=SceneEntityCfg("imu"))
    
    assert isinstance(result, torch.Tensor)
    assert result.shape == (2, 3)


def test_imu_lin_acc_returns_correct_shape(mock_env):
    """Test that imu_lin_acc returns tensor with correct shape."""
    from isaaclab.managers import SceneEntityCfg
    
    result = imu_lin_acc(mock_env, sensor_cfg=SceneEntityCfg("imu"))
    
    assert isinstance(result, torch.Tensor)
    assert result.shape == (2, 3)


def test_imu_orientation_returns_correct_shape(mock_env):
    """Test that imu_orientation returns tensor with correct shape."""
    from isaaclab.managers import SceneEntityCfg
    
    result = imu_orientation(mock_env, sensor_cfg=SceneEntityCfg("imu"))
    
    assert isinstance(result, torch.Tensor)
    assert result.shape == (2, 4)


def test_image_returns_correct_shape(mock_env):
    """Test that image returns tensor with correct shape."""
    from isaaclab.managers import SceneEntityCfg
    
    result = image(mock_env, sensor_cfg=SceneEntityCfg("tiled_camera"))
    
    assert isinstance(result, torch.Tensor)
    assert result.shape == (2, 1000, 1000, 3)


def test_all_functions_handle_default_sensor_cfg(mock_env):
    """Test that all functions work with default sensor configurations."""
    # This test verifies that the default SceneEntityCfg arguments work
    # We don't test actual functionality since that requires Isaac Sim
    
    functions_to_test = [
        (depth_image, "depth_camera"),
        (lidar_distance, "lidar"),
        (imu_ang_vel, "imu"),
        (imu_lin_acc, "imu"),
        (imu_orientation, "imu"),
        (image, "tiled_camera"),
    ]
    
    for func, sensor_name in functions_to_test:
        # Verify function is callable and returns a tensor
        result = func(mock_env)
        assert isinstance(result, torch.Tensor), f"{func.__name__} should return a Tensor"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
