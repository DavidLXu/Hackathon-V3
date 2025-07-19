# 智慧冰箱系统

## 概述

这是一个基于事件驱动架构的智慧冰箱系统，采用模块化设计，支持物品识别、智能推荐、人脸检测等功能。

## 系统架构

### 核心组件

1. **核心系统调度器** (`Agent/core_system.py`)
   - 系统的中央控制器
   - 负责事件分发和模块协调
   - 提供事件总线机制

2. **硬件管理器** (`Sensor/hardware_manager.py`)
   - 统一管理所有外设硬件
   - 支持GPIO按钮、摄像头、人脸检测
   - 提供硬件抽象接口

3. **AI处理器** (`Agent/ai_processor.py`)
   - 专门处理AI相关功能
   - 图像识别（Qwen-VL）
   - 智能推荐系统

4. **Web服务管理器** (`Agent/web_manager.py`)
   - 处理Web界面和API服务
   - 提供RESTful API
   - 实时事件推送

5. **系统启动器** (`Agent/system_launcher.py`)
   - 统一启动和管理所有模块
   - 系统监控和健康检查
   - 优雅关闭处理

### 硬件组件

- **两个按钮**:
  - GPIO 16: 绿色按钮 - 放入物品
  - GPIO 17: 红色按钮 - 取出物品

- **两个摄像头**:
  - 内部摄像头 (Camera 0): 用于物品识别
  - 外部摄像头 (Camera 1): 用于人脸检测

## 快速开始

### 环境要求

- Python 3.7+
- OpenCV
- Flask
- RPi.GPIO (在Raspberry Pi上)
- 摄像头设备

### 安装依赖

```bash
pip install opencv-python flask dashscope numpy
```

### 启动系统

```bash
# 启动新系统
python start_new_system.py

# 或者直接启动系统启动器
python Agent/system_launcher.py
```

### 测试系统

```bash
# 运行架构测试
python test_new_architecture.py
```

## 功能特性

### 1. 物品管理
- 自动物品识别和分类
- 智能温度层分配
- 过期时间管理
- 库存状态监控

### 2. 智能推荐
- 基于过期时间的推荐
- 个性化使用建议
- 实时状态提醒

### 3. 人脸检测
- 接近传感器功能
- 个性化问候
- 智能推荐触发

### 4. Web界面
- 实时库存显示
- 过期进度条
- 温度层信息
- 事件通知

## 事件驱动架构

系统采用事件驱动架构，主要事件类型：

- `BUTTON_PRESS`: 按钮事件
- `CAMERA_CAPTURE`: 拍照事件
- `ITEM_PLACED`: 物品放置事件
- `ITEM_TAKEN`: 物品取出事件
- `PROXIMITY_SENSOR`: 接近传感器事件

## 开发模式

### 硬件模拟器

在没有实际硬件的情况下，可以使用硬件模拟器进行测试：

```python
from Sensor.hardware_simulator import hardware_simulator, ButtonType

# 模拟按钮按下
hardware_simulator.simulate_button_press(ButtonType.PLACE_ITEM)

# 模拟人脸检测
hardware_simulator.simulate_face_detection()
```

### 调试模式

```bash
# 启用调试模式
python Agent/system_launcher.py --debug
```

## 文件结构

```
HackathonV2/
├── Agent/                    # 核心业务模块
│   ├── core_system.py       # 核心系统调度器
│   ├── ai_processor.py      # AI处理器
│   ├── web_manager.py       # Web服务管理器
│   ├── system_launcher.py   # 系统启动器
│   └── templates/           # Web模板
├── Sensor/                   # 硬件管理模块
│   ├── hardware_manager.py  # 硬件管理器
│   └── hardware_simulator.py # 硬件模拟器
├── uploads/                  # 上传文件目录
├── logs/                     # 日志目录
├── start_new_system.py      # 系统启动脚本
├── test_new_architecture.py # 架构测试脚本
└── ARCHITECTURE.md          # 详细架构文档
```

## API接口

### Web API

- `GET /api/fridge-status`: 获取冰箱状态
- `GET /api/recommendations`: 获取推荐
- `POST /api/physical-button`: 物理按钮事件
- `POST /api/proximity-sensor`: 接近传感器事件
- `GET /api/system-status`: 获取系统状态

### 事件API

- `EventType.BUTTON_PRESS`: 按钮事件
- `EventType.CAMERA_CAPTURE`: 拍照事件
- `EventType.ITEM_PLACED`: 物品放置事件
- `EventType.ITEM_TAKEN`: 物品取出事件
- `EventType.PROXIMITY_SENSOR`: 接近传感器事件

## 监控和日志

- 系统日志: `logs/system.log`
- Web界面: `http://localhost:8080`
- 系统状态API: `/api/system-status`

## 故障排除

### 常见问题

1. **硬件管理器不可用**
   - 检查GPIO权限
   - 确认摄像头连接
   - 查看硬件日志

2. **AI识别失败**
   - 检查API密钥
   - 确认网络连接
   - 验证图片格式

3. **Web服务无法访问**
   - 检查端口占用
   - 确认防火墙设置
   - 查看Web日志

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

---

*更多详细信息请参考 [ARCHITECTURE.md](ARCHITECTURE.md)* 