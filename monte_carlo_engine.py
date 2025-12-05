"""
蒙特卡洛算法引擎
实现基于蒙特卡洛方法的住宅布局随机生成和迭代优化
"""

import random
import math
import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import time

from core_data_structures import (
    Layout, Room, RoomType, Rectangle, Point, RoomTemplate, 
    LayoutConstraints, OptimizationTarget
)


@dataclass
class MonteCarloConfig:
    """蒙特卡洛算法配置"""
    max_iterations: int = 10000          # 最大迭代次数
    population_size: int = 50            # 种群大小
    mutation_rate: float = 0.3           # 变异率
    crossover_rate: float = 0.7          # 交叉率
    temperature_start: float = 100.0     # 模拟退火起始温度
    temperature_end: float = 0.01        # 模拟退火结束温度
    cooling_rate: float = 0.995          # 冷却速率
    elite_ratio: float = 0.2             # 精英保留比例
    convergence_threshold: float = 1e-6   # 收敛阈值
    max_no_improvement: int = 100        # 最大无改进次数
    
    # 布局生成参数
    min_room_area: float = 5.0           # 最小房间面积
    max_room_area: float = 50.0          # 最大房间面积
    min_aspect_ratio: float = 0.5        # 最小宽高比
    max_aspect_ratio: float = 2.0        # 最大宽高比
    wall_thickness: float = 0.2          # 墙体厚度


