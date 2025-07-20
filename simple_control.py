#!/usr/bin/env python
#
# *********     Synchronized Dual Arm Control      *********
#
# 这个示例提供双臂伺服电机的同步控制功能
# 提供简洁的函数接口进行控制
#

import sys
import os
import time
import math
import serial

sys.path.append("..")
from scservo_sdk import *
from move_z_serial import encode_distance_packet, find_available_port

class DualArmController:
    # 定义每个电机的位置限制
    SERVO_LIMITS = {
        1: {"min_pos": 0, "max_pos": 4095, "min_angle": 0, "max_angle": 360},  # 新增的旋转舵机
        2: {"min_pos": 1054, "max_pos": 3045, "min_angle": 0, "max_angle": 180},
        3: {"min_pos": 1030, "max_pos": 3111, "min_angle": 0, "max_angle": 180}
    }
    
    # 定义旋转舵机的分区（6个等分区域）
    ROTATION_SECTORS = {
        1: (0, 60),
        2: (60, 120),
        3: (120, 180),
        4: (180, 240),
        5: (240, 300),
        6: (300, 360)
    }
    
    # 定义Z轴高度分区（3个等分区域）
    Z_SECTORS = {
        1: (0, 20),    # 下层
        2: (20, 40),   # 中层
        3: (40, 60)    # 上层
    }
    
    # 定义机械臂长度（单位：毫米，需要根据实际情况调整）
    ARM_LENGTH = 128  # 假设每个臂长为128mm

    def __init__(self, port="/dev/ttyACM0", baudrate=1000000):
        """初始化双臂控制器"""
        self.servo_ids = [1, 2, 3]  # 现在使用ID 1, 2和3
        self.portHandler = PortHandler(port)
        self.packetHandler = sms_sts(self.portHandler)
        
        # 初始化Z轴串口
        self.z_serial = find_available_port()
        if not self.z_serial:
            raise Exception("无法初始化Z轴控制器")
        
        # 初始化连接
        if not self._initialize_connection(port, baudrate):
            raise Exception("无法初始化控制器")
            
        # 检查电机
        if not self._check_servos():
            raise Exception("无法连接到电机")

        # 启用扭矩并设置默认加速度
        self._set_torque(True)
        self._set_acceleration(255)
        
        # 初始化时直接进入还原态
        success, height = self.restore()
        time.sleep(2)
        if not success:
            raise Exception("无法进入还原态")
            
        print("系统初始化完成")
    
    def _initialize_connection(self, port, baudrate):
        """初始化串口连接"""
        if not self.portHandler.openPort():
            print("无法打开端口")
            return False
        if not self.portHandler.setBaudRate(baudrate):
            print("无法设置波特率")
            return False
        return True
    
    def _check_servos(self):
        """检查两个电机是否都可用"""
        for servo_id in self.servo_ids:
            model_number, result, error = self.packetHandler.ping(servo_id)
            if result != COMM_SUCCESS or error != 0:
                print(f"错误: 无法连接到ID为 {servo_id} 的伺服电机")
                return False
            print(f"已连接到电机 {servo_id}")
        return True

    def start(self):
        """启动双臂系统（启用扭矩并设置默认加速度）"""
        self._set_torque(True)
        self._set_acceleration(255)
        return True

    def stop(self):
        """停止双臂系统（确保还原后再禁用扭矩并关闭端口）"""
        # 先尝试回到还原态
        self.restore()
        time.sleep(0.5)  # 等待还原完成
        # 然后再禁用扭矩并关闭端口
        self._set_torque(False)
        self.portHandler.closePort()
        # 关闭Z轴串口
        if self.z_serial:
            self.z_serial.close()
        print("系统已停止")

    def _set_torque(self, enable):
        """设置两个电机的扭矩状态"""
        value = 1 if enable else 0
        for servo_id in self.servo_ids:
            self.packetHandler.write1ByteTxRx(servo_id, SMS_STS_TORQUE_ENABLE, value)

    def _set_acceleration(self, acceleration):
        """设置两个电机的加速度"""
        for servo_id in self.servo_ids:
            self.packetHandler.write1ByteTxRx(servo_id, SMS_STS_ACC, acceleration)

    def move_to_angle(self, angle2, speed=1000):
        """
        移动到指定角度（以ID=2电机的角度为基准）
        angle2: ID=2电机的目标角度 (0-180度)
        speed: 运动速度
        返回: (是否成功, 当前高度)
        """
        # 确保角度在有效范围内
        angle2 = max(0, min(180, angle2))
        angle3 = 180 - angle2  # 计算ID=3电机的角度
        
        # 计算目标高度
        height = self.calculate_height(angle2)
        
        # 同时设置两个电机的角度
        success2 = self._set_single_angle(2, angle2, speed)
        success3 = self._set_single_angle(3, angle3, speed)
        
        if success2 and success3:
            actual_height = self.get_height()
            return True, actual_height
        return False, None

    def _set_single_angle(self, servo_id, angle, speed):
        """设置单个电机的角度"""
        position = self._angle_to_position(servo_id, angle)
        result, error = self.packetHandler.WritePosEx(servo_id, position, speed, 0)
        return result == COMM_SUCCESS and error == 0

    def _angle_to_position(self, servo_id, angle):
        """角度转换为位置值"""
        limits = self.SERVO_LIMITS[servo_id]
        pos_range = limits["max_pos"] - limits["min_pos"]
        angle_range = limits["max_angle"] - limits["min_angle"]
        return limits["min_pos"] + int((angle / angle_range) * pos_range)

    def _position_to_angle(self, servo_id, position):
        """位置值转换为角度"""
        limits = self.SERVO_LIMITS[servo_id]
        pos_range = limits["max_pos"] - limits["min_pos"]
        angle_range = limits["max_angle"] - limits["min_angle"]
        return limits["min_angle"] + ((position - limits["min_pos"]) / pos_range) * angle_range

    def calculate_height(self, angle2):
        """计算高度（基于ID=2电机的角度）"""
        rad = math.radians(angle2)
        return 2 * self.ARM_LENGTH * math.sin(rad/2)

    def get_height(self):
        """获取当前高度"""
        angle = self.get_angle()
        if angle is not None:
            return self.calculate_height(angle)
        return None

    def get_angle(self):
        """获取当前角度（ID=2电机的角度）"""
        position, result, error = self.packetHandler.ReadPos(2)
        if result == COMM_SUCCESS and error == 0:
            return self._position_to_angle(2, position)
        return None

    def get_status(self):
        """
        获取系统状态
        返回: (当前角度, 当前高度)
        """
        angle = self.get_angle()
        if angle is not None:
            height = self.calculate_height(angle)
            return angle, height
        return None, None

    def restore(self, speed=1000):
        """
        将机械臂恢复到收起态（10度）
        返回: (是否成功, 当前高度)
        """
        print("\n执行还原动作...")
        return self.move_to_angle(10, speed)

    def move_z(self, target_height_mm):
        """
        移动Z轴到指定高度
        target_height_mm: 目标高度（毫米）
        返回: 是否成功
        """
        try:
            # 编码并发送数据包
            packet = encode_distance_packet(target_height_mm)
            self.z_serial.write(packet)
            print(f"已发送Z轴移动指令: {target_height_mm}mm")
            
            # 等待响应
            time.sleep(0.1)
            while self.z_serial.in_waiting:
                response = self.z_serial.readline().decode(errors='ignore').strip()
                print(f"Z轴响应: {response}")
            
            return True
        except Exception as e:
            print(f"Z轴移动失败: {str(e)}")
            return False

    def take_out(self, speed=1000):
        """
        执行取出动作序列：
        1. 向前展开到90度
        2. 向上移动到100mm
        3. 还原到10度
        4. 再次向上移动到150mm
        5. 最后回到还原态
        
        返回: (是否成功, 最终高度)
        """
        print("\n执行取出动作...")
        
        # 1. 向前展开到90度
        success1, height1 = self.move_to_angle(90, speed)
        if not success1:
            self.restore()  # 出错时也尝试回到还原态
            return False, None
        time.sleep(0.5)
        
        # 2. 向上移动到100mm
        if not self.move_z(100):
            self.restore()
            return False, None
        time.sleep(0.3)
        
        # 3. 还原到10度
        success2, height2 = self.restore(speed)
        if not success2:
            return False, None
        time.sleep(0.5)
        
        # 4. 再次向上移动到150mm
        if not self.move_z(150):
            self.restore()
            return False, None
        time.sleep(0.3)

        # 5. 最后回到还原态
        success3, height3 = self.restore(speed)
        if not success3:
            return False, None
        time.sleep(0.5)
            
        return True, self.get_height()

    def take_in(self, speed=1000):
        """
        执行收回动作序列：
        1. 还原到10度
        2. 向下移动到50mm
        3. 向前展开到90度
        4. 再次向下移动到0mm
        5. 最后回到还原态
        
        返回: (是否成功, 最终高度)
        """
        print("\n执行收回动作...")
        
        # 1. 还原到10度
        success1, height1 = self.restore(speed)
        if not success1:
            return False, None
        time.sleep(0.5)
        
        # 2. 向下移动到50mm
        if not self.move_z(50):
            self.restore()
            return False, None
        time.sleep(0.3)
        
        # 3. 向前展开到90度
        success2, height2 = self.move_to_angle(90, speed)
        if not success2:
            self.restore()
            return False, None
        time.sleep(0.5)
        
        # 4. 再次向下移动到0mm
        if not self.move_z(0):
            self.restore()
            return False, None
        time.sleep(0.3)

        # 5. 最后回到还原态
        success3, height3 = self.restore(speed)
        if not success3:
            return False, None
        time.sleep(0.5)
            
        return True, self.get_height()

    def get_current_sector(self):
        """
        获取当前旋转舵机所在的分区
        返回: 分区号（1-6）或 None（如果发生错误）
        """
        position, result, error = self.packetHandler.ReadPos(1)
        if result == COMM_SUCCESS and error == 0:
            angle = self._position_to_angle(1, position)
            for sector, (start, end) in self.ROTATION_SECTORS.items():
                if start <= angle < end:
                    return sector
            # 处理360度的特殊情况
            if angle == 360:
                return 6
        return None

    def move_to_sector(self, sector, speed=1000):
        """
        移动旋转舵机到指定分区的中心位置
        sector: 目标分区（1-6）
        speed: 运动速度
        返回: 是否成功
        """
        if sector not in self.ROTATION_SECTORS:
            print(f"错误: 无效的分区号 {sector}")
            return False
            
        start, end = self.ROTATION_SECTORS[sector]
        target_angle = (start + end) / 2  # 移动到分区中心
        position = self._angle_to_position(1, target_angle)
        
        result, error = self.packetHandler.WritePosEx(1, position, speed, 0)
        success = result == COMM_SUCCESS and error == 0
        
        if success:
            print(f"已移动到分区 {sector} (中心角度: {target_angle}°)")
        else:
            print(f"移动到分区 {sector} 失败")
        
        return success

    def rotate_to_angle(self, angle, speed=1000):
        """
        将旋转舵机转到指定角度
        angle: 目标角度 (0-360度)
        speed: 运动速度
        返回: 是否成功
        """
        # 确保角度在有效范围内
        angle = max(0, min(360, angle))
        position = self._angle_to_position(1, angle)
        
        result, error = self.packetHandler.WritePosEx(1, position, speed, 0)
        success = result == COMM_SUCCESS and error == 0
        
        if success:
            print(f"旋转舵机已转到 {angle}°")
        else:
            print("旋转舵机转动失败")
        
        return success

    def get_z_sector(self):
        """
        获取当前Z轴所在的高度分区
        返回: 分区号（1-3）或 None（如果发生错误）
        """
        try:
            # 等待并读取Z轴响应以获取当前高度
            self.z_serial.write(b'get_height\n')  # 假设有这样的命令
            time.sleep(0.1)
            if self.z_serial.in_waiting:
                response = self.z_serial.readline().decode(errors='ignore').strip()
                try:
                    current_height = float(response)
                    for sector, (start, end) in self.Z_SECTORS.items():
                        if start <= current_height < end:
                            return sector
                    # 处理边界情况
                    if current_height == 60:
                        return 3
                except ValueError:
                    print("无法解析Z轴高度数据")
                    return None
        except Exception as e:
            print(f"获取Z轴分区失败: {str(e)}")
            return None
        return None

    def move_to_z_sector(self, sector, speed=1000):
        """
        移动Z轴到指定分区的中心位置
        sector: 目标分区（1-3）
        speed: 运动速度（暂时未使用）
        返回: 是否成功
        """
        if sector not in self.Z_SECTORS:
            print(f"错误: 无效的Z轴分区号 {sector}")
            return False
            
        start, end = self.Z_SECTORS[sector]
        target_height = (start + end) / 2  # 移动到分区中心
        
        success = self.move_z(target_height)
        
        if success:
            print(f"Z轴已移动到分区 {sector} (中心高度: {target_height}mm)")
        else:
            print(f"Z轴移动到分区 {sector} 失败")
        
        return success

