#!/usr/bin/env python3
"""
演示脚本：展示蒙特卡洛住宅生成系统的核心功能
"""

import sys
import os
import time
from typing import Dict

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def import_modules():
    """导入所需模块"""
    try:
        from core_data_structures import Layout, Room, RoomType, Rectangle
        from monte_carlo_engine import MonteCarloOptimizer, MonteCarloConfig
        from evaluation_system import MultiDimensionalEvaluator
        from visualization_engine import LayoutRenderer
        from export_system import ExportManager
        
        # 将类添加到全局命名空间以便使用
        globals().update({
            'Layout': Layout,
            'Room': Room,
            'RoomType': RoomType,
            'Rectangle': Rectangle,
            'MonteCarloOptimizer': MonteCarloOptimizer,
            'MonteCarloConfig': MonteCarloConfig,
            'MultiDimensionalEvaluator': MultiDimensionalEvaluator,
            'LayoutRenderer': LayoutRenderer,
            'ExportManager': ExportManager
        })
        
        return True
    except ImportError as e:
        print(f"导入模块失败: {e}")
        return False

def create_test_layout() -> Layout:
    """创建测试布局"""
    print("创建测试布局...")
    
    # 创建布局边界
    bounds = Rectangle(0, 0, 20, 15)
    layout = Layout(bounds)
    
    # 添加房间
    living_room = Room(RoomType.LIVING_ROOM, Rectangle(2, 2, 8, 6))
    bedroom1 = Room(RoomType.BEDROOM, Rectangle(12, 2, 6, 5))
    bedroom2 = Room(RoomType.BEDROOM, Rectangle(12, 8, 6, 5))
    kitchen = Room(RoomType.KITCHEN, Rectangle(2, 8, 5, 4))
    bathroom = Room(RoomType.BATHROOM, Rectangle(8, 8, 3, 3))
    dining_room = Room(RoomType.DINING_ROOM, Rectangle(8, 2, 3, 4))
    
    # 添加到布局
    layout.add_room(living_room)
    layout.add_room(bedroom1)
    layout.add_room(bedroom2)
    layout.add_room(kitchen)
    layout.add_room(bathroom)
    layout.add_room(dining_room)
    
    # 添加门窗
    living_room.add_window(Rectangle(2, 2, 2, 0.2))
    living_room.add_door(Rectangle(8, 4, 0.8, 0.1))
    
    bedroom1.add_window(Rectangle(12, 2, 2, 0.2))
    bedroom1.add_door(Rectangle(16, 6, 0.8, 0.1))
    
    bedroom2.add_window(Rectangle(12, 8, 2, 0.2))
    bedroom2.add_door(Rectangle(16, 10, 0.8, 0.1))
    
    kitchen.add_window(Rectangle(2, 8, 1, 0.2))
    kitchen.add_door(Rectangle(5, 10, 0.8, 0.1))
    
    bathroom.add_door(Rectangle(8, 10, 0.8, 0.1))
    
    dining_room.add_door(Rectangle(10, 4, 0.8, 0.1))
    
    print(f"✓ 创建了包含 {len(layout.rooms)} 个房间的布局")
    return layout

def test_evaluation(layout: Layout):
    """测试评估系统"""
    print("\n测试评估系统...")
    
    # 创建评估器
    evaluator = MultiDimensionalEvaluator()
    
    # 评估布局
    start_time = time.time()
    total_score = evaluator.evaluate(layout)
    detailed_results = evaluator.evaluate_detailed(layout)
    end_time = time.time()
    
    print(f"✓ 评估完成，耗时: {end_time - start_time:.3f}秒")
    print(f"总分: {total_score:.3f}")
    print("详细评估结果:")
    
    # 显示各维度得分
    dimension_names = {
        'spaceefficiency': '空间效率',
        'lighting': '采光效果',
        'ventilation': '通风效果',
        'circulation': '动线效率',
        'comfort': '舒适度'
    }
    
    for key, result in detailed_results.items():
        if key == 'total':
            print(f"  {key}: {result['weighted_score']:.3f}")
        elif key in dimension_names:
            name = dimension_names[key]
            print(f"  {name}: {result['score']:.3f} (权重: {result['weight']:.2f})")
    
    return detailed_results

def test_visualization(layout: Layout, evaluation_results: Dict):
    """测试可视化系统"""
    print("\n测试可视化系统...")
    
    try:
        # 创建渲染器
        renderer = LayoutRenderer()
        
        # 渲染布局
        start_time = time.time()
        renderer.render_layout(layout, show_evaluation=True, 
                             evaluation_results=evaluation_results)
        end_time = time.time()
        
        print(f"✓ 可视化完成，耗时: {end_time - start_time:.3f}秒")
        
        # 保存图像
        output_file = "demo_layout.png"
        renderer.save_image(output_file, dpi=150)
        print(f"✓ 图像已保存为: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ 可视化失败: {e}")
        return False

