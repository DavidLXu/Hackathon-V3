#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统启动器
统一启动和管理所有模块
"""

import logging
import threading
import time
import signal
import sys
import os
from typing import Dict, List

# 添加路径以便导入其他模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入各个模块
from core_system import core_system, EventType, SystemEvent
from ai_processor import ai_processor
from web_manager import web_manager

# 尝试导入硬件管理器（可能不在当前环境）
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Sensor'))
    from hardware_manager import hardware_manager
    HARDWARE_AVAILABLE = True
except ImportError as e:
    print(f"警告: 硬件管理器不可用 ({e})")
    HARDWARE_AVAILABLE = False
    hardware_manager = None

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemLauncher:
    """系统启动器"""
    
    def __init__(self):
        self.running = False
        self.modules = {}
        self.threads = {}
        
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在关闭系统...")
        self.shutdown()
        sys.exit(0)
    
    def initialize_modules(self):
        """初始化所有模块"""
        try:
            logger.info("开始初始化系统模块...")
            
            # 启动核心系统
            core_system.start()
            self.modules['core_system'] = core_system
            logger.info("✅ 核心系统已启动")
            
            # 初始化AI处理器
            self.modules['ai_processor'] = ai_processor
            logger.info("✅ AI处理器已初始化")
            
            # 初始化Web管理器
            self.modules['web_manager'] = web_manager
            logger.info("✅ Web管理器已初始化")
            
            # 初始化硬件管理器（如果可用）
            if HARDWARE_AVAILABLE and hardware_manager:
                self.modules['hardware_manager'] = hardware_manager
                logger.info("✅ 硬件管理器已初始化")
                
                # 启动人脸检测监控
                try:
                    hardware_manager.start_face_detection_monitor()
                    logger.info("✅ 人脸检测监控已启动")
                except Exception as e:
                    logger.warning(f"人脸检测监控启动失败: {e}")
            else:
                logger.warning("⚠️ 硬件管理器不可用，将使用模拟模式")
            
            logger.info("✅ 所有模块初始化完成")
            
        except Exception as e:
            logger.error(f"模块初始化失败: {e}")
            raise
    
    def start_web_server(self):
        """启动Web服务器"""
        try:
            logger.info("启动Web服务器...")
            
            # 使用新的线程启动方法
            web_thread = web_manager.start_in_thread(host='0.0.0.0', port=8080, debug=False)
            self.threads['web_server'] = web_thread
            
            # 等待一下确保服务器启动
            time.sleep(2)
            
            logger.info("✅ Web服务器已启动: http://localhost:8080")
            
        except Exception as e:
            logger.error(f"Web服务器启动失败: {e}")
            raise
    
    def start_hardware_monitoring(self):
        """启动硬件监控"""
        if not HARDWARE_AVAILABLE or not hardware_manager:
            logger.warning("硬件管理器不可用，跳过硬件监控")
            return
        
        try:
            logger.info("启动硬件监控...")
            
            # 硬件监控已经在初始化时启动
            logger.info("✅ 硬件监控已启动")
            
        except Exception as e:
            logger.error(f"硬件监控启动失败: {e}")
            raise
    
    def start_system_monitoring(self):
        """启动系统监控"""
        try:
            logger.info("启动系统监控...")
            
            # 启动系统状态监控线程
            monitor_thread = threading.Thread(
                target=self._system_monitor_loop,
                daemon=True
            )
            monitor_thread.start()
            self.threads['system_monitor'] = monitor_thread
            
            logger.info("✅ 系统监控已启动")
            
        except Exception as e:
            logger.error(f"系统监控启动失败: {e}")
            raise
    
    def _system_monitor_loop(self):
        """系统监控循环"""
        while self.running:
            try:
                # 检查系统状态
                status = core_system.get_status()
                
                # 记录系统状态（每分钟一次）
                if int(time.time()) % 60 == 0:
                    logger.info(f"系统状态: {status}")
                
                # 检查各模块状态
                for module_name, module in self.modules.items():
                    if hasattr(module, 'get_status'):
                        module_status = module.get_status()
                        if module_status and not module_status.get('running', True):
                            logger.warning(f"模块 {module_name} 状态异常")
                
                time.sleep(10)  # 每10秒检查一次
                
            except Exception as e:
                logger.error(f"系统监控出错: {e}")
                time.sleep(30)  # 出错后等待30秒再重试
    
    def start(self):
        """启动整个系统"""
        try:
            logger.info("🚀 启动智慧冰箱系统...")
            
            self.running = True
            
            # 初始化模块
            self.initialize_modules()
            
            # 启动Web服务器
            self.start_web_server()
            
            # 启动硬件监控
            self.start_hardware_monitoring()
            
            # 启动系统监控
            self.start_system_monitoring()
            
            logger.info("🎉 系统启动完成！")
            logger.info("📱 Web界面: http://localhost:8080")
            logger.info("🔧 按 Ctrl+C 停止系统")
            
            # 保持主线程运行
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在关闭系统...")
                self.shutdown()
            
        except Exception as e:
            logger.error(f"系统启动失败: {e}")
            self.shutdown()
            raise
    
    def shutdown(self):
        """关闭系统"""
        try:
            logger.info("正在关闭系统...")
            self.running = False
            
            # 停止硬件管理器
            if HARDWARE_AVAILABLE and hardware_manager:
                try:
                    hardware_manager.cleanup()
                    logger.info("✅ 硬件管理器已关闭")
                except Exception as e:
                    logger.error(f"关闭硬件管理器失败: {e}")
            
            # 停止核心系统
            try:
                core_system.stop()
                logger.info("✅ 核心系统已关闭")
            except Exception as e:
                logger.error(f"关闭核心系统失败: {e}")
            
            # 等待线程结束
            for thread_name, thread in self.threads.items():
                if thread.is_alive():
                    logger.info(f"等待线程 {thread_name} 结束...")
                    thread.join(timeout=5)
                    if thread.is_alive():
                        logger.warning(f"线程 {thread_name} 未能正常结束")
            
            logger.info("✅ 系统已完全关闭")
            
        except Exception as e:
            logger.error(f"系统关闭过程中出错: {e}")
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        status = {
            "running": self.running,
            "modules": {},
            "threads": {},
            "hardware_available": HARDWARE_AVAILABLE
        }
        
        # 获取各模块状态
        for module_name, module in self.modules.items():
            if hasattr(module, 'get_status'):
                status["modules"][module_name] = module.get_status()
            else:
                status["modules"][module_name] = {"status": "initialized"}
        
        # 获取线程状态
        for thread_name, thread in self.threads.items():
            status["threads"][thread_name] = {
                "alive": thread.is_alive(),
                "daemon": thread.daemon
            }
        
        return status

def main():
    """主函数"""
    launcher = SystemLauncher()
    
    try:
        launcher.start()
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭系统...")
    except Exception as e:
        logger.error(f"系统运行出错: {e}")
    finally:
        launcher.shutdown()

if __name__ == "__main__":
    main() 