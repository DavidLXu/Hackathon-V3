#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧冰箱核心系统调度器
负责协调各个模块的工作，作为系统的中央控制器
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EventType(Enum):
    """事件类型枚举"""
    BUTTON_PRESS = "button_press"
    FACE_DETECTION = "face_detection"
    CAMERA_CAPTURE = "camera_capture"
    ITEM_PLACED = "item_placed"
    ITEM_TAKEN = "item_taken"
    PROXIMITY_SENSOR = "proximity_sensor"
    SYSTEM_ERROR = "system_error"

@dataclass
class SystemEvent:
    """系统事件数据类"""
    event_type: EventType
    timestamp: datetime
    source: str
    data: Dict
    priority: int = 0

class CoreSystem:
    """核心系统调度器"""
    
    def __init__(self):
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.running = False
        self.event_queue = []
        self.event_lock = threading.Lock()
        
        # 系统状态
        self.system_status = {
            "running": False,
            "modules": {},
            "last_event": None,
            "error_count": 0
        }
        
        # 初始化事件处理器
        self._init_event_handlers()
    
    def _init_event_handlers(self):
        """初始化事件处理器"""
        for event_type in EventType:
            self.event_handlers[event_type] = []
    
    def register_event_handler(self, event_type: EventType, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"注册事件处理器: {event_type.value} -> {handler.__name__}")
    
    def unregister_event_handler(self, event_type: EventType, handler: Callable):
        """注销事件处理器"""
        if event_type in self.event_handlers and handler in self.event_handlers[event_type]:
            self.event_handlers[event_type].remove(handler)
            logger.info(f"注销事件处理器: {event_type.value} -> {handler.__name__}")
    
    def emit_event(self, event: SystemEvent):
        """发送系统事件"""
        with self.event_lock:
            self.event_queue.append(event)
            self.system_status["last_event"] = event
        
        logger.info(f"发送事件: {event.event_type.value} from {event.source}")
        
        # 异步处理事件
        threading.Thread(target=self._process_event, args=(event,), daemon=True).start()
    
    def _process_event(self, event: SystemEvent):
        """处理系统事件"""
        try:
            handlers = self.event_handlers.get(event.event_type, [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"事件处理器出错: {handler.__name__} -> {e}")
                    self.system_status["error_count"] += 1
        except Exception as e:
            logger.error(f"事件处理出错: {e}")
    
    def start(self):
        """启动核心系统"""
        if self.running:
            logger.warning("核心系统已在运行")
            return
        
        self.running = True
        self.system_status["running"] = True
        logger.info("核心系统已启动")
    
    def stop(self):
        """停止核心系统"""
        self.running = False
        self.system_status["running"] = False
        logger.info("核心系统已停止")
    
    def get_status(self) -> Dict:
        """获取系统状态"""
        return self.system_status.copy()
    
    def create_event(self, event_type: EventType, source: str, data: Dict, priority: int = 0) -> SystemEvent:
        """创建系统事件"""
        return SystemEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            source=source,
            data=data,
            priority=priority
        )

# 全局核心系统实例
core_system = CoreSystem() 