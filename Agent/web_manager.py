#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web服务管理器
专门处理Web界面和API服务
"""

from flask import Flask, render_template, jsonify, request, Response
import json
import os
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Set

# 添加路径以便导入核心系统
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core_system import core_system, EventType, SystemEvent
from ai_processor import ai_processor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebManager:
    """Web服务管理器"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.sse_clients: Set[str] = set()
        self.sse_lock = threading.Lock()
        
        # 食物emoji映射
        self.FOOD_EMOJIS = {
            "苹果": "🍎", "香蕉": "🍌", "橙子": "🍊", "草莓": "🍓", "葡萄": "🍇",
            "西瓜": "🍉", "牛奶": "🥛", "酸奶": "🥛", "奶酪": "🧀", "鸡蛋": "🥚",
            "面包": "🍞", "三明治": "🥪", "肉类": "🥩", "鱼类": "🐟", "蔬菜": "🥬",
            "胡萝卜": "🥕", "番茄": "🍅", "洋葱": "🧅", "土豆": "🥔", "青椒": "🫑",
            "黄瓜": "🥒", "生菜": "🥬", "冰淇淋": "🍦", "饺子": "🥟", "汤圆": "🥟",
            "橙汁": "🧃", "可乐": "🥤", "啤酒": "🍺", "巧克力": "🍫", "黄油": "🧈",
            "小提琴": "🎻", "乐器": "🎻", "熟食": "🍱", "水果": "🍎", "乳制品": "🥛",
            "蛋类": "🥚", "海鲜": "🐟", "饮料": "🥤", "零食": "🍿", "冷冻食品": "🧊",
            "其他": "📦"
        }
        
        # 注册事件处理器
        self._register_event_handlers()
        
        # 设置路由
        self._setup_routes()
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        core_system.register_event_handler(EventType.ITEM_PLACED, self._handle_item_placed)
        core_system.register_event_handler(EventType.ITEM_TAKEN, self._handle_item_taken)
        core_system.register_event_handler(EventType.PROXIMITY_SENSOR, self._handle_proximity_sensor)
        logger.info("Web管理器事件处理器注册完成")
    
    def _handle_item_placed(self, event: SystemEvent):
        """处理物品放置事件"""
        try:
            data = event.data
            message = f"✅ 物品已放置: {data.get('item_name')} (第{data.get('temperature_level')}层)"
            
            # 发送SSE通知
            self.notify_sse_clients("item_placed", {
                "message": message,
                "item_name": data.get("item_name"),
                "category": data.get("category"),
                "temperature_level": data.get("temperature_level")
            })
            
            logger.info(message)
            
        except Exception as e:
            logger.error(f"处理物品放置事件失败: {e}")
    
    def _handle_item_taken(self, event: SystemEvent):
        """处理物品取出事件"""
        try:
            data = event.data
            message = f"📤 物品已取出: {data.get('item_name')} ({data.get('reason')})"
            
            # 发送SSE通知
            self.notify_sse_clients("item_taken", {
                "message": message,
                "item_name": data.get("item_name"),
                "category": data.get("category"),
                "reason": data.get("reason")
            })
            
            logger.info(message)
            
        except Exception as e:
            logger.error(f"处理物品取出事件失败: {e}")
    
    def _handle_proximity_sensor(self, event: SystemEvent):
        """处理接近传感器事件"""
        try:
            data = event.data
            current_time = datetime.now()
            hour = current_time.hour
            
            if 6 <= hour < 12:
                greeting = "早上好！"
                recommendation = "建议食用新鲜水果补充维生素"
            elif 12 <= hour < 18:
                greeting = "下午好！"
                recommendation = "下午茶时间，可以享用冰箱里的新鲜食物"
            else:
                greeting = "晚上好！"
                recommendation = "注意检查过期食物"
            
            message = f"👤 {greeting} {recommendation}"
            
            # 发送SSE通知
            self.notify_sse_clients("proximity_sensor", {
                "message": message,
                "greeting": greeting,
                "recommendation": recommendation
            })
            
            logger.info(message)
            
        except Exception as e:
            logger.error(f"处理接近传感器事件失败: {e}")
    
    def _setup_routes(self):
        """设置Web路由"""
        
        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')
        
        @self.app.route('/api/fridge-status')
        def get_fridge_status():
            """获取冰箱状态API"""
            try:
                # 获取冰箱库存
                inventory_result = ai_processor.get_fridge_inventory()
                
                if not inventory_result["success"]:
                    return jsonify({"error": "获取库存失败"})
                
                # 处理库存数据
                items = []
                level_usage = {str(i): {str(j): False for j in range(4)} for i in range(5)}
                temperature_levels = {str(i): -18 + i * 7 for i in range(5)}  # 模拟温度数据
                
                # 统计数据
                stats = {
                    "total_items": 0,
                    "fresh_items": 0,
                    "long_term_items": 0,
                    "expiring_soon": 0,
                    "expired_items": 0
                }
                
                for item in inventory_result["inventory"]:
                    emoji = self.get_food_emoji(item["name"], item["category"])
                    expiry_progress = self.calculate_expiry_progress(
                        ai_processor.fridge_data["items"][item["item_id"]]["expiry_date"]
                    )
                    temp_info = self.get_temperature_info(item["level"])
                    
                    # 更新统计
                    stats["total_items"] += 1
                    if expiry_progress["status"] == "fresh":
                        stats["fresh_items"] += 1
                    elif expiry_progress["status"] == "long_term":
                        stats["long_term_items"] += 1
                    elif expiry_progress["status"] == "expiring_soon":
                        stats["expiring_soon"] += 1
                    elif expiry_progress["status"] == "expired":
                        stats["expired_items"] += 1
                    
                    # 更新层级使用情况
                    level_usage[str(item["level"])][str(item["section"])] = True
                    
                    items.append({
                        "id": item["item_id"],
                        "name": item["name"],
                        "category": item["category"],
                        "emoji": emoji,
                        "level": item["level"],
                        "section": item["section"],
                        "temp_info": temp_info,  # 修正字段名
                        "expiry_progress": expiry_progress,
                        "added_date": item["added_date"]
                    })
                
                return jsonify({
                    "success": True,
                    "items": items,
                    "stats": stats,
                    "level_usage": level_usage,
                    "temperature_levels": temperature_levels,
                    "total_items": len(items)
                })
                
            except Exception as e:
                logger.error(f"获取冰箱状态失败: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/recommendations')
        def get_recommendations():
            """获取推荐API"""
            try:
                recommendations = ai_processor.get_recommendations()
                
                if not recommendations["success"]:
                    return jsonify({"error": "获取推荐失败"})
                
                # 处理推荐数据
                processed_recommendations = {
                    "success": True,
                    "expired_items": [],
                    "expiring_soon_items": [],
                    "take_out_item": None,
                    "suggestions": recommendations.get("suggestions", [])
                }
                
                # 处理过期物品
                for item in recommendations.get("expired_items", []):
                    emoji = self.get_food_emoji(item["name"], item["category"])
                    processed_recommendations["expired_items"].append({
                        **item,
                        "emoji": emoji
                    })
                
                # 处理即将过期物品
                for item in recommendations.get("expiring_soon_items", []):
                    emoji = self.get_food_emoji(item["name"], item["category"])
                    processed_recommendations["expiring_soon_items"].append({
                        **item,
                        "emoji": emoji
                    })
                
                # 处理推荐取出的物品
                take_out_item = recommendations.get("take_out_item")
                if take_out_item:
                    emoji = self.get_food_emoji(take_out_item["name"], take_out_item["category"])
                    processed_recommendations["take_out_item"] = {
                        **take_out_item,
                        "emoji": emoji
                    }
                
                return jsonify(processed_recommendations)
                
            except Exception as e:
                logger.error(f"获取推荐失败: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/physical-button', methods=['POST'])
        def physical_button():
            """物理按钮API"""
            try:
                data = request.get_json()
                button_type = data.get("button_type")
                
                if button_type == "take_out":
                    # 处理取出物品
                    result = ai_processor.process_item_removal()
                    
                    if result["success"]:
                        return jsonify({
                            "success": True,
                            "message": result.get("message", "物品取出成功"),
                            "item": result.get("item")
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "error": result.get("error", "取出物品失败")
                        })
                else:
                    return jsonify({
                        "success": False,
                        "error": "未知的按钮类型"
                    })
                    
            except Exception as e:
                logger.error(f"处理物理按钮事件失败: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/proximity-sensor', methods=['POST'])
        def proximity_sensor():
            """接近传感器API"""
            try:
                data = request.get_json()
                detected = data.get("detected", False)
                
                if detected:
                    current_time = datetime.now()
                    hour = current_time.hour
                    
                    if 6 <= hour < 12:
                        greeting = "早上好！"
                        recommendation = "建议食用新鲜水果补充维生素"
                    elif 12 <= hour < 18:
                        greeting = "下午好！"
                        recommendation = "下午茶时间，可以享用冰箱里的新鲜食物"
                    else:
                        greeting = "晚上好！"
                        recommendation = "注意检查过期食物"
                    
                    return jsonify({
                        "success": True,
                        "detected": True,
                        "recommendation": {
                            "greeting": greeting,
                            "message": recommendation
                        }
                    })
                else:
                    return jsonify({
                        "success": True,
                        "detected": False
                    })
                    
            except Exception as e:
                logger.error(f"处理接近传感器事件失败: {e}")
                return jsonify({"error": str(e)})
        
        @self.app.route('/api/events')
        def sse():
            """SSE事件流"""
            def generate():
                # 生成客户端ID
                client_id = f"client_{int(time.time())}_{threading.get_ident()}"
                
                # 添加客户端
                with self.sse_lock:
                    self.sse_clients.add(client_id)
                
                try:
                    # 发送连接确认
                    yield f"data: {json.dumps({'type': 'connected', 'client_id': client_id})}\n\n"
                    
                    # 保持连接
                    while True:
                        time.sleep(1)
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"
                        
                except GeneratorExit:
                    # 客户端断开连接
                    with self.sse_lock:
                        self.sse_clients.discard(client_id)
            
            return Response(generate(), mimetype='text/event-stream')
        
        @self.app.route('/api/system-status')
        def get_system_status():
            """获取系统状态API"""
            try:
                status = core_system.get_status()
                return jsonify({
                    "success": True,
                    "system_status": status
                })
            except Exception as e:
                logger.error(f"获取系统状态失败: {e}")
                return jsonify({"error": str(e)})
    
    def get_food_emoji(self, food_name: str, category: str) -> str:
        """获取食物的emoji"""
        # 优先使用具体食物名称的emoji
        if food_name in self.FOOD_EMOJIS:
            return self.FOOD_EMOJIS[food_name]
        
        # 如果没有具体食物名称，使用类别emoji
        if category in self.FOOD_EMOJIS:
            return self.FOOD_EMOJIS[category]
        
        return self.FOOD_EMOJIS["其他"]
    
    def calculate_expiry_progress(self, expiry_date_str: str) -> Dict:
        """计算过期进度条"""
        try:
            expiry_date = datetime.fromisoformat(expiry_date_str)
            current_time = datetime.now()
            
            # 计算剩余天数
            remaining_days = (expiry_date - current_time).days
            
            # 检查是否为长期保存的物品
            if remaining_days > 10000:
                return {
                    "percentage": 100,
                    "status": "long_term",
                    "color": "green",
                    "text": "长期保存"
                }
            
            # 计算总保质期和剩余天数
            total_days = 7  # 假设总保质期为7天
            
            if remaining_days <= 0:
                return {
                    "percentage": 5,
                    "status": "expired",
                    "color": "red",
                    "text": "已过期"
                }
            elif remaining_days <= 1:
                percentage = max(5, (remaining_days / total_days) * 100)
                return {
                    "percentage": percentage,
                    "status": "expiring_soon",
                    "color": "orange",
                    "text": f"剩余{remaining_days}天"
                }
            elif remaining_days <= 3:
                percentage = max(10, (remaining_days / total_days) * 100)
                return {
                    "percentage": percentage,
                    "status": "expiring_soon",
                    "color": "yellow",
                    "text": f"剩余{remaining_days}天"
                }
            elif remaining_days <= 5:
                percentage = max(30, (remaining_days / total_days) * 100)
                return {
                    "percentage": percentage,
                    "status": "fresh",
                    "color": "blue",
                    "text": f"剩余{remaining_days}天"
                }
            else:
                percentage = max(60, (remaining_days / total_days) * 100)
                return {
                    "percentage": percentage,
                    "status": "fresh",
                    "color": "green",
                    "text": f"剩余{remaining_days}天"
                }
        except:
            return {
                "percentage": 0,
                "status": "unknown",
                "color": "gray",
                "text": "未知"
            }
    
    def get_temperature_info(self, level: int) -> Dict:
        """获取温度信息"""
        temperature_levels = {
            0: {"temp": -18, "name": "冷冻", "emoji": "🧊"},
            1: {"temp": -5, "name": "冷冻", "emoji": "🧊"},
            2: {"temp": 2, "name": "冷藏", "emoji": "❄️"},
            3: {"temp": 6, "name": "保鲜", "emoji": "🌡️"},
            4: {"temp": 10, "name": "常温", "emoji": "🌡️"}
        }
        return temperature_levels.get(level, {"temp": 0, "name": "未知", "emoji": "❓"})
    
    def notify_sse_clients(self, event_type: str, data: Dict):
        """通知SSE客户端"""
        message = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        
        with self.sse_lock:
            # 这里可以添加实际的SSE通知逻辑
            logger.info(f"SSE通知: {event_type} -> {len(self.sse_clients)} 个客户端")
    
    def start(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        """启动Web服务"""
        logger.info(f"启动Web服务: http://{host}:{port}")
        # 使用Flask的开发服务器，但设置为非阻塞模式
        self.app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
    
    def start_in_thread(self, host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        """在后台线程中启动Web服务"""
        def run_server():
            try:
                logger.info(f"Web服务器线程启动: http://{host}:{port}")
                self.app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)
            except Exception as e:
                logger.error(f"Web服务器启动失败: {e}")
        
        # 创建并启动线程
        import threading
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        return server_thread
    
    def get_app(self):
        """获取Flask应用"""
        return self.app

# 全局Web管理器实例
web_manager = WebManager() 