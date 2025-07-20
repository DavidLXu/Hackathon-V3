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
        self.fridge_data_file = "Agent/fridge_inventory_qwen.json"
        
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
                recognition_result = self.process_item_recognition(image_path)
                
                if recognition_result["success"]:
                    logger.info(f"物品识别和添加成功: {recognition_result.get('item_id')}")
                else:
                    logger.error(f"物品识别失败: {recognition_result.get('error')}")
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
                # 不直接处理，等待拍照事件
                logger.info("等待拍照事件...")
            elif button_type == "take_item":
                logger.info("处理取出物品按钮事件")
                # 不直接处理，让前端弹窗选择
                logger.info("等待前端用户选择物品...")
                
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
    
    def process_item_placement(self) -> Dict:
        """处理物品放置"""
        try:
            logger.info("开始处理物品放置")
            
            # 直接调用硬件管理器拍照
            from Sensor.hardware_manager import hardware_manager, CameraType
            
            # 拍照
            image_path = hardware_manager.capture_image(CameraType.INTERNAL)
            
            if image_path:
                logger.info(f"拍照成功: {image_path}")
                
                # 等待一下确保图片保存完成
                time.sleep(1)
                
                # 处理物品识别
                recognition_result = self.process_item_recognition(image_path)
                
                if recognition_result["success"]:
                    return {
                        "success": True,
                        "message": "物品识别和添加成功",
                        "item": recognition_result.get("item_id")
                    }
                else:
                    return {
                        "success": False,
                        "error": recognition_result.get("error", "物品识别失败")
                    }
            else:
                logger.error("拍照失败")
                return {
                    "success": False,
                    "error": "拍照失败"
                }
            
        except Exception as e:
            logger.error(f"处理物品放置失败: {e}")
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
        # 获取冰箱当前状态
        fridge_status = self.get_fridge_status()
        
        return f"""你是一个智慧冰箱的AI助手。用户要添加一个新物品到冰箱。

冰箱配置：
- 5层，每层4个扇区
- 温度分布：第0层-18°C(冷冻)，第1层-5°C(冷冻)，第2层2°C(冷藏)，第3层6°C(冷藏)，第4层10°C(冷藏)

温度选择规则：
- 水果、蔬菜、乳制品、谷物、烘焙、饮料：选择2-6°C（第2-3层）
- 肉类、海鲜：选择-5°C（第1层）
- 冰淇淋、冷冻食品：选择-18°C（第0层）
- 其他：选择2-6°C（第2-3层）
- 非食物物品（乐器、工具等）：选择2-6°C（第2-3层）

保质期规则：
- 水果：3-7天
- 蔬菜：5-10天
- 肉类：7-30天
- 乳制品：7-14天
- 谷物：3-7天
- 海鲜：3-7天
- 烘焙：3-7天
- 饮料：7-14天
- 其他：5-10天
- 非食物物品（乐器、工具等）：长期保存

当前冰箱状态：
{json.dumps(fridge_status, ensure_ascii=False, indent=2)}

你的任务：
1. 识别图片中的物品（可能是食物或非食物）
2. 判断这种物品的最佳存储温度（-18°C到10°C之间）
3. 判断这种物品的保质期：
   - 如果是食物，返回具体的保质期天数（如：7、30等数字）
   - 如果是非食物（如乐器、工具、玩具等），返回"长期"
4. 根据最佳温度选择最合适的冰箱层
5. 在该层找到空闲的扇区
6. 返回JSON格式的结果，包含：
   - food_name: 物品名称（保持VLM识别的原始名称，如"玩具车"、"小提琴"等）
   - optimal_temp: 最佳存储温度（数字，包括负数）
   - shelf_life_days: 保质期天数（数字，如7、30等，非食物返回"长期"）
   - category: 物品类别
   - level: 选择的层数
   - section: 选择的扇区
   - reasoning: 选择理由

重要：food_name字段必须保持VLM识别的原始物品名称，不要修改为通用分类名称。

重要提示：
- 食物分类：请在以下分类中选择最合适的：
  * 水果：苹果、橙子、香蕉、葡萄、草莓等
  * 蔬菜：胡萝卜、土豆、洋葱、菠菜、芹菜等
  * 肉类：牛肉、猪肉、鸡肉、鱼肉等
  * 乳制品：牛奶、鸡蛋、奶酪、酸奶等
  * 谷物：面包、米饭、面条、麦片、三明治、汉堡、披萨、寿司等
  * 海鲜：鱼、虾、蟹、贝类等
  * 烘焙：蛋糕、饼干、面包、巧克力、冰淇淋等
  * 饮料：果汁、可乐、啤酒等
  * 其他：如果找不到对应分类，选择"其他"

分类优先级：
- 三明治、汉堡、披萨、寿司等主食类食物优先分类为"谷物"
- 只有真正的非食物（乐器、工具、书籍、玩具等）才分类为"非食物"
- 食物都有保质期，非食物才是长期保存
- 对于非食物物品，保持原始名称（如"玩具车"、"小提琴"等），不要改为"其他"

识别优先级：
- 优先识别为食物，除非明确看到乐器、工具、书籍等非食物物品
- 如果图片模糊或无法识别，默认识别为"其他"食物
- 不要轻易将物品识别为乐器，除非图片中明确显示乐器
- 保留VLM的原始识别结果，不要强制修改物品名称

重要：
1. 请确保选择的层温度与物品的最佳存储温度匹配，水果蔬菜不要放在冷冻层！
2. 保质期必须是具体的数字天数，不要写"7天"、"30天"，直接写数字7、30
3. 只有非食物物品才返回"长期"
4. 如果目标层满了，系统会自动选择温度最接近的其他层

温度选择优先级：
- 水果、蔬菜、乳制品、谷物、烘焙、饮料、其他：优先选择2-6°C（第2-3层），绝对不要选择-18°C或-5°C
- 肉类、海鲜：优先选择-5°C（第1层），其次选择-18°C（第0层）
- 冷冻食品：选择-18°C（第0层）

请只返回JSON格式的结果，不要其他文字。"""
    
    def _parse_recognition_result(self, response: str) -> Dict:
        """解析识别结果"""
        try:
            # 添加调试信息
            logger.info(f"🔍 VLM原始响应: {response}")
            
            # 尝试提取JSON部分
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                food_info = json.loads(json_str)
                
                # 验证必要字段
                required_fields = ["food_name", "optimal_temp", "shelf_life_days", "category", "level", "section"]
                for field in required_fields:
                    if field not in food_info:
                        logger.warning(f"识别结果缺少字段: {field}")
                        return self._get_default_recognition_result()
                
                # 转换字段名以匹配原有格式
                result = {
                    "name": food_info["food_name"],
                    "category": food_info["category"],
                    "optimal_temperature": self._parse_temperature(food_info["optimal_temp"]),
                    "expiry_days": self._parse_shelf_life(food_info["shelf_life_days"]),
                    "freezable": food_info.get("freezable", False),
                    "level": food_info["level"],
                    "section": food_info["section"],
                    "reasoning": food_info.get("reasoning", "")
                }
                
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
    
    def _parse_temperature(self, temp_str: str) -> int:
        """解析温度字符串，提取数字部分（包括负数）"""
        try:
            temp_str = str(temp_str).strip()
            
            # 检查是否包含负号
            is_negative = '-' in temp_str
            
            # 提取数字部分
            import re
            numbers = re.findall(r'\d+', temp_str)
            if numbers:
                # 取第一个数字作为温度值
                result = int(numbers[0])
                # 如果原字符串包含负号，则返回负数
                if is_negative:
                    result = -result
                return result
            else:
                return 4  # 默认温度
        except:
            return 4  # 默认温度
    
    def _parse_shelf_life(self, shelf_life_str: str) -> int:
        """解析保质期字符串，提取数字部分"""
        try:
            shelf_life_str_lower = str(shelf_life_str).lower()
            
            # 检查是否包含长期保存的关键词
            long_term_keywords = ['长期', '永久', '无保质期', '无期限', '长期保存', '无限期', '不限期']
            if any(keyword in shelf_life_str_lower for keyword in long_term_keywords):
                return -1  # 表示长期保存
            
            # 如果输入是纯数字，直接转换
            try:
                result = int(shelf_life_str)
                if result > 0:  # 确保是正数
                    return result
            except ValueError:
                pass
            
            # 检查是否包含"天"、"日"等时间单位
            if '天' in shelf_life_str or '日' in shelf_life_str:
                # 提取数字
                import re
                numbers = re.findall(r'\d+', str(shelf_life_str))
                if numbers:
                    return int(numbers[0])
            
            # 默认保质期
            return 7
        except:
            return 7  # 默认保质期
    
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
            # 检查图片文件是否存在
            if not os.path.exists(image_path):
                return {"success": False, "error": f"图片文件不存在: {image_path}"}
            
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
                            {'image': f"data:image/jpeg;base64,{image_base64}"},
                            {'text': prompt}
                        ]
                    }
                ]
            )
            
            if response.status_code == 200:
                # 添加调试信息
                logger.info(f"API响应结构: {response.output}")
                
                # 正确解析响应
                try:
                    # 获取响应文本
                    response_text = response.output.choices[0].message.content
                    if isinstance(response_text, list):
                        # 如果是列表，取第一个文本元素
                        response_text = response_text[0]
                    
                    if isinstance(response_text, dict) and 'text' in response_text:
                        response_text = response_text['text']
                    elif isinstance(response_text, str):
                        # 已经是字符串
                        pass
                    else:
                        # 尝试其他可能的格式
                        response_text = str(response_text)
                    
                    return {
                        "success": True,
                        "response": response_text
                    }
                except Exception as parse_error:
                    logger.error(f"解析API响应失败: {parse_error}")
                    return {
                        "success": False,
                        "error": f"解析响应失败: {parse_error}"
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
            # 使用大模型推荐的层和扇区
            level = item_info.get("level", 2)
            section = item_info.get("section", 0)
            shelf_life_days = item_info.get("expiry_days", 7)
            
            # 检查扇区是否可用
            level_str = str(level)
            section_str = str(section)
            
            if self.fridge_data["level_usage"][level_str][section_str]:
                # 如果推荐的扇区被占用，寻找其他可用扇区
                available_section = None
                for sec in range(4):  # 每层4个扇区
                    if not self.fridge_data["level_usage"][level_str][str(sec)]:
                        available_section = sec
                        break
                
                if available_section is not None:
                    section = available_section
                    section_str = str(section)
                else:
                    # 如果该层没有可用扇区，寻找其他层
                    for lvl in range(5):  # 5层
                        lvl_str = str(lvl)
                        for sec in range(4):
                            if not self.fridge_data["level_usage"][lvl_str][str(sec)]:
                                level = lvl
                                section = sec
                                level_str = str(level)
                                section_str = str(section)
                                break
                        if not self.fridge_data["level_usage"][level_str][section_str]:
                            break
                    
                    if self.fridge_data["level_usage"][level_str][section_str]:
                        return {"success": False, "error": "冰箱已满"}
            
            # 生成物品ID
            item_id = f"item_{int(time.time())}"
            
            # 计算过期日期
            if shelf_life_days == -1:
                # 长期保存
                expiry_date = (datetime.now() + timedelta(days=36500)).isoformat()  # 100年后
            else:
                expiry_date = (datetime.now() + timedelta(days=shelf_life_days)).isoformat()
            
            # 添加到冰箱数据
            self.fridge_data["items"][item_id] = {
                "name": item_info.get("name", "未知食物"),
                "category": item_info.get("category", "其他"),
                "level": level,
                "section": section,
                "optimal_temperature": item_info.get("optimal_temperature", 4),
                "expiry_date": expiry_date,
                "added_date": datetime.now().isoformat(),
                "image_path": image_path,
                "freezable": item_info.get("freezable", False),
                "reasoning": item_info.get("reasoning", "")
            }
            
            # 更新层和扇区占用状态
            self.fridge_data["level_usage"][level_str][section_str] = True
            
            # 保存数据
            self.save_fridge_data()
            
            logger.info(f"物品添加成功: {item_info.get('name')} -> 第{level}层第{section}扇区")
            
            return {
                "success": True,
                "item_id": item_id,
                "temperature_level": level,
                "message": f"物品已添加到第{level}层第{section}扇区",
                "reasoning": item_info.get("reasoning", "")
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
            
            # 更新层级使用情况
            level_str = str(level)
            section_str = str(section)
            if level_str in self.fridge_data["level_usage"] and section_str in self.fridge_data["level_usage"][level_str]:
                self.fridge_data["level_usage"][level_str][section_str] = False
            
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
    
    def get_fridge_status(self) -> Dict:
        """获取冰箱当前状态"""
        current_time = datetime.now()
        inventory = []
        
        for item_id, item in self.fridge_data["items"].items():
            expiry_date = datetime.fromisoformat(item["expiry_date"])
            days_remaining = (expiry_date - current_time).days
            
            inventory.append({
                "item_id": item_id,
                "name": item["name"],
                "category": item["category"],
                "level": item["level"],
                "section": item["section"],
                "days_remaining": max(0, days_remaining),
                "is_expired": days_remaining < 0,
                "optimal_temp": item.get("optimal_temperature", 4)
            })
        
        return {
            "inventory": inventory,
            "total_items": len(inventory),
            "temperature_levels": self.temperature_levels,
            "available_sections": self.fridge_data.get("level_usage", {})
        }
    
    def get_fridge_inventory(self) -> Dict:
        """获取冰箱库存"""
        try:
            inventory = []
            
            # 遍历所有物品
            for item_id, item_data in self.fridge_data["items"].items():
                inventory.append({
                    "item_id": item_id,
                    "name": item_data["name"],
                    "category": item_data["category"],
                    "level": item_data["level"],
                    "section": item_data["section"],
                    "optimal_temperature": item_data.get("optimal_temp", 4),
                    "expiry_date": item_data["expiry_date"],
                    "added_date": item_data.get("added_time", item_data.get("added_date", ""))
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
                
                # 确保数据格式正确
                if "items" not in data:
                    data["items"] = {}
                if "level_usage" not in data:
                    data["level_usage"] = self._initialize_level_usage()
                if "last_update" not in data:
                    data["last_update"] = datetime.now().isoformat()
                
                return data
            else:
                return self.initialize_fridge_data()
        except Exception as e:
            logger.error(f"加载冰箱数据失败: {e}")
            return self.initialize_fridge_data()
    
    def _initialize_level_usage(self) -> Dict:
        """初始化层级使用情况"""
        level_usage = {}
        for level in range(self.total_levels):
            level_usage[str(level)] = {}
            for section in range(self.sections_per_level):
                level_usage[str(level)][str(section)] = False
        return level_usage
    
    def initialize_fridge_data(self) -> Dict:
        """初始化冰箱数据"""
        data = {
            "items": {},
            "level_usage": self._initialize_level_usage(),
            "last_update": datetime.now().isoformat()
        }
        
        return data
    
    def save_fridge_data(self):
        """保存冰箱数据"""
        try:
            # 更新最后修改时间
            self.fridge_data["last_update"] = datetime.now().isoformat()
            
            with open(self.fridge_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.fridge_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存冰箱数据失败: {e}")

# 全局AI处理器实例
ai_processor = AIProcessor() 