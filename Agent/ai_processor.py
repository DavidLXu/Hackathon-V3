#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI处理器
专门处理图像识别和AI相关功能
"""

import dashscope
import json
import os
import base64
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# 添加路径以便导入核心系统
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core_system import core_system, EventType, SystemEvent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置API密钥 - 从环境变量获取
os.environ['DASHSCOPE_API_KEY'] = 'sk-0419b645f1d4499da2094c863442e0db'

api_key = os.getenv('DASHSCOPE_API_KEY')
if not api_key:
    raise ValueError("Please set the DASHSCOPE_API_KEY environment variable")
dashscope.api_key = api_key

class AIProcessor:
    """AI处理器"""
    
    def __init__(self):
        self.fridge_data_file = "fridge_inventory_qwen.json"
        
        # 冰箱配置
        self.total_levels = 5  # 5层
        self.sections_per_level = 4  # 每层4个扇区
        self.temperature_levels = {
            0: -18,  # 最底层：-18°C (冷冻)
            1: -5,   # 第二层：-5°C (冷冻)
            2: 2,    # 第三层：2°C (冷藏)
            3: 6,    # 第四层：6°C (冷藏)
            4: 10    # 最顶层：10°C (冷藏)
        }
        
        # 加载冰箱数据
        self.fridge_data = self.load_fridge_data()
        
        # 注册事件处理器
        self._register_event_handlers()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        core_system.register_event_handler(EventType.CAMERA_CAPTURE, self._handle_camera_capture)
        core_system.register_event_handler(EventType.BUTTON_PRESS, self._handle_button_press)
        logger.info("AI处理器事件处理器注册完成")
    
    def _handle_camera_capture(self, event: SystemEvent):
        """处理拍照事件"""
        try:
            data = event.data
            image_path = data.get("image_path")
            camera_type = data.get("camera_type")
            
            if camera_type == "internal":
                # 内部摄像头拍照，进行物品识别
                logger.info(f"处理内部摄像头拍照事件: {image_path}")
                self.process_item_recognition(image_path)
            else:
                logger.info(f"处理外部摄像头拍照事件: {image_path}")
                
        except Exception as e:
            logger.error(f"处理拍照事件失败: {e}")
    
    def _handle_button_press(self, event: SystemEvent):
        """处理按钮事件"""
        try:
            data = event.data
            button_type = data.get("button_type")
            
            if button_type == "place_item":
                logger.info("处理放入物品按钮事件")
                # 这里可以触发拍照或其他操作
                # 实际拍照由硬件管理器处理
            elif button_type == "take_item":
                logger.info("处理取出物品按钮事件")
                self.process_item_removal()
                
        except Exception as e:
            logger.error(f"处理按钮事件失败: {e}")
    
    def process_item_recognition(self, image_path: str) -> Dict:
        """处理物品识别"""
        try:
            logger.info(f"开始处理物品识别: {image_path}")
            
            # 调用Qwen-VL进行图像识别
            result = self.call_qwen_vl(image_path, self._get_recognition_prompt())
            
            if result["success"]:
                # 解析识别结果
                parsed_result = self._parse_recognition_result(result["response"])
                
                # 添加到冰箱
                add_result = self.add_item_to_fridge(parsed_result, image_path)
                
                if add_result["success"]:
                    # 发送物品放置事件
                    event = core_system.create_event(
                        EventType.ITEM_PLACED,
                        "ai_processor",
                        {
                            "item_name": parsed_result.get("name"),
                            "category": parsed_result.get("category"),
                            "expiry_days": parsed_result.get("expiry_days"),
                            "temperature_level": add_result.get("temperature_level")
                        }
                    )
                    core_system.emit_event(event)
                    
                    logger.info(f"物品识别和添加成功: {parsed_result.get('name')}")
                    return add_result
                else:
                    logger.error(f"添加物品到冰箱失败: {add_result.get('error')}")
                    return add_result
            else:
                logger.error(f"物品识别失败: {result.get('error')}")
                return result
                
        except Exception as e:
            logger.error(f"处理物品识别失败: {e}")
            return {"success": False, "error": str(e)}
    
    def process_item_removal(self) -> Dict:
        """处理物品取出"""
        try:
            # 获取推荐取出的物品
            recommendation = self.get_recommendations()
            
            if recommendation["success"] and recommendation.get("take_out_item"):
                item = recommendation["take_out_item"]
                
                # 从冰箱中取出物品
                remove_result = self.get_item_from_fridge(item["id"])
                
                if remove_result["success"]:
                    # 发送物品取出事件
                    event = core_system.create_event(
                        EventType.ITEM_TAKEN,
                        "ai_processor",
                        {
                            "item_name": item.get("name"),
                            "category": item.get("category"),
                            "reason": item.get("reason")
                        }
                    )
                    core_system.emit_event(event)
                    
                    logger.info(f"物品取出成功: {item.get('name')}")
                    return remove_result
                else:
                    logger.error(f"取出物品失败: {remove_result.get('error')}")
                    return remove_result
            else:
                logger.warning("没有推荐取出的物品")
                return {"success": False, "error": "没有推荐取出的物品"}
                
        except Exception as e:
            logger.error(f"处理物品取出失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_recognition_prompt(self) -> str:
        """获取识别提示词"""
        return """
        请分析这张图片中的食物，并提供以下信息：
        1. 食物名称（中文）
        2. 食物类别（如：水果、蔬菜、肉类、乳制品、饮料、零食等）
        3. 建议的保存温度（摄氏度）
        4. 预计保质期（天数）
        5. 是否适合冷冻保存（是/否）
        
        请以JSON格式返回，格式如下：
        {
            "name": "食物名称",
            "category": "食物类别",
            "optimal_temperature": 温度值,
            "expiry_days": 保质期天数,
            "freezable": true/false
        }
        """
    
    def _parse_recognition_result(self, response: str) -> Dict:
        """解析识别结果"""
        try:
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                
                # 验证必要字段
                required_fields = ["name", "category", "optimal_temperature", "expiry_days"]
                for field in required_fields:
                    if field not in result:
                        logger.warning(f"识别结果缺少字段: {field}")
                        result[field] = self._get_default_value(field)
                
                return result
            else:
                logger.warning("无法从响应中提取JSON")
                return self._get_default_recognition_result()
                
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON失败: {e}")
            return self._get_default_recognition_result()
        except Exception as e:
            logger.error(f"解析识别结果失败: {e}")
            return self._get_default_recognition_result()
    
    def _get_default_value(self, field: str):
        """获取默认值"""
        defaults = {
            "name": "未知食物",
            "category": "其他",
            "optimal_temperature": 4,
            "expiry_days": 7,
            "freezable": False
        }
        return defaults.get(field, "未知")
    
    def _get_default_recognition_result(self) -> Dict:
        """获取默认识别结果"""
        return {
            "name": "未知食物",
            "category": "其他",
            "optimal_temperature": 4,
            "expiry_days": 7,
            "freezable": False
        }
    
    def call_qwen_vl(self, image_path: str, prompt: str) -> Dict:
        """调用Qwen-VL模型"""
        try:
            # 读取并编码图片
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 调用Qwen-VL API
            response = dashscope.MultiModalConversation.call(
                model='qwen-vl-plus',
                messages=[
                    {
                        'role': 'user',
                        'content': [
                            {'image': image_base64},
                            {'text': prompt}
                        ]
                    }
                ]
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "response": response.output.choices[0].message.content[0].text
                }
            else:
                return {
                    "success": False,
                    "error": f"API调用失败: {response.code} - {response.message}"
                }
                
        except Exception as e:
            logger.error(f"调用Qwen-VL失败: {e}")
            return {"success": False, "error": str(e)}
    
    def add_item_to_fridge(self, item_info: Dict, image_path: str) -> Dict:
        """添加物品到冰箱"""
        try:
            # 找到最佳温度层
            optimal_temp = item_info.get("optimal_temperature", 4)
            level = self.find_best_temperature_level(optimal_temp)
            
            # 找到可用位置
            position = self._find_available_position(level)
            
            if position is None:
                return {"success": False, "error": "冰箱已满"}
            
            # 生成物品ID
            item_id = f"item_{int(time.time())}"
            
            # 计算过期日期
            expiry_days = item_info.get("expiry_days", 7)
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            
            # 添加到冰箱数据
            self.fridge_data["items"][item_id] = {
                "name": item_info.get("name", "未知食物"),
                "category": item_info.get("category", "其他"),
                "level": level,
                "section": position["section"],
                "optimal_temperature": optimal_temp,
                "expiry_date": expiry_date.isoformat(),
                "added_date": datetime.now().isoformat(),
                "image_path": image_path,
                "freezable": item_info.get("freezable", False)
            }
            
            # 更新层和扇区占用状态
            self.fridge_data["levels"][level]["sections"][position["section"]] = item_id
            
            # 保存数据
            self.save_fridge_data()
            
            logger.info(f"物品添加成功: {item_info.get('name')} -> 第{level}层第{position['section']}扇区")
            
            return {
                "success": True,
                "item_id": item_id,
                "temperature_level": level,
                "message": f"物品已添加到第{level}层"
            }
            
        except Exception as e:
            logger.error(f"添加物品到冰箱失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _find_available_position(self, level: int) -> Optional[Dict]:
        """找到可用位置"""
        if level not in self.fridge_data["levels"]:
            return None
        
        level_data = self.fridge_data["levels"][level]
        for section in range(self.sections_per_level):
            if level_data["sections"][section] is None:
                return {"level": level, "section": section}
        
        return None
    
    def find_best_temperature_level(self, optimal_temp: float) -> int:
        """找到最佳温度层"""
        best_level = 2  # 默认冷藏层
        min_diff = float('inf')
        
        for level, temp in self.temperature_levels.items():
            diff = abs(temp - optimal_temp)
            if diff < min_diff:
                min_diff = diff
                best_level = level
        
        return best_level
    
    def get_item_from_fridge(self, item_id: str) -> Dict:
        """从冰箱中取出物品"""
        try:
            if item_id not in self.fridge_data["items"]:
                return {"success": False, "error": "物品不存在"}
            
            item = self.fridge_data["items"][item_id]
            level = item["level"]
            section = item["section"]
            
            # 从冰箱数据中移除
            del self.fridge_data["items"][item_id]
            self.fridge_data["levels"][level]["sections"][section] = None
            
            # 保存数据
            self.save_fridge_data()
            
            logger.info(f"物品取出成功: {item['name']}")
            
            return {
                "success": True,
                "item": item,
                "message": f"已取出 {item['name']}"
            }
            
        except Exception as e:
            logger.error(f"取出物品失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_recommendations(self) -> Dict:
        """获取推荐"""
        try:
            # 分析冰箱状态
            inventory = self.get_fridge_inventory()
            
            if not inventory["success"]:
                return {"success": False, "error": "获取库存失败"}
            
            items = inventory["inventory"]
            
            # 检查过期物品
            expired_items = []
            expiring_soon_items = []
            
            current_time = datetime.now()
            
            for item in items:
                item_data = self.fridge_data["items"][item["item_id"]]
                expiry_date = datetime.fromisoformat(item_data["expiry_date"])
                
                days_until_expiry = (expiry_date - current_time).days
                
                if days_until_expiry <= 0:
                    expired_items.append(item)
                elif days_until_expiry <= 2:
                    expiring_soon_items.append(item)
            
            # 生成推荐
            recommendations = {
                "success": True,
                "expired_items": expired_items,
                "expiring_soon_items": expiring_soon_items,
                "take_out_item": None,
                "suggestions": []
            }
            
            # 优先推荐取出过期物品
            if expired_items:
                recommendations["take_out_item"] = {
                    "id": expired_items[0]["item_id"],
                    "name": expired_items[0]["name"],
                    "category": expired_items[0]["category"],
                    "reason": "已过期"
                }
                recommendations["suggestions"].append("发现过期物品，建议立即取出")
            
            # 其次推荐即将过期的物品
            elif expiring_soon_items:
                recommendations["take_out_item"] = {
                    "id": expiring_soon_items[0]["item_id"],
                    "name": expiring_soon_items[0]["name"],
                    "category": expiring_soon_items[0]["category"],
                    "reason": "即将过期"
                }
                recommendations["suggestions"].append("发现即将过期的物品，建议优先食用")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_fridge_inventory(self) -> Dict:
        """获取冰箱库存"""
        try:
            inventory = []
            
            for level in range(self.total_levels):
                level_data = self.fridge_data["levels"][level]
                
                for section in range(self.sections_per_level):
                    item_id = level_data["sections"][section]
                    
                    if item_id and item_id in self.fridge_data["items"]:
                        item_data = self.fridge_data["items"][item_id]
                        inventory.append({
                            "item_id": item_id,
                            "name": item_data["name"],
                            "category": item_data["category"],
                            "level": level,
                            "section": section,
                            "optimal_temperature": item_data["optimal_temperature"],
                            "expiry_date": item_data["expiry_date"],
                            "added_date": item_data["added_date"]
                        })
            
            return {
                "success": True,
                "inventory": inventory
            }
            
        except Exception as e:
            logger.error(f"获取冰箱库存失败: {e}")
            return {"success": False, "error": str(e)}
    
    def load_fridge_data(self) -> Dict:
        """加载冰箱数据"""
        try:
            if os.path.exists(self.fridge_data_file):
                with open(self.fridge_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 兼容旧格式数据
                if "levels" not in data:
                    # 从level_usage转换为levels格式
                    data["levels"] = {}
                    for level in range(self.total_levels):
                        data["levels"][level] = {
                            "temperature": self.temperature_levels[level],
                            "sections": [None] * self.sections_per_level
                        }
                        
                        # 如果有level_usage数据，转换过来
                        if "level_usage" in data:
                            level_usage = data["level_usage"].get(str(level), {})
                            for section in range(self.sections_per_level):
                                if level_usage.get(str(section), False):
                                    # 找到对应的物品ID
                                    for item_id, item_data in data["items"].items():
                                        if (item_data.get("level") == level and 
                                            item_data.get("section") == section):
                                            data["levels"][level]["sections"][section] = item_id
                                            break
                
                return data
            else:
                return self.initialize_fridge_data()
        except Exception as e:
            logger.error(f"加载冰箱数据失败: {e}")
            return self.initialize_fridge_data()
    
    def initialize_fridge_data(self) -> Dict:
        """初始化冰箱数据"""
        data = {
            "items": {},
            "levels": {}
        }
        
        for level in range(self.total_levels):
            data["levels"][level] = {
                "temperature": self.temperature_levels[level],
                "sections": [None] * self.sections_per_level
            }
        
        return data
    
    def save_fridge_data(self):
        """保存冰箱数据"""
        try:
            with open(self.fridge_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.fridge_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存冰箱数据失败: {e}")

# 全局AI处理器实例
ai_processor = AIProcessor() 