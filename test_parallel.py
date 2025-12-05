#!/usr/bin/env python3
"""
测试并行优化功能
"""

import sys
import os
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_parallel_optimization():
    """测试并行优化"""
    try:
        from core_data_structures import Layout, RoomType, Rectangle, LayoutConstraints
        from monte_carlo_engine import MonteCarloConfig, ParallelMonteCarloOptimizer
        from evaluation_system import EvaluationConfig, MultiDimensionalEvaluator
        
        print("设置测试环境...")
        
        # 创建配置
        config = MonteCarloConfig(
            max_iterations=100,
            population_size=20,
            mutation_rate=0.3,
            crossover_rate=0.7
        )
        
        evaluation_config = EvaluationConfig()
        constraints = LayoutConstraints()
        
        # 创建评估函数
        def evaluation_function(layout):
            evaluator = MultiDimensionalEvaluator(evaluation_config)
            results = evaluator.evaluate(layout)
            return results.get('total', {}).get('weighted_score', 0)
        
        # 创建并行优化器
        print("创建并行优化器...")
        optimizer = ParallelMonteCarloOptimizer(
            config, 
            evaluation_function,
            2,  # 使用2个线程避免资源竞争
            constraints
        )
        
        # 设置优化参数
        bounds = Rectangle(0, 0, 15, 12)
        room_requirements = {
            RoomType.LIVING_ROOM: 1,
            RoomType.BEDROOM: 1,
            RoomType.KITCHEN: 1,
            RoomType.BATHROOM: 1
        }
        
        print("开始并行优化...")
        start_time = time.time()
        
        best_layout = optimizer.optimize(bounds, room_requirements, room_requirements)
        
        end_time = time.time()
        
        # 评估结果
        final_score = evaluation_function(best_layout)
        
        print(f"✓ 并行优化完成，耗时: {end_time - start_time:.3f}秒")
        print(f"  最佳得分: {final_score:.3f}")
        print(f"  房间数量: {len(best_layout.rooms)}")
        print(f"  空间利用率: {best_layout.utilization_rate:.2%}")
        
        return True
        
    except Exception as e:
        print(f"✗ 并行优化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_standard_optimization():
    """测试标准优化作为对比"""
    try:
        from core_data_structures import Layout, RoomType, Rectangle, LayoutConstraints
        from monte_carlo_engine import MonteCarloConfig, MonteCarloOptimizer
        from evaluation_system import EvaluationConfig, MultiDimensionalEvaluator
        
        print("测试标准优化（对比）...")
        
        # 创建配置
        config = MonteCarloConfig(
            max_iterations=50,  # 减少迭代次数
            population_size=10,
            mutation_rate=0.3,
            crossover_rate=0.7
        )
        
        evaluation_config = EvaluationConfig()
        constraints = LayoutConstraints()
        
        # 创建评估函数
        def evaluation_function(layout):
            evaluator = MultiDimensionalEvaluator(evaluation_config)
            results = evaluator.evaluate(layout)
            return results.get('total', {}).get('weighted_score', 0)
        
        # 创建标准优化器
        optimizer = MonteCarloOptimizer(config, evaluation_function, constraints)
        
        # 设置优化参数
        bounds = Rectangle(0, 0, 15, 12)
        room_requirements = {
            RoomType.LIVING_ROOM: 1,
            RoomType.BEDROOM: 1,
            RoomType.KITCHEN: 1,
            RoomType.BATHROOM: 1
        }
        
        print("开始标准优化...")
        start_time = time.time()
        
        best_layout = optimizer.optimize(bounds, room_requirements, room_requirements)
        
        end_time = time.time()
        
        # 评估结果
        final_score = evaluation_function(best_layout)
        
        print(f"✓ 标准优化完成，耗时: {end_time - start_time:.3f}秒")
        print(f"  最佳得分: {final_score:.3f}")
        print(f"  房间数量: {len(best_layout.rooms)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 标准优化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("并行优化功能测试")
    print("=" * 50)
    
    # 测试标准优化
    print("\n1. 标准优化测试")
    print("-" * 30)
    if not test_standard_optimization():
        print("标准优化失败，无法继续")
        return
    
    # 测试并行优化
    print("\n2. 并行优化测试")
    print("-" * 30)
    if not test_parallel_optimization():
        print("并行优化失败")
        return
    
    print("\n" + "=" * 50)
    print("✓ 所有优化测试通过！")
    print("并行优化功能正常工作。")
    
    print("\n现在可以安全地运行主GUI应用程序：")
    print("python main_application.py")

if __name__ == "__main__":
    main()