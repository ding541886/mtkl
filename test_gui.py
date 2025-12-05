#!/usr/bin/env python3
"""
测试GUI应用程序是否能正常启动
"""

import sys
import os
import tkinter as tk

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入是否正常"""
    try:
        from main_application import MainApplication
        print("✓ 主应用程序导入成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_optimization_setup():
    """测试优化设置是否正常"""
    try:
        from main_application import MainApplication
        from core_data_structures import LayoutConstraints
        
        # 创建应用实例
        app = MainApplication()
        print("✓ 应用程序实例创建成功")
        
        # 测试快速开始参数
        small_params = app._get_small_apartment_params()
        standard_params = app._get_standard_house_params()
        large_params = app._get_large_house_params()
        
        print("✓ 预设参数获取成功")
        print(f"  - 小户型: {small_params['layout']['total_width']}x{small_params['layout']['total_height']}")
        print(f"  - 标准户型: {standard_params['layout']['total_width']}x{standard_params['layout']['total_height']}")
        print(f"  - 大户型: {large_params['layout']['total_width']}x{large_params['layout']['total_height']}")
        
        # 不运行主循环，只测试初始化
        app.root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ 优化设置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("GUI应用程序测试")
    print("=" * 40)
    
    # 测试导入
    if not test_imports():
        print("导入测试失败，无法继续")
        return
    
    # 测试优化设置
    if not test_optimization_setup():
        print("优化设置测试失败")
        return
    
    print("\n" + "=" * 40)
    print("✓ 所有测试通过！")
    print("GUI应用程序应该可以正常启动。")
    print("\n要启动完整GUI，请运行:")
    print("python main_application.py")
    print("\n或者双击: 启动程序.bat")

if __name__ == "__main__":
    main()