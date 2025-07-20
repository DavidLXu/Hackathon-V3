#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试按钮按下功能
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from Agent.ai_processor import ai_processor
from Sensor.hardware_manager import hardware_manager, CameraType

def test_button_press():
    """测试按钮按下功能"""
    print("🔘 开始测试按钮按下功能...")
    
    # 检查当前冰箱状态
    print("\n1. 检查当前冰箱状态")
    inventory = ai_processor.get_fridge_inventory()
    print(f"当前物品数量: {len(inventory['inventory'])}")
    
    # 测试物品放置
    print("\n2. 测试物品放置功能")
    result = ai_processor.process_item_placement()
    print(f"物品放置结果: {result}")
    
    # 检查拍照是否成功
    if result["success"]:
        print("✅ 物品放置成功")
        
        # 再次检查冰箱状态
        print("\n3. 检查更新后的冰箱状态")
        inventory = ai_processor.get_fridge_inventory()
        print(f"更新后物品数量: {len(inventory['inventory'])}")
        
        if len(inventory['inventory']) > 0:
            print("✅ 新物品已添加到冰箱")
            for item in inventory['inventory']:
                print(f"  - {item['name']} ({item['category']}) -> 第{item['level']}层第{item['section']}扇区")
        else:
            print("❌ 新物品未添加到冰箱")
    else:
        print(f"❌ 物品放置失败: {result.get('error')}")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    test_button_press() 