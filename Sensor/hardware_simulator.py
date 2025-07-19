#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬件模拟器
用于在没有实际硬件的情况下测试系统
"""

import logging
import threading
import time
import cv2
import numpy as np
from typing import Dict, Optional
from enum import Enum

# 添加路径以便导入核心系统
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Agent'))
from core_system import core_system, EventType, SystemEvent

logger = logging.getLogger(__name__)

class ButtonType(Enum):
    """按钮类型枚举"""
    PLACE_ITEM = "place_item"  # 绿色按钮 - 放入物品
    TAKE_ITEM = "take_item"    # 红色按钮 - 取出物品

class CameraType(Enum):
    """摄像头类型枚举"""
    INTERNAL = "internal"  # 内部摄像头 - 用于物品识别
    EXTERNAL = "external"  # 外部摄像头 - 用于人脸检测

class HardwareSimulator:
    """硬件模拟器"""
    
    def __init__(self):
        # 模拟摄像头
        self.cameras: Dict[CameraType, Optional[cv2.VideoCapture]] = {}
        self.face_cascade = None
        
        # 模拟按钮状态
        self.button_states = {
            ButtonType.PLACE_ITEM: False,
            ButtonType.TAKE_ITEM: False
        }
        
        # 防抖配置
        self.last_button_time = 0
        self.button_cooldown = 0.5  # 0.5秒冷却时间
        self.last_face_detection_time = 0
        self.face_detection_cooldown = 3.0  # 3秒冷却时间
        
        # 人脸检测参数
        self.REFERENCE_FACE_WIDTH = 150  # 像素
        self.REFERENCE_DISTANCE = 50  # 厘米
        self.DETECTION_DISTANCE = 50  # 检测距离阈值
        
        # 运行状态
        self.running = False
        self.face_detection_thread = None
        self.button_simulation_thread = None
        
        # 初始化模拟硬件
        self._init_simulated_cameras()
        self._init_face_detection()
        self._init_button_simulation()
    
    def _init_simulated_cameras(self):
        """初始化模拟摄像头"""
        try:
            # 尝试初始化内部摄像头
            internal_cam = cv2.VideoCapture(0)
            if internal_cam.isOpened():
                internal_cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cameras[CameraType.INTERNAL] = internal_cam
                logger.info("✅ 内部摄像头模拟器初始化成功")
            else:
                logger.warning("⚠️ 无法访问真实摄像头，将使用模拟图像")
                self.cameras[CameraType.INTERNAL] = None
            
            # 模拟外部摄像头（使用内部摄像头或生成模拟图像）
            if self.cameras[CameraType.INTERNAL]:
                self.cameras[CameraType.EXTERNAL] = self.cameras[CameraType.INTERNAL]
                logger.info("✅ 外部摄像头模拟器初始化成功")
            else:
                self.cameras[CameraType.EXTERNAL] = None
                
        except Exception as e:
            logger.error(f"摄像头模拟器初始化失败: {e}")
    
    def _init_face_detection(self):
        """初始化人脸检测"""
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if self.face_cascade.empty():
                logger.warning("无法加载人脸检测器，将使用模拟检测")
                self.face_cascade = None
            else:
                logger.info("✅ 人脸检测器初始化成功")
        except Exception as e:
            logger.error(f"人脸检测器初始化失败: {e}")
            self.face_cascade = None
    
    def _init_button_simulation(self):
        """初始化按钮模拟"""
        logger.info("✅ 按钮模拟器初始化成功")
        logger.info("📝 模拟按钮操作:")
        logger.info("   - 按 'p' 键模拟放入物品按钮")
        logger.info("   - 按 't' 键模拟取出物品按钮")
        logger.info("   - 按 'f' 键模拟人脸检测事件")
        logger.info("   - 按 'q' 键退出模拟器")
    
    def simulate_button_press(self, button_type: ButtonType):
        """模拟按钮按下"""
        current_time = time.time()
        
        # 防抖检查
        if current_time - self.last_button_time < self.button_cooldown:
            logger.warning(f"按钮模拟被忽略 - 冷却时间未到")
            return
        
        self.last_button_time = current_time
        logger.info(f"🔘 模拟按钮按下: {button_type.value}")
        
        # 发送按钮事件
        event = core_system.create_event(
            EventType.BUTTON_PRESS,
            "hardware_simulator",
            {"button_type": button_type.value},
            priority=1
        )
        core_system.emit_event(event)
    
    def simulate_face_detection(self):
        """模拟人脸检测事件"""
        current_time = time.time()
        
        # 防抖检查
        if current_time - self.last_face_detection_time < self.face_detection_cooldown:
            logger.warning(f"人脸检测模拟被忽略 - 冷却时间未到")
            return
        
        self.last_face_detection_time = current_time
        logger.info("👤 模拟人脸检测事件")
        
        # 发送接近传感器事件
        event = core_system.create_event(
            EventType.PROXIMITY_SENSOR,
            "hardware_simulator",
            {"detected": True, "distance": "near"},
            priority=2
        )
        core_system.emit_event(event)
    
    def capture_image(self, camera_type: CameraType = CameraType.INTERNAL) -> Optional[str]:
        """拍照并保存图片"""
        try:
            camera = self.cameras.get(camera_type)
            
            if camera is None:
                # 生成模拟图像
                logger.info("📸 生成模拟图像")
                image_path = self._generate_mock_image(camera_type)
            else:
                # 使用真实摄像头
                logger.info(f"📸 使用真实摄像头拍照")
                
                # 清空摄像头缓冲区，确保获取最新帧
                for _ in range(5):
                    camera.grab()
                
                ret, frame = camera.read()
                if not ret:
                    logger.error("无法读取摄像头帧")
                    return None
                
                # 生成唯一文件名
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"captured_{camera_type.value}_{timestamp}.jpg"
                filepath = os.path.join("uploads", filename)
                
                # 确保uploads目录存在
                os.makedirs("uploads", exist_ok=True)
                
                # 保存图片
                cv2.imwrite(filepath, frame)
                image_path = filepath
            
            logger.info(f"📸 拍照成功: {image_path}")
            
            # 发送拍照事件
            event = core_system.create_event(
                EventType.CAMERA_CAPTURE,
                "hardware_simulator",
                {
                    "camera_type": camera_type.value,
                    "image_path": image_path,
                    "image_size": (640, 480)  # 模拟尺寸
                }
            )
            core_system.emit_event(event)
            
            return image_path
            
        except Exception as e:
            logger.error(f"拍照失败: {e}")
            return None
    
    def _generate_mock_image(self, camera_type: CameraType) -> str:
        """生成模拟图像"""
        try:
            # 创建模拟图像
            if camera_type == CameraType.INTERNAL:
                # 内部摄像头 - 生成食物图像
                image = np.zeros((480, 640, 3), dtype=np.uint8)
                # 添加一些模拟的食物形状
                cv2.circle(image, (320, 240), 100, (0, 255, 0), -1)  # 绿色圆形
                cv2.putText(image, "FOOD", (280, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
            else:
                # 外部摄像头 - 生成人脸图像
                image = np.zeros((480, 640, 3), dtype=np.uint8)
                # 添加模拟的人脸形状
                cv2.ellipse(image, (320, 240), (80, 100), 0, 0, 360, (255, 200, 150), -1)
                cv2.circle(image, (300, 200), 10, (255, 255, 255), -1)  # 左眼
                cv2.circle(image, (340, 200), 10, (255, 255, 255), -1)  # 右眼
                cv2.putText(image, "FACE", (280, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # 生成文件名并保存
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"mock_{camera_type.value}_{timestamp}.jpg"
            filepath = os.path.join("uploads", filename)
            
            # 确保uploads目录存在
            os.makedirs("uploads", exist_ok=True)
            
            # 保存图像
            cv2.imwrite(filepath, image)
            
            return filepath
            
        except Exception as e:
            logger.error(f"生成模拟图像失败: {e}")
            return None
    
    def detect_faces(self) -> bool:
        """检测人脸（模拟）"""
        # 模拟人脸检测，随机返回结果
        import random
        return random.random() < 0.3  # 30%概率检测到人脸
    
    def start_face_detection_monitor(self):
        """启动人脸检测监控（模拟）"""
        if self.face_detection_thread and self.face_detection_thread.is_alive():
            logger.warning("人脸检测监控已在运行")
            return
        
        self.running = True
        self.face_detection_thread = threading.Thread(target=self._face_detection_loop, daemon=True)
        self.face_detection_thread.start()
        logger.info("✅ 人脸检测监控模拟器已启动")
    
    def stop_face_detection_monitor(self):
        """停止人脸检测监控"""
        self.running = False
        if self.face_detection_thread:
            self.face_detection_thread.join(timeout=2)
        logger.info("✅ 人脸检测监控模拟器已停止")
    
    def _face_detection_loop(self):
        """人脸检测循环（模拟）"""
        while self.running:
            try:
                # 模拟人脸检测
                if self.detect_faces():
                    current_time = time.time()
                    
                    # 防抖检查
                    if current_time - self.last_face_detection_time >= self.face_detection_cooldown:
                        self.last_face_detection_time = current_time
                        logger.info("👤 模拟检测到人脸接近")
                        
                        # 发送接近传感器事件
                        event = core_system.create_event(
                            EventType.PROXIMITY_SENSOR,
                            "hardware_simulator",
                            {"detected": True, "distance": "near"},
                            priority=2
                        )
                        core_system.emit_event(event)
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                logger.error(f"人脸检测模拟循环出错: {e}")
                time.sleep(10)
    
    def start_button_simulation(self):
        """启动按钮模拟"""
        if self.button_simulation_thread and self.button_simulation_thread.is_alive():
            logger.warning("按钮模拟已在运行")
            return
        
        self.running = True
        self.button_simulation_thread = threading.Thread(target=self._button_simulation_loop, daemon=True)
        self.button_simulation_thread.start()
        logger.info("✅ 按钮模拟器已启动")
    
    def _button_simulation_loop(self):
        """按钮模拟循环"""
        logger.info("🎮 按钮模拟器已启动，等待键盘输入...")
        logger.info("按键说明:")
        logger.info("  p - 模拟放入物品按钮")
        logger.info("  t - 模拟取出物品按钮")
        logger.info("  f - 模拟人脸检测事件")
        logger.info("  q - 退出模拟器")
        
        while self.running:
            try:
                # 这里可以添加键盘监听逻辑
                # 为了简化，我们使用简单的输入
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"按钮模拟循环出错: {e}")
                time.sleep(1)
    
    def get_camera_status(self) -> Dict:
        """获取摄像头状态"""
        status = {}
        for camera_type, camera in self.cameras.items():
            status[camera_type.value] = {
                "available": camera is not None and camera.isOpened(),
                "simulated": camera is None,
                "index": camera.get(cv2.CAP_PROP_POS_FRAMES) if camera else None
            }
        return status
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止监控
            self.stop_face_detection_monitor()
            
            # 释放摄像头
            for camera in self.cameras.values():
                if camera:
                    camera.release()
            
            logger.info("✅ 硬件模拟器资源清理完成")
        except Exception as e:
            logger.error(f"硬件模拟器资源清理失败: {e}")

# 全局硬件模拟器实例
hardware_simulator = HardwareSimulator()

def main():
    """主函数 - 用于测试硬件模拟器"""
    try:
        logger.info("🚀 启动硬件模拟器...")
        
        # 启动人脸检测监控
        hardware_simulator.start_face_detection_monitor()
        
        # 启动按钮模拟
        hardware_simulator.start_button_simulation()
        
        logger.info("✅ 硬件模拟器已启动")
        logger.info("📝 使用以下命令测试:")
        logger.info("  - 模拟放入物品: hardware_simulator.simulate_button_press(ButtonType.PLACE_ITEM)")
        logger.info("  - 模拟取出物品: hardware_simulator.simulate_button_press(ButtonType.TAKE_ITEM)")
        logger.info("  - 模拟人脸检测: hardware_simulator.simulate_face_detection()")
        
        # 保持运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭模拟器...")
        finally:
            hardware_simulator.cleanup()
            
    except Exception as e:
        logger.error(f"硬件模拟器运行出错: {e}")

if __name__ == "__main__":
    main() 