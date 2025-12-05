#!/usr/bin/env python3
"""
蒙特卡洛住宅自动化生成及优化系统启动脚本
"""

import sys
import os
import traceback

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 9):
        print("错误：需要Python 3.9或更高版本")
        print(f"当前版本：{sys.version}")
        sys.exit(1)

def check_dependencies():
    """检查依赖库"""
    required_packages = [
        'numpy',
        'matplotlib',
        'tkinter',
        'PIL'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'PIL':
                from PIL import Image
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("错误：缺少以下依赖库：")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖：")
        print("pip install -r requirements.txt")
        sys.exit(1)

def setup_environment():
    """设置运行环境"""
    # 添加当前目录到Python路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 设置环境变量
    os.environ['PYTHONUNBUFFERED'] = '1'

def main():
    """主函数"""
    print("=" * 60)
    print("蒙特卡洛住宅自动化生成及优化系统")
    print("=" * 60)
    print()
    
    # 检查环境
    print("检查运行环境...")
    check_python_version()
    check_dependencies()
    setup_environment()
    print("✓ 环境检查通过")
    print()
    
    try:
        # 导入主应用程序
        print("启动应用程序...")
        from main_application import MainApplication
        
        # 创建并运行应用
        app = MainApplication()
        app.run()
        
    except KeyboardInterrupt:
        print("\n\n用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n启动失败：{str(e)}")
        print("\n详细错误信息：")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()