class RandomLayoutGenerator:
    """随机布局生成器"""
    
    def __init__(self, config: MonteCarloConfig, constraints: Optional[LayoutConstraints] = None):
        self.config = config
        self.constraints = constraints or LayoutConstraints()
        self.room_templates = self._create_room_templates()
    
    def _create_room_templates(self) -> Dict[RoomType, RoomTemplate]:
        """创建房间模板"""
        templates = {
            RoomType.LIVING_ROOM: RoomTemplate(RoomType.LIVING_ROOM, 15, 40, 0.8, 1.5),
            RoomType.BEDROOM: RoomTemplate(RoomType.BEDROOM, 8, 25, 0.7, 1.4),
            RoomType.KITCHEN: RoomTemplate(RoomType.KITCHEN, 6, 20, 0.6, 1.8),
            RoomType.BATHROOM: RoomTemplate(RoomType.BATHROOM, 3, 12, 0.5, 2.0),
            RoomType.DINING_ROOM: RoomTemplate(RoomType.DINING_ROOM, 10, 25, 0.7, 1.6),
            RoomType.STUDY: RoomTemplate(RoomType.STUDY, 6, 18, 0.6, 1.5),
            RoomType.BALCONY: RoomTemplate(RoomType.BALCONY, 4, 15, 0.3, 3.0),
            RoomType.STORAGE: RoomTemplate(RoomType.STORAGE, 2, 8, 0.4, 2.5),
            RoomType.HALLWAY: RoomTemplate(RoomType.HALLWAY, 3, 15, 0.2, 5.0),
        }
        return templates
    
    def generate_random_layout(self, bounds: Rectangle, 
                             room_requirements: Dict[RoomType, int]) -> Layout:
        """生成随机布局"""
        layout = Layout(bounds)
        
        # 生成房间列表
        rooms_to_place = []
        for room_type, count in room_requirements.items():
            for _ in range(count):
                template = self.room_templates.get(room_type)
                if template:
                    width, height = template.generate_random_size()
                    rooms_to_place.append((room_type, width, height))
        
        # 随机打乱房间顺序
        random.shuffle(rooms_to_place)
        
        # 使用矩形分割算法放置房间
        self._place_rooms_rectangular_split(layout, rooms_to_place)
        
        # 添加必要的走廊
        self._add_hallways(layout)
        
        return layout
    
    def _place_rooms_rectangular_split(self, layout: Layout, 
                                     rooms_to_place: List[Tuple[RoomType, float, float]]):
        """使用矩形分割算法放置房间"""
        available_spaces = [layout.bounds]
        
        for room_type, width, height in rooms_to_place:
            placed = False
            
            for i, space in enumerate(available_spaces):
                if self._can_place_room_in_space(space, width, height):
                    # 选择放置位置
                    x, y = self._choose_position_in_space(space, width, height)
                    room_bounds = Rectangle(x, y, width, height)
                    
                    room = Room(room_type, room_bounds)
                    layout.add_room(room)
                    
                    # 分割剩余空间
                    remaining_spaces = self._split_space(space, room_bounds)
                    available_spaces.pop(i)
                    available_spaces.extend(remaining_spaces)
                    
                    placed = True
                    break
            
            if not placed:
                # 如果无法放置，尝试紧凑放置
                self._compact_place_room(layout, room_type, width, height)
    
    def _can_place_room_in_space(self, space: Rectangle, width: float, height: float) -> bool:
        """检查房间是否可以放入空间"""
        return (space.width >= width + 2 * self.config.wall_thickness and 
                space.height >= height + 2 * self.config.wall_thickness)
    
    def _choose_position_in_space(self, space: Rectangle, width: float, height: float) -> Tuple[float, float]:
        """在空间中选择放置位置"""
        margin = self.config.wall_thickness
        
        # 随机选择位置，但确保不超出边界
        x = space.x + margin + random.random() * (space.width - width - 2 * margin)
        y = space.y + margin + random.random() * (space.height - height - 2 * margin)
        
        return x, y
    
    def _split_space(self, original_space: Rectangle, placed_room: Rectangle) -> List[Rectangle]:
        """分割剩余空间"""
        spaces = []
        margin = self.config.wall_thickness
        
        # 上方空间
        if placed_room.top - original_space.top > margin * 2:
            spaces.append(Rectangle(
                original_space.x, original_space.y,
                original_space.width, placed_room.top - original_space.top - margin
            ))
        
        # 下方空间
        if original_space.bottom - placed_room.bottom > margin * 2:
            spaces.append(Rectangle(
                original_space.x, placed_room.bottom + margin,
                original_space.width, original_space.bottom - placed_room.bottom - margin
            ))
        
        # 左侧空间
        if placed_room.left - original_space.left > margin * 2:
            spaces.append(Rectangle(
                original_space.x, placed_room.top,
                placed_room.left - original_space.left - margin,
                placed_room.bottom - placed_room.top
            ))
        
        # 右侧空间
        if original_space.right - placed_room.right > margin * 2:
            spaces.append(Rectangle(
                placed_room.right + margin, placed_room.top,
                original_space.right - placed_room.right - margin,
                placed_room.bottom - placed_room.top
            ))
        
        return spaces
    
    def _compact_place_room(self, layout: Layout, room_type: RoomType, width: float, height: float):
        """紧凑放置房间（备用方法）"""
        margin = self.config.wall_thickness
        
        # 简单的网格放置
        grid_size = 1.0
        cols = int(layout.bounds.width / grid_size)
        rows = int(layout.bounds.height / grid_size)
        
        for row in range(rows):
            for col in range(cols):
                x = layout.bounds.x + col * grid_size + margin
                y = layout.bounds.y + row * grid_size + margin
                
                if (x + width <= layout.bounds.right - margin and 
                    y + height <= layout.bounds.bottom - margin):
                    
                    room_bounds = Rectangle(x, y, width, height)
                    
                    # 检查是否与现有房间冲突
                    conflict = False
                    for existing_room in layout.rooms:
                        if room_bounds.intersects(existing_room.bounds):
                            conflict = True
                            break
                    
                    if not conflict:
                        room = Room(room_type, room_bounds)
                        layout.add_room(room)
                        return
    
    def _add_hallways(self, layout: Layout):
        """添加走廊连接房间"""
        if len(layout.rooms) < 2:
            return
        
        # 简单的直线走廊连接
        margin = self.config.wall_thickness
        hallway_width = self.constraints.min_hallway_width
        
        # 连接主要房间
        main_rooms = layout.get_rooms_by_type(RoomType.LIVING_ROOM)
        if main_rooms:
            main_room = main_rooms[0]
            
            for room in layout.rooms:
                if room != main_room and random.random() < 0.3:
                    # 创建连接走廊
                    start_point = main_room.bounds.center
                    end_point = room.bounds.center
                    
                    # 简单的L型走廊
                    if abs(start_point.x - end_point.x) > abs(start_point.y - end_point.y):
                        # 水平连接
                        y = (start_point.y + end_point.y) / 2
                        x1 = min(start_point.x, end_point.x)
                        x2 = max(start_point.x, end_point.x)
                        
                        hallway = Rectangle(
                            x1 - hallway_width/2, y - hallway_width/2,
                            x2 - x1 + hallway_width, hallway_width
                        )
                    else:
                        # 垂直连接
                        x = (start_point.x + end_point.x) / 2
                        y1 = min(start_point.y, end_point.y)
                        y2 = max(start_point.y, end_point.y)
                        
                        hallway = Rectangle(
                            x - hallway_width/2, y1 - hallway_width/2,
                            hallway_width, y2 - y1 + hallway_width
                        )
                    
                    layout.add_hallway(hallway)


