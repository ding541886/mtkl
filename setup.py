#!/usr/bin/env python3
"""
蒙特卡洛住宅自动化生成及优化系统安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# 读取requirements文件
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # 移除注释
                    if '#' in line:
                        line = line.split('#')[0].strip()
                    if line:
                        requirements.append(line)
    return requirements

setup(
    name="residence-automation-optimizer",
    version="1.0.0",
    author="住宅自动化开发团队",
    author_email="support@example.com",
    description="基于蒙特卡洛算法的智能化住宅平面图生成和优化系统",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/residence-automation-optimizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Scientific/Engineering :: Architecture",
    ],
    python_requires=">=3.9",
    install_requires=read_requirements(),
    extras_require={
        "cad": ["ezdxf>=0.18.0"],
        "pdf": ["reportlab>=3.6.0"],
        "full": ["ezdxf>=0.18.0", "reportlab>=3.6.0"],
    },
    entry_points={
        "console_scripts": [
            "residence-optimizer=main_application:main",
            "residence-demo=demo:main",
        ],
        "gui_scripts": [
            "residence-optimizer-gui=main_application:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md", "*.txt", "*.png", "*.jpg", "*.gif"],
    },
    zip_safe=False,
    keywords="monte-carlo, residence, layout, optimization, architecture, floor-plan, ai",
    project_urls={
        "Bug Reports": "https://github.com/example/residence-automation-optimizer/issues",
        "Source": "https://github.com/example/residence-automation-optimizer",
        "Documentation": "https://github.com/example/residence-automation-optimizer/wiki",
    },
)