def test_export(layout: Layout, evaluation_results: Dict):
    """测试导出系统"""
    print("\n测试导出系统...")
    
    try:
        # 创建导出管理器
        export_manager = ExportManager()
        
        # 测试各种格式导出
        formats = ['PNG', 'SVG', 'JSON']
        results = {}
        
        for format_type in formats:
            filename = f"demo_layout.{format_type.lower()}"
            start_time = time.time()
            success = export_manager.export(layout, filename, format_type, evaluation_results)
            end_time = time.time()
            
            results[format_type] = success
            status = "成功" if success else "失败"
            print(f"  {format_type}: {status} (耗时: {end_time - start_time:.3f}秒)")
        
        return results
        
    except Exception as e:
        print(f"✗ 导出失败: {e}")
        return {}

def test_monte_carlo_optimization():
    """测试蒙特卡洛优化"""
    print("\n测试蒙特卡洛优化算法...")
    
    try:
        from monte_carlo_engine import MonteCarloConfig
        from evaluation_system import EvaluationConfig
        
        # 配置参数
        config = MonteCarloConfig(
            max_iterations=100,  # 减少迭代次数用于演示
            population_size=20,
            mutation_rate=0.3,
            crossover_rate=0.7
        )
        
        eval_config = EvaluationConfig()
        
        # 创建评估器
        def evaluation_function(layout):
            evaluator = MultiDimensionalEvaluator(eval_config)
            return evaluator.evaluate(layout)
        
        # 创建约束和优化器
        from core_data_structures import LayoutConstraints
        constraints = LayoutConstraints()
        optimizer = MonteCarloOptimizer(config, evaluation_function, constraints)
        
        # 设置优化参数
        bounds = Rectangle(0, 0, 18, 12)
        room_requirements = {
            RoomType.LIVING_ROOM: 1,
            RoomType.BEDROOM: 2,
            RoomType.KITCHEN: 1,
            RoomType.BATHROOM: 1
        }
        
        print("开始优化（100次迭代，20个个体）...")
        start_time = time.time()
        
        best_layout = optimizer.optimize(bounds, room_requirements, room_requirements)
        
        end_time = time.time()
        print(f"✓ 优化完成，耗时: {end_time - start_time:.3f}秒")
        print(f"  最佳得分: {optimizer.best_score:.3f}")
        print(f"  房间数量: {len(best_layout.rooms)}")
        print(f"  空间利用率: {best_layout.utilization_rate:.2%}")
        
        return best_layout, optimizer.best_score
        
    except Exception as e:
        print(f"✗ 优化失败: {e}")
        return None, 0

def main():
    """主演示函数"""
    print("=" * 60)
    print("蒙特卡洛住宅自动化生成及优化系统 - 功能演示")
    print("=" * 60)
    
    # 检查依赖
    if not import_modules():
        print("请先安装所需依赖: pip install -r requirements.txt")
        return
    
    # 1. 测试基本布局创建
    print("\n" + "="*40)
    print("1. 基本布局创建测试")
    print("="*40)
    layout = create_test_layout()
    
    # 2. 测试评估系统
    print("\n" + "="*40)
    print("2. 评估系统测试")
    print("="*40)
    evaluation_results = test_evaluation(layout)
    
    # 3. 测试可视化
    print("\n" + "="*40)
    print("3. 可视化系统测试")
    print("="*40)
    viz_success = test_visualization(layout, evaluation_results)
    
    # 4. 测试导出功能
    print("\n" + "="*40)
    print("4. 导出功能测试")
    print("="*40)
    export_results = test_export(layout, evaluation_results)
    
    # 5. 测试蒙特卡洛优化
    print("\n" + "="*40)
    print("5. 蒙特卡洛优化测试")
    print("="*40)
    optimized_layout, best_score = test_monte_carlo_optimization()
    
    # 6. 总结
    print("\n" + "="*60)
    print("演示总结")
    print("="*60)
    
    print(f"✓ 布局创建: 成功")
    print(f"✓ 评估系统: 成功")
    print(f"✓ 可视化系统: {'成功' if viz_success else '失败'}")
    print(f"✓ 导出功能: {sum(export_results.values())}/{len(export_results)} 格式成功")
    
    if optimized_layout:
        print(f"✓ 蒙特卡洛优化: 成功 (得分: {best_score:.3f})")
        
        # 保存优化结果
        try:
            evaluator = MultiDimensionalEvaluator()
            opt_score = evaluator.evaluate(optimized_layout)
            opt_results = evaluator.evaluate_detailed(optimized_layout)
            renderer = LayoutRenderer()
            renderer.render_layout(optimized_layout, True, opt_results)
            renderer.save_image("optimized_layout.png", dpi=150)
            print("✓ 优化结果已保存为: optimized_layout.png")
        except Exception as e:
            print(f"✗ 保存优化结果失败: {e}")
    else:
        print("✗ 蒙特卡洛优化: 失败")
    
    print(f"\n生成的文件:")
    for file in ["demo_layout.png", "demo_layout.svg", "demo_layout.json", "optimized_layout.png"]:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  {file}: {size} 字节")
    
    print(f"\n演示完成！")
    print(f"要运行完整的GUI应用程序，请执行: python main_application.py")

if __name__ == "__main__":
    main()