class MonteCarloOptimizer:
    """蒙特卡洛优化器"""
    
    def __init__(self, config: MonteCarloConfig, 
                 evaluation_function: Callable[[Layout], float],
                 constraints: Optional[LayoutConstraints] = None):
        self.config = config
        self.evaluation_function = evaluation_function
        self.constraints = constraints or LayoutConstraints()
        self.generator = RandomLayoutGenerator(config, constraints)
        
        # 统计信息
        self.generation_count = 0
        self.best_score = float('-inf')
        self.best_layout = None
        self.score_history = []
        self.convergence_count = 0
    
    def optimize(self, bounds: Rectangle, 
                room_requirements: Dict[RoomType, int],
                room_requirements_dict: Dict[RoomType, int]) -> Layout:
        """执行蒙特卡洛优化"""
        start_time = time.time()
        
        # 初始化种群
        population = self._initialize_population(bounds, room_requirements_dict)
        
        # 评估初始种群
        evaluated_population = []
        for layout in population:
            score = self.evaluation_function(layout)
            layout.fitness_score = score
            evaluated_population.append((layout, score))
        
        # 排序
        evaluated_population.sort(key=lambda x: x[1], reverse=True)
        
        # 记录最佳结果
        if evaluated_population:
            self.best_layout = evaluated_population[0][0].copy()
            self.best_score = evaluated_population[0][1]
        
        # 主优化循环
        temperature = self.config.temperature_start
        
        for iteration in range(self.config.max_iterations):
            # 选择父代
            parents = self._select_parents(evaluated_population)
            
            # 生成子代
            offspring = self._generate_offspring(parents, bounds, room_requirements_dict)
            
            # 评估子代
            evaluated_offspring = []
            for layout in offspring:
                score = self.evaluation_function(layout)
                layout.fitness_score = score
                evaluated_offspring.append((layout, score))
            
            # 合并种群
            evaluated_population.extend(evaluated_offspring)
            
            # 环境选择
            evaluated_population = self._environmental_selection(evaluated_population)
            
            # 更新最佳结果
            current_best = evaluated_population[0]
            if current_best[1] > self.best_score:
                self.best_layout = current_best[0].copy()
                self.best_score = current_best[1]
                self.convergence_count = 0
            else:
                self.convergence_count += 1
            
            # 记录历史
            self.score_history.append(self.best_score)
            
            # 模拟退火调整
            temperature *= self.config.cooling_rate
            
            # 检查收敛
            if self._check_convergence():
                break
            
            self.generation_count += 1
        
        end_time = time.time()
        print(f"优化完成，耗时: {end_time - start_time:.2f}秒")
        print(f"迭代次数: {self.generation_count}")
        print(f"最佳得分: {self.best_score:.4f}")
        
        return self.best_layout
    
    def _initialize_population(self, bounds: Rectangle, 
                             room_requirements: Dict[RoomType, int]) -> List[Layout]:
        """初始化种群"""
        population = []
        
        for _ in range(self.config.population_size):
            layout = self.generator.generate_random_layout(bounds, room_requirements)
            population.append(layout)
        
        return population
    
    def _select_parents(self, evaluated_population: List[Tuple[Layout, float]]) -> List[Layout]:
        """选择父代（锦标赛选择）"""
        tournament_size = 3
        selected = []
        
        num_parents = int(self.config.population_size * (1 - self.config.elite_ratio))
        
        for _ in range(num_parents):
            # 锦标赛选择
            tournament = random.sample(evaluated_population, tournament_size)
            winner = max(tournament, key=lambda x: x[1])
            selected.append(winner[0].copy())
        
        # 添加精英
        elite_count = int(self.config.population_size * self.config.elite_ratio)
        for i in range(elite_count):
            selected.append(evaluated_population[i][0].copy())
        
        return selected
    
    def _generate_offspring(self, parents: List[Layout], bounds: Rectangle,
                          room_requirements: Dict[RoomType, int]) -> List[Layout]:
        """生成子代"""
        offspring = []
        
        while len(offspring) < self.config.population_size:
            if len(parents) >= 2 and random.random() < self.config.crossover_rate:
                # 交叉
                parent1, parent2 = random.sample(parents, 2)
                child = self._crossover(parent1, parent2, bounds, room_requirements)
            else:
                # 变异
                parent = random.choice(parents)
                child = self._mutate(parent, bounds, room_requirements)
            
            if child:
                offspring.append(child)
        
        return offspring[:self.config.population_size]
    
    def _crossover(self, parent1: Layout, parent2: Layout, bounds: Rectangle,
                   room_requirements: Dict[RoomType, int]) -> Optional[Layout]:
        """交叉操作"""
        try:
            child = Layout(bounds)
            
            # 随机选择来自父代的房间
            for room_type, count in room_requirements.items():
                parent1_rooms = parent1.get_rooms_by_type(room_type)
                parent2_rooms = parent2.get_rooms_by_type(room_type)
                
                rooms_to_use = []
                
                for i in range(count):
                    if random.random() < 0.5 and parent1_rooms:
                        rooms_to_use.append(parent1_rooms[i % len(parent1_rooms)])
                    elif parent2_rooms:
                        rooms_to_use.append(parent2_rooms[i % len(parent2_rooms)])
                
                for room in rooms_to_use[:count]:
                    child.add_room(Room(room.room_type, room.bounds))
            
            # 变异操作
            if random.random() < self.config.mutation_rate:
                child = self._mutate(child, bounds, room_requirements)
            
            return child
        
        except Exception:
            return None
    
    def _mutate(self, layout: Layout, bounds: Rectangle,
               room_requirements: Dict[RoomType, int]) -> Layout:
        """变异操作"""
        mutated = layout.copy()
        
        mutation_type = random.choice(['position', 'size', 'room_swap', 'room_add_remove'])
        
        if mutation_type == 'position':
            # 位置变异
            if mutated.rooms:
                room = random.choice(mutated.rooms)
                dx = random.uniform(-2, 2)
                dy = random.uniform(-2, 2)
                
                new_bounds = Rectangle(
                    max(bounds.x, room.bounds.x + dx),
                    max(bounds.y, room.bounds.y + dy),
                    room.bounds.width,
                    room.bounds.height
                )
                
                # 确保不超出边界
                if new_bounds.right <= bounds.right and new_bounds.bottom <= bounds.bottom:
                    room.bounds = new_bounds
        
        elif mutation_type == 'size':
            # 尺寸变异
            if mutated.rooms:
                room = random.choice(mutated.rooms)
                dw = random.uniform(-1, 1)
                dh = random.uniform(-1, 1)
                
                new_width = max(3, room.bounds.width + dw)
                new_height = max(3, room.bounds.height + dh)
                
                # 确保不超出边界
                if (room.bounds.x + new_width <= bounds.right and 
                    room.bounds.y + new_height <= bounds.bottom):
                    room.bounds.width = new_width
                    room.bounds.height = new_height
        
        elif mutation_type == 'room_swap':
            # 房间交换
            if len(mutated.rooms) >= 2:
                room1, room2 = random.sample(mutated.rooms, 2)
                room1.bounds, room2.bounds = room2.bounds, room1.bounds
        
        elif mutation_type == 'room_add_remove':
            # 添加或移除房间（保持总数不变）
            if len(mutated.rooms) >= 2:
                # 移除一个房间
                room_to_remove = random.choice(mutated.rooms)
                mutated.rooms.remove(room_to_remove)
                
                # 添加新房间
                room_type = random.choice(list(room_requirements.keys()))
                template = self.generator.room_templates.get(room_type)
                if template:
                    width, height = template.generate_random_size()
                    x = random.uniform(bounds.x, bounds.right - width)
                    y = random.uniform(bounds.y, bounds.bottom - height)
                    
                    new_room = Room(room_type, Rectangle(x, y, width, height))
                    mutated.add_room(new_room)
        
        return mutated
    
    def _environmental_selection(self, evaluated_population: List[Tuple[Layout, float]]) -> List[Tuple[Layout, float]]:
        """环境选择"""
        # 按得分排序
        evaluated_population.sort(key=lambda x: x[1], reverse=True)
        
        # 保留前N个
        return evaluated_population[:self.config.population_size]
    
    def _check_convergence(self) -> bool:
        """检查收敛条件"""
        if self.convergence_count >= self.config.max_no_improvement:
            return True
        
        if len(self.score_history) >= 100:
            recent_scores = self.score_history[-100:]
            variance = np.var(recent_scores)
            if variance < self.config.convergence_threshold:
                return True
        
        return False


