#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧冰箱系统启动脚本
使用新的模块化架构
"""

import sys
import os

# 添加Agent目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'Agent'))

def main():
    """主函数"""
    try:
        from Agent.system_launcher import main as launch_system
        launch_system()
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保所有依赖模块都已正确安装")
        sys.exit(1)
    except Exception as e:
        print(f"系统启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 