#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI处理器功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Agent.ai_processor import ai_processor
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ai_processor():
    """测试AI处理器功能"""
    print("🔍 开始测试AI处理器功能...")
    
    # 测试1: 获取冰箱状态
    print("\n1. 测试获取冰箱状态")
    try:
        inventory = ai_processor.get_fridge_inventory()
        print(f"✅ 冰箱库存: {inventory}")
    except Exception as e:
        print(f"❌ 获取冰箱库存失败: {e}")
    
    # 测试2: 获取推荐
    print("\n2. 测试获取推荐")
    try:
        recommendations = ai_processor.get_recommendations()
        print(f"✅ 推荐结果: {recommendations}")
    except Exception as e:
        print(f"❌ 获取推荐失败: {e}")
    
    # 测试3: 测试大模型调用（如果有测试图片）
    print("\n3. 测试大模型调用")
    test_image_path = "uploads/test_camera_0_default_20250720_023024.jpg"
    if os.path.exists(test_image_path):
        try:
            result = ai_processor.process_item_recognition(test_image_path)
            print(f"✅ 物品识别结果: {result}")
        except Exception as e:
            print(f"❌ 物品识别失败: {e}")
    else:
        print(f"⚠️ 测试图片不存在: {test_image_path}")
        print("请先运行摄像头测试生成测试图片")
    
    # 测试4: 测试温度解析
    print("\n4. 测试温度解析")
    test_temps = ["4°C", "-18°C", "2度", "-5摄氏度", "10"]
    for temp in test_temps:
        try:
            parsed = ai_processor._parse_temperature(temp)
            print(f"✅ '{temp}' -> {parsed}°C")
        except Exception as e:
            print(f"❌ 解析'{temp}'失败: {e}")
    
    # 测试5: 测试保质期解析
    print("\n5. 测试保质期解析")
    test_shelf_life = ["7天", "30", "长期", "永久", "无保质期"]
    for shelf_life in test_shelf_life:
        try:
            parsed = ai_processor._parse_shelf_life(shelf_life)
            result = "长期" if parsed == -1 else f"{parsed}天"
            print(f"✅ '{shelf_life}' -> {result}")
        except Exception as e:
            print(f"❌ 解析'{shelf_life}'失败: {e}")
    
    print("\n🎉 AI处理器功能测试完成！")

if __name__ == "__main__":
    test_ai_processor() 