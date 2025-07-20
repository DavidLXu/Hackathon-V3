#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头测试脚本
"""

import cv2
import time
import os

def test_camera(camera_index):
    """测试指定索引的摄像头"""
    print(f"测试摄像头索引: {camera_index}")
    
    try:
        # 尝试打开摄像头
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
        filename = f"test_camera_{camera_index}_{timestamp}.jpg"
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

def main():
    """主函数"""
    print("🔍 开始摄像头测试...")
    
    # 测试多个摄像头索引
    camera_indices = [0, 1, 2, 3, 4, 5, 6, 7]
    working_cameras = []
    
    for idx in camera_indices:
        if test_camera(idx):
            working_cameras.append(idx)
        print("-" * 50)
    
    print(f"\n📊 测试结果:")
    print(f"可用的摄像头索引: {working_cameras}")
    
    if working_cameras:
        print("✅ 找到可用的摄像头")
    else:
        print("❌ 没有找到可用的摄像头")

if __name__ == "__main__":
    main() 