# 智慧冰箱系统架构重构

## 概述

本次重构将原有的单体架构重新组织为模块化的事件驱动架构，提高了代码的可维护性、可扩展性和可测试性。

## 新架构设计

### 核心组件

#### 1. 核心系统调度器 (`Agent/core_system.py`)
- **职责**: 系统的中央控制器，负责事件分发和模块协调
- **功能**:
  - 事件类型定义和管理
  - 事件处理器注册和分发
  - 系统状态监控
  - 异步事件处理

#### 2. 硬件管理器 (`Sensor/hardware_manager.py`)
- **职责**: 统一管理所有外设硬件
- **功能**:
  - GPIO按钮管理（放入/取出按钮）
  - 摄像头管理（内部/外部摄像头）
  - 人脸检测和距离估算
  - 硬件事件触发

#### 3. AI处理器 (`Agent/ai_processor.py`)
- **职责**: 专门处理AI相关功能
- **功能**:
  - 图像识别（Qwen-VL）
  - 物品分类和属性识别
  - 冰箱库存管理
  - 智能推荐系统

#### 4. Web服务管理器 (`Agent/web_manager.py`)
- **职责**: 处理Web界面和API服务
- **功能**:
  - RESTful API提供
  - 实时事件推送（SSE）
  - 用户界面数据格式化
  - 系统状态展示

#### 5. 系统启动器 (`Agent/system_launcher.py`)
- **职责**: 统一启动和管理所有模块
- **功能**:
  - 模块初始化和启动
  - 系统监控和健康检查
  - 优雅关闭处理
  - 错误恢复机制

## 事件驱动架构

### 事件类型

```python
class EventType(Enum):
    BUTTON_PRESS = "button_press"        # 按钮事件
    FACE_DETECTION = "face_detection"    # 人脸检测事件
    CAMERA_CAPTURE = "camera_capture"    # 拍照事件
    ITEM_PLACED = "item_placed"         # 物品放置事件
    ITEM_TAKEN = "item_taken"           # 物品取出事件
    PROXIMITY_SENSOR = "proximity_sensor" # 接近传感器事件
    SYSTEM_ERROR = "system_error"        # 系统错误事件
```

### 事件流程

1. **放入物品流程**:
   ```
   按钮按下 → 硬件管理器 → 拍照 → AI处理器 → 物品识别 → 添加到冰箱 → Web通知
   ```

2. **取出物品流程**:
   ```
   按钮按下 → 硬件管理器 → AI处理器 → 智能推荐 → 取出物品 → Web通知
   ```

3. **人脸检测流程**:
   ```
   摄像头检测 → 硬件管理器 → 距离估算 → 接近传感器事件 → Web个性化推荐
   ```

## 外设管理

### 硬件组件

1. **两个按钮**:
   - GPIO 16: 绿色按钮 - 放入物品
   - GPIO 17: 红色按钮 - 取出物品

2. **两个摄像头**:
   - 内部摄像头 (Camera 0): 用于物品识别
   - 外部摄像头 (Camera 1): 用于人脸检测

### 硬件抽象层

硬件管理器提供了统一的硬件抽象接口：

```python
class HardwareManager:
    def capture_image(self, camera_type: CameraType) -> Optional[str]
    def detect_faces(self) -> bool
    def start_face_detection_monitor(self)
    def get_camera_status(self) -> Dict
```

## 模块间通信

### 事件总线

所有模块通过核心系统的事件总线进行通信：

```python
# 发送事件
event = core_system.create_event(EventType.BUTTON_PRESS, "source", data)
core_system.emit_event(event)

# 注册事件处理器
core_system.register_event_handler(EventType.CAMERA_CAPTURE, handler)
```

### 数据流

```
硬件事件 → 硬件管理器 → 核心系统 → AI处理器/Web管理器
                ↓
           事件总线
                ↓
        各模块事件处理器
```

## 优势

### 1. 解耦合
- 各模块职责清晰，相互独立
- 通过事件总线通信，降低耦合度
- 便于单独测试和维护

### 2. 可扩展性
- 新增功能只需添加新模块和事件处理器
- 硬件变化只需修改硬件管理器
- 支持插件化架构

### 3. 可维护性
- 代码结构清晰，易于理解
- 错误定位更容易
- 支持热插拔模块

### 4. 可测试性
- 每个模块可以独立测试
- 可以模拟硬件事件
- 支持单元测试和集成测试

## 部署和运行

### 启动方式

```bash
# 启动新系统
python start_new_system.py

# 或者直接启动系统启动器
python Agent/system_launcher.py
```

### 配置要求

1. **Python环境**: Python 3.7+
2. **依赖包**: 见 `requirements.txt`
3. **硬件要求**: 
   - Raspberry Pi (推荐)
   - 摄像头
   - GPIO按钮
4. **网络**: 用于Web界面访问

### 监控和日志

- 系统日志: `logs/system.log`
- Web界面: `http://localhost:8080`
- 系统状态API: `/api/system-status`

## 迁移指南

### 从旧架构迁移

1. **停止旧系统**:
   ```bash
   # 停止原有的web_interface.py
   pkill -f web_interface.py
   ```

2. **启动新系统**:
   ```bash
   python start_new_system.py
   ```

3. **验证功能**:
   - 访问Web界面
   - 测试按钮功能
   - 检查人脸检测

### 兼容性

- 保持原有的Web API接口
- 保持原有的数据文件格式
- 支持渐进式迁移

## 故障排除

### 常见问题

1. **硬件管理器不可用**:
   - 检查GPIO权限
   - 确认摄像头连接
   - 查看硬件日志

2. **AI识别失败**:
   - 检查API密钥
   - 确认网络连接
   - 验证图片格式

3. **Web服务无法访问**:
   - 检查端口占用
   - 确认防火墙设置
   - 查看Web日志

### 调试模式

```python
# 在system_launcher.py中启用调试模式
web_manager.start(debug=True)
```

## 未来扩展

### 计划中的功能

1. **多用户支持**: 用户识别和个性化
2. **云端同步**: 数据备份和远程访问
3. **智能推荐**: 基于使用习惯的推荐
4. **语音交互**: 语音命令和反馈
5. **移动应用**: 手机APP支持

### 架构扩展点

1. **插件系统**: 支持第三方插件
2. **微服务架构**: 支持分布式部署
3. **容器化**: Docker支持
4. **监控系统**: 更完善的监控和告警

---

*本文档描述了智慧冰箱系统的重构架构，如有问题请参考代码注释或联系开发团队。* 