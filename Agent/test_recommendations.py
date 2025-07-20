#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能推荐功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_processor import ai_processor
import json
from datetime import datetime, timedelta

def test_recommendations():
    """测试智能推荐功能"""
    print("=== 测试智能推荐功能 ===")
    
    # 获取推荐
    print("\n1. 获取智能推荐...")
    recommendations = ai_processor.get_recommendations()
    
    if recommendations["success"]:
        print("✅ 推荐获取成功")
        print(f"📊 推荐总数: {recommendations.get('total_recommendations', 0)}")
        print(f"📝 推荐摘要: {recommendations.get('summary', '无')}")
        
        # 显示AI推荐
        ai_recommendations = recommendations.get("ai_recommendations", [])
        if ai_recommendations:
            print(f"\n🤖 AI推荐 ({len(ai_recommendations)}个):")
            for i, rec in enumerate(ai_recommendations, 1):
                print(f"  {i}. {rec.get('title', '无标题')}")
                print(f"     类型: {rec.get('type', '未知')}")
                print(f"     优先级: {rec.get('priority', '无')}")
                print(f"     消息: {rec.get('message', '无')}")
                print(f"     行动: {rec.get('action', '无')}")
                if rec.get('items'):
                    items_str = ', '.join([item.get('name', '未知') for item in rec['items']])
                    print(f"     相关物品: {items_str}")
                print()
        else:
            print("❌ 没有AI推荐")
        
        # 显示过期物品
        expired_items = recommendations.get("expired_items", [])
        if expired_items:
            print(f"⚠️ 过期物品 ({len(expired_items)}个):")
            for item in expired_items:
                print(f"  - {item.get('name', '未知')} (ID: {item.get('item_id', '未知')})")
        else:
            print("✅ 没有过期物品")
        
        # 显示即将过期物品
        expiring_items = recommendations.get("expiring_soon_items", [])
        if expiring_items:
            print(f"⏰ 即将过期物品 ({len(expiring_items)}个):")
            for item in expiring_items:
                print(f"  - {item.get('name', '未知')} (ID: {item.get('item_id', '未知')})")
        else:
            print("✅ 没有即将过期的物品")
        
        # 显示建议
        suggestions = recommendations.get("suggestions", [])
        if suggestions:
            print(f"\n💡 建议:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        
    else:
        print("❌ 推荐获取失败")
        print(f"错误: {recommendations.get('error', '未知错误')}")
    
    print("\n=== 测试完成 ===")

def test_fridge_status():
    """测试冰箱状态获取"""
    print("\n=== 测试冰箱状态 ===")
    
    status = ai_processor.get_fridge_status()
    print(f"📦 总物品数: {status.get('total_items', 0)}")
    
    inventory = status.get("inventory", [])
    if inventory:
        print("📋 物品列表:")
        for item in inventory:
            print(f"  - {item.get('name', '未知')} (第{item.get('level', 0)}层第{item.get('section', 0)}扇区)")
            print(f"    剩余天数: {item.get('days_remaining', 0)}")
            print(f"    是否过期: {'是' if item.get('is_expired', False) else '否'}")
    else:
        print("📭 冰箱为空")

if __name__ == "__main__":
    test_fridge_status()
    test_recommendations() 