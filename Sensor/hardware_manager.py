#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬件管理器
统一管理所有外设：按钮、摄像头等
"""

import logging
import threading
import time
import cv2
import RPi.GPIO as GPIO
from typing import Dict, Optional, Callable
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

class HardwareManager:
    """硬件管理器"""
    
    def __init__(self):
        # GPIO配置
        self.GPIO_16 = 16  # 绿色按键 - 放入物品
        self.GPIO_17 = 17  # 红色按键 - 取出物品
        
        # 摄像头配置
        self.cameras: Dict[CameraType, Optional[cv2.VideoCapture]] = {}
        self.face_cascade = None
        
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
        
        # 初始化硬件
        self._init_gpio()
        self._init_cameras()
        self._init_face_detection()
    
    def _init_gpio(self):
        """初始化GPIO"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.GPIO_16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.GPIO_17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            
            # 设置事件检测
            GPIO.add_event_detect(self.GPIO_16, GPIO.RISING, callback=self._button16_callback, bouncetime=200)
            GPIO.add_event_detect(self.GPIO_17, GPIO.RISING, callback=self._button17_callback, bouncetime=200)
            
            logger.info("GPIO初始化成功")
        except Exception as e:
            logger.error(f"GPIO初始化失败: {e}")
    
    def _init_cameras(self):
        """初始化摄像头"""
        try:
            # 初始化内部摄像头（用于物品识别）
            internal_cam = cv2.VideoCapture(0)
            if internal_cam.isOpened():
                internal_cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cameras[CameraType.INTERNAL] = internal_cam
                logger.info("内部摄像头初始化成功")
            else:
                logger.warning("内部摄像头初始化失败")
                self.cameras[CameraType.INTERNAL] = None
            
            # 初始化外部摄像头（用于人脸检测）
            external_cam = cv2.VideoCapture(1)  # 尝试第二个摄像头
            if external_cam.isOpened():
                external_cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cameras[CameraType.EXTERNAL] = external_cam
                logger.info("外部摄像头初始化成功")
            else:
                # 如果外部摄像头不可用，使用内部摄像头进行人脸检测
                logger.warning("外部摄像头不可用，将使用内部摄像头进行人脸检测")
                self.cameras[CameraType.EXTERNAL] = self.cameras[CameraType.INTERNAL]
                
        except Exception as e:
            logger.error(f"摄像头初始化失败: {e}")
    
    def _init_face_detection(self):
        """初始化人脸检测"""
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            if self.face_cascade.empty():
                logger.warning("无法加载人脸检测器")
                self.face_cascade = None
            else:
                logger.info("人脸检测器初始化成功")
        except Exception as e:
            logger.error(f"人脸检测器初始化失败: {e}")
            self.face_cascade = None
    
    def _button16_callback(self, channel):
        """GPIO16按键回调函数 - 放入物品"""
        current_time = time.time()
        
        # 防抖检查
        if current_time - self.last_button_time < self.button_cooldown:
            logger.warning(f"按键16被忽略 - 冷却时间未到")
            return
        
        self.last_button_time = current_time
        logger.info("按键16被按下 - 触发放入物品功能")
        
        # 发送按钮事件
        event = core_system.create_event(
            EventType.BUTTON_PRESS,
            "hardware_manager",
            {"button_type": ButtonType.PLACE_ITEM.value},
            priority=1
        )
        core_system.emit_event(event)
    
    def _button17_callback(self, channel):
        """GPIO17按键回调函数 - 取出物品"""
        current_time = time.time()
        
        # 防抖检查
        if current_time - self.last_button_time < self.button_cooldown:
            logger.warning(f"按键17被忽略 - 冷却时间未到")
            return
        
        self.last_button_time = current_time
        logger.info("按键17被按下 - 触发取出物品功能")
        
        # 发送按钮事件
        event = core_system.create_event(
            EventType.BUTTON_PRESS,
            "hardware_manager",
            {"button_type": ButtonType.TAKE_ITEM.value},
            priority=1
        )
        core_system.emit_event(event)
    
    def capture_image(self, camera_type: CameraType = CameraType.INTERNAL) -> Optional[str]:
        """拍照并保存图片"""
        try:
            camera = self.cameras.get(camera_type)
            if camera is None:
                logger.error(f"摄像头 {camera_type.value} 不可用")
                return None
            
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
            
            logger.info(f"拍照成功: {filepath}")
            
            # 发送拍照事件
            event = core_system.create_event(
                EventType.CAMERA_CAPTURE,
                "hardware_manager",
                {
                    "camera_type": camera_type.value,
                    "image_path": filepath,
                    "image_size": frame.shape
                }
            )
            core_system.emit_event(event)
            
            return filepath
            
        except Exception as e:
            logger.error(f"拍照失败: {e}")
            return None
    
    def estimate_distance(self, face_width: int) -> float:
        """根据人脸框宽度估算距离"""
        if face_width <= 0:
            return float('inf')
        distance = (self.REFERENCE_FACE_WIDTH * self.REFERENCE_DISTANCE) / face_width
        return distance
    
    def detect_faces(self) -> bool:
        """检测人脸并判断是否触发接近事件"""
        camera = self.cameras.get(CameraType.EXTERNAL)
        if camera is None or self.face_cascade is None:
            return False
        
        try:
            ret, frame = camera.read()
            if not ret:
                return False
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 检测人脸
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # 检查是否需要触发事件
            if len(faces) >= 1:
                for (x, y, w, h) in faces:
                    distance = self.estimate_distance(w)
                    if distance <= self.DETECTION_DISTANCE:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"人脸检测出错: {e}")
            return False
    
    def start_face_detection_monitor(self):
        """启动人脸检测监控"""
        if self.face_detection_thread and self.face_detection_thread.is_alive():
            logger.warning("人脸检测监控已在运行")
            return
        
        self.running = True
        self.face_detection_thread = threading.Thread(target=self._face_detection_loop, daemon=True)
        self.face_detection_thread.start()
        logger.info("人脸检测监控已启动")
    
    def stop_face_detection_monitor(self):
        """停止人脸检测监控"""
        self.running = False
        if self.face_detection_thread:
            self.face_detection_thread.join(timeout=2)
        logger.info("人脸检测监控已停止")
    
    def _face_detection_loop(self):
        """人脸检测循环"""
        while self.running:
            try:
                if self.detect_faces():
                    current_time = time.time()
                    
                    # 防抖检查
                    if current_time - self.last_face_detection_time >= self.face_detection_cooldown:
                        self.last_face_detection_time = current_time
                        logger.info("👤 检测到人脸接近 - 触发接近传感器事件")
                        
                        # 发送接近传感器事件
                        event = core_system.create_event(
                            EventType.PROXIMITY_SENSOR,
                            "hardware_manager",
                            {"detected": True, "distance": "near"},
                            priority=2
                        )
                        core_system.emit_event(event)
                
                time.sleep(0.1)  # 短暂休眠以减少CPU使用
                
            except Exception as e:
                logger.error(f"人脸检测循环出错: {e}")
                time.sleep(1)
    
    def get_camera_status(self) -> Dict:
        """获取摄像头状态"""
        status = {}
        for camera_type, camera in self.cameras.items():
            status[camera_type.value] = {
                "available": camera is not None and camera.isOpened(),
                "index": camera.get(cv2.CAP_PROP_POS_FRAMES) if camera else None
            }
        return status
    
    def cleanup(self):
        """清理硬件资源"""
        try:
            # 停止人脸检测
            self.stop_face_detection_monitor()
            
            # 释放摄像头
            for camera in self.cameras.values():
                if camera:
                    camera.release()
            
            # 清理GPIO
            GPIO.cleanup()
            
            logger.info("硬件资源清理完成")
        except Exception as e:
            logger.error(f"硬件资源清理失败: {e}")

# 全局硬件管理器实例
hardware_manager = HardwareManager() 