# 使用示例
if __name__ == "__main__":
    try:
        print("=== 系统启动 ===")
        arm = DualArmController()
        
        # 测试旋转舵机功能
        print("\n测试旋转舵机分区功能...")
        for sector in range(1, 7):
            arm.move_to_sector(sector)
            time.sleep(1)
            current_sector = arm.get_current_sector()
            print(f"当前在分区 {current_sector}")
        
        # 测试Z轴分区功能
        print("\n测试Z轴分区功能...")
        for sector in range(1, 4):
            arm.move_to_z_sector(sector)
            time.sleep(1)
            current_z_sector = arm.get_z_sector()
            print(f"当前在Z轴分区 {current_z_sector}")
        
        # 执行取出动作
        success, height = arm.take_out()
        if not success:
            print("取出动作失败")
            sys.exit(1)
        print(f"取出完成，高度: {height:.1f}mm")
        
        # 等待5秒
        time.sleep(5)
        
        # 获取当前状态
        angle, height = arm.get_status()
        if angle is not None and height is not None:
            print(f"当前状态: {angle:.1f}°, {height:.1f}mm")
        
        # 执行收回动作
        success, height = arm.take_in()
        if not success:
            print("收回动作失败")
            sys.exit(1)
        print(f"收回完成，高度: {height:.1f}mm")
        
        # 等待5秒
        time.sleep(5)
        
        print("=== 执行完成 ===")
                
    except Exception as e:
        print(f"错误: {str(e)}")
    finally:
        arm.stop() 