class ParallelMonteCarloOptimizer:
    """并行蒙特卡洛优化器"""
    
    def __init__(self, config: MonteCarloConfig,
                 evaluation_function: Callable[[Layout], float],
                 num_workers: int = 4,
                 constraints: Optional[LayoutConstraints] = None):
        self.config = config
        self.evaluation_function = evaluation_function
        self.num_workers = num_workers
        self.optimizer = MonteCarloOptimizer(config, evaluation_function, constraints or LayoutConstraints())
    
    def optimize(self, bounds: Rectangle,
                room_requirements: Dict[RoomType, int],
                room_requirements_dict: Dict[RoomType, int] = None) -> Layout:
        """并行优化（兼容标准接口）"""
        if room_requirements_dict is None:
            room_requirements_dict = room_requirements
        
        return self.optimize_parallel(bounds, room_requirements_dict)
    
    def optimize_parallel(self, bounds: Rectangle,
                         room_requirements: Dict[RoomType, int]) -> Layout:
        """并行优化"""
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # 将优化任务分配给多个工作线程
            futures = []
            
            for i in range(self.num_workers):
                # 创建独立的优化器实例
                local_config = MonteCarloConfig(
                    max_iterations=self.config.max_iterations // self.num_workers,
                    population_size=self.config.population_size // self.num_workers,
                    **{k: v for k, v in self.config.__dict__.items() 
                       if k not in ['max_iterations', 'population_size']}
                )
                
                local_optimizer = MonteCarloOptimizer(
                    local_config, self.evaluation_function, self.optimizer.constraints
                )
                
                future = executor.submit(
                    local_optimizer.optimize, bounds, room_requirements, room_requirements
                )
                futures.append(future)
            
            # 收集结果
            results = [future.result() for future in futures]
            
            # 选择最佳结果
            best_result = max(results, key=lambda x: self.evaluation_function(x))
            
            return best_result


