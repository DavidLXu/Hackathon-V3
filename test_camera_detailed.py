#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细的摄像头测试脚本
"""

import cv2
import time
import os
import subprocess

def test_camera_with_backend(camera_index, backend=None):
    """使用指定后端测试摄像头"""
    print(f"测试摄像头索引: {camera_index}, 后端: {backend}")
    
    try:
        if backend:
            # 使用指定的后端
            cap = cv2.VideoCapture(camera_index, backend)
        else:
            # 使用默认后端
            cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print(f"❌ 摄像头 {camera_index} 无法打开")
            return False
        
        print(f"✅ 摄像头 {camera_index} 已打开")
        
        # 尝试读取一帧
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print(f"❌ 摄像头 {camera_index} 无法读取帧")
            cap.release()
            return False
        
        print(f"✅ 摄像头 {camera_index} 可以读取帧 (尺寸: {frame.shape})")
        
        # 保存测试图片
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backend_name = backend.__name__ if backend else "default"
        filename = f"test_camera_{camera_index}_{backend_name}_{timestamp}.jpg"
        filepath = os.path.join("uploads", filename)
        
        # 确保uploads目录存在
        os.makedirs("uploads", exist_ok=True)
        
        # 保存图片
        success = cv2.imwrite(filepath, frame)
        
        if success:
            print(f"✅ 测试图片已保存: {filepath}")
        else:
            print(f"❌ 保存测试图片失败")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ 摄像头 {camera_index} 测试失败: {e}")
        return False

def test_v4l2_devices():
    """测试v4l2设备"""
    print("\n🔍 检查v4l2设备...")
    
    try:
        # 运行v4l2-ctl命令
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("v4l2设备列表:")
            print(result.stdout)
        else:
            print("无法获取v4l2设备列表")
            
    except Exception as e:
        print(f"v4l2设备检查失败: {e}")

def test_camera_with_different_backends(camera_index):
    """使用不同后端测试摄像头"""
    print(f"\n🔍 使用不同后端测试摄像头 {camera_index}...")
    
    backends = [
        None,  # 默认后端
        cv2.CAP_V4L2,  # V4L2后端
        cv2.CAP_V4L,   # V4L后端
        cv2.CAP_ANY,   # 自动选择后端
    ]
    
    working_backends = []
    
    for backend in backends:
        if test_camera_with_backend(camera_index, backend):
            working_backends.append(backend)
        print("-" * 50)
    
    return working_backends

def main():
    """主函数"""
    print("🔍 开始详细摄像头测试...")
    
    # 检查v4l2设备
    test_v4l2_devices()
    
    # 测试多个摄像头索引
    camera_indices = [0, 1, 2, 3, 4, 5, 6, 7]
    working_cameras = {}
    
    for idx in camera_indices:
        working_backends = test_camera_with_different_backends(idx)
        if working_backends:
            working_cameras[idx] = working_backends
    
    print(f"\n📊 测试结果:")
    for idx, backends in working_cameras.items():
        print(f"摄像头 {idx}: 可用后端 {backends}")
    
    if working_cameras:
        print("✅ 找到可用的摄像头")
        return working_cameras
    else:
        print("❌ 没有找到可用的摄像头")
        return {}

if __name__ == "__main__":
    main() 