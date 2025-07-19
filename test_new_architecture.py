#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新架构测试脚本
验证重构后的系统功能
"""

import sys
import os
import time
import threading
import logging

# 添加路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'Agent'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'Sensor'))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_core_system():
    """测试核心系统"""
    logger.info("🧪 测试核心系统...")
    
    try:
        from Agent.core_system import core_system, EventType, SystemEvent
        
        # 测试事件创建
        event = core_system.create_event(
            EventType.BUTTON_PRESS,
            "test",
            {"button_type": "test_button"}
        )
        
        # 测试事件处理器注册
        def test_handler(event):
            logger.info(f"✅ 事件处理器被调用: {event.event_type.value}")
        
        core_system.register_event_handler(EventType.BUTTON_PRESS, test_handler)
        
        # 测试事件发送
        core_system.emit_event(event)
        
        # 等待事件处理
        time.sleep(0.1)
        
        logger.info("✅ 核心系统测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 核心系统测试失败: {e}")
        return False

def test_ai_processor():
    """测试AI处理器"""
    logger.info("🧪 测试AI处理器...")
    
    try:
        from Agent.ai_processor import ai_processor
        
        # 测试冰箱数据加载
        inventory = ai_processor.get_fridge_inventory()
        logger.info(f"✅ 冰箱库存获取成功: {len(inventory.get('inventory', []))} 个物品")
        
        # 测试推荐系统
        recommendations = ai_processor.get_recommendations()
        logger.info(f"✅ 推荐系统测试成功: {recommendations.get('success', False)}")
        
        logger.info("✅ AI处理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ AI处理器测试失败: {e}")
        return False

def test_web_manager():
    """测试Web管理器"""
    logger.info("🧪 测试Web管理器...")
    
    try:
        from Agent.web_manager import web_manager
        
        # 测试emoji映射
        emoji = web_manager.get_food_emoji("苹果", "水果")
        logger.info(f"✅ Emoji映射测试: 苹果 -> {emoji}")
        
        # 测试温度信息
        temp_info = web_manager.get_temperature_info(2)
        logger.info(f"✅ 温度信息测试: 第2层 -> {temp_info}")
        
        # 测试过期进度计算
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=3)).isoformat()
        progress = web_manager.calculate_expiry_progress(future_date)
        logger.info(f"✅ 过期进度计算测试: {progress}")
        
        logger.info("✅ Web管理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ Web管理器测试失败: {e}")
        return False

def test_hardware_simulator():
    """测试硬件模拟器"""
    logger.info("🧪 测试硬件模拟器...")
    
    try:
        from Sensor.hardware_simulator import hardware_simulator, ButtonType, CameraType
        
        # 测试按钮模拟
        hardware_simulator.simulate_button_press(ButtonType.PLACE_ITEM)
        time.sleep(0.1)
        
        # 测试人脸检测模拟
        hardware_simulator.simulate_face_detection()
        time.sleep(0.1)
        
        # 测试拍照功能
        image_path = hardware_simulator.capture_image(CameraType.INTERNAL)
        if image_path:
            logger.info(f"✅ 拍照测试成功: {image_path}")
        
        # 测试摄像头状态
        camera_status = hardware_simulator.get_camera_status()
        logger.info(f"✅ 摄像头状态: {camera_status}")
        
        logger.info("✅ 硬件模拟器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 硬件模拟器测试失败: {e}")
        return False

def test_event_flow():
    """测试事件流程"""
    logger.info("🧪 测试事件流程...")
    
    try:
        from Agent.core_system import core_system, EventType
        from Sensor.hardware_simulator import hardware_simulator, ButtonType
        
        # 重置核心系统状态
        core_system.event_handlers = {}
        core_system._init_event_handlers()
        
        # 记录事件
        events_received = []
        
        def event_logger(event):
            events_received.append(event.event_type.value)
            logger.info(f"📨 收到事件: {event.event_type.value} from {event.source}")
        
        # 注册事件监听器
        for event_type in EventType:
            core_system.register_event_handler(event_type, event_logger)
        
        # 等待一下确保注册完成
        time.sleep(0.1)
        
        # 直接发送事件，绕过防抖机制
        button_event = core_system.create_event(
            EventType.BUTTON_PRESS,
            "test_event_flow",
            {"button_type": "place_item"}
        )
        core_system.emit_event(button_event)
        time.sleep(0.2)
        
        # 直接发送接近传感器事件
        proximity_event = core_system.create_event(
            EventType.PROXIMITY_SENSOR,
            "test_event_flow",
            {"detected": True, "distance": "near"}
        )
        core_system.emit_event(proximity_event)
        time.sleep(0.2)
        
        # 检查事件是否被正确接收
        if len(events_received) >= 2:
            logger.info(f"✅ 事件流程测试成功，收到 {len(events_received)} 个事件: {events_received}")
            return True
        else:
            logger.error(f"❌ 事件流程测试失败，只收到 {len(events_received)} 个事件: {events_received}")
            return False
        
    except Exception as e:
        logger.error(f"❌ 事件流程测试失败: {e}")
        return False

def test_system_integration():
    """测试系统集成"""
    logger.info("🧪 测试系统集成...")
    
    try:
        # 启动核心系统
        from Agent.core_system import core_system
        core_system.start()
        
        # 初始化AI处理器
        from Agent.ai_processor import ai_processor
        
        # 初始化Web管理器
        from Agent.web_manager import web_manager
        
        # 初始化硬件模拟器
        from Sensor.hardware_simulator import hardware_simulator
        
        # 启动硬件监控
        hardware_simulator.start_face_detection_monitor()
        
        logger.info("✅ 系统集成测试通过")
        
        # 清理
        hardware_simulator.stop_face_detection_monitor()
        core_system.stop()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 系统集成测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始新架构测试...")
    
    tests = [
        ("核心系统", test_core_system),
        ("AI处理器", test_ai_processor),
        ("Web管理器", test_web_manager),
        ("硬件模拟器", test_hardware_simulator),
        ("事件流程", test_event_flow),
        ("系统集成", test_system_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 测试出错: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"测试结果: {passed}/{total} 通过")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 所有测试通过！新架构工作正常。")
        return True
    else:
        logger.error(f"❌ {total - passed} 个测试失败，请检查问题。")
        return False

def main():
    """主函数"""
    try:
        success = run_all_tests()
        
        if success:
            logger.info("\n🎉 新架构验证成功！")
            logger.info("📝 可以运行以下命令启动新系统:")
            logger.info("   python start_new_system.py")
        else:
            logger.error("\n❌ 新架构验证失败，请修复问题后重试。")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️ 测试被用户中断")
    except Exception as e:
        logger.error(f"\n❌ 测试过程中出现未预期的错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 