if __name__ == "__main__":
    # 测试代码
    config = MonteCarloConfig(
        max_iterations=100,
        population_size=20,
        mutation_rate=0.3,
        crossover_rate=0.7
    )
    
    # 简单的评估函数
    def simple_evaluation(layout: Layout) -> float:
        score = layout.utilization_rate * 100
        
        # 检查必要房间
        required_types = [RoomType.LIVING_ROOM, RoomType.BEDROOM, RoomType.KITCHEN, RoomType.BATHROOM]
        for room_type in required_types:
            if layout.get_rooms_by_type(room_type):
                score += 20
        
        # 检查布局有效性
        is_valid, errors = layout.validate_layout()
        if not is_valid:
            score -= len(errors) * 10
        
        return max(0, score)
    
    optimizer = MonteCarloOptimizer(config, simple_evaluation)
    
    bounds = Rectangle(0, 0, 20, 15)
    room_requirements = {
        RoomType.LIVING_ROOM: 1,
        RoomType.BEDROOM: 2,
        RoomType.KITCHEN: 1,
        RoomType.BATHROOM: 1
    }
    
    best_layout = optimizer.optimize(bounds, room_requirements, room_requirements)
    print(f"最佳布局得分: {optimizer.best_score:.2f}")
    print(f"房间数量: {len(best_layout.rooms)}")
    print(f"空间利用率: {best_layout.utilization_rate:.2%}")