"""
多维度评估系统
实现住宅布局的多维度评估，包括空间利用率、采光、通风、动线效率等
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

from core_data_structures import (
    Layout, Room, RoomType, Rectangle, Point, Orientation, 
    OptimizationTarget, Furniture
)


@dataclass
class EvaluationConfig:
    """评估系统配置"""
    # 权重设置
    space_efficiency_weight: float = 0.25      # 空间效率权重
    lighting_weight: float = 0.20             # 采光权重
    ventilation_weight: float = 0.15           # 通风权重
    circulation_weight: float = 0.20          # 动线效率权重
    comfort_weight: float = 0.20               # 舒适度权重
    
    # 空间效率参数
    min_room_efficiency: float = 0.4          # 最小房间效率
    ideal_utilization_rate: float = 0.75      # 理想空间利用率
    corridor_penalty_factor: float = 0.8      # 走廊惩罚因子
    
    # 采光参数
    max_depth_from_window: float = 6.0        # 最大窗距
    window_area_ratio: float = 0.15           # 窗墙比
    light_decay_factor: float = 0.1           # 光线衰减因子
    
    # 通风参数
    min_ventilation_path: float = 2.0        # 最小通风路径
    cross_ventilation_bonus: float = 1.2      # 对流通风奖励
    dead_space_penalty: float = 0.5           # 死角空间惩罚
    
    # 动线参数
    max_circulation_distance: float = 15.0    # 最大动线距离
    intersection_penalty: float = 0.3         # 交叉动线惩罚
    connection_bonus: float = 0.2             # 连接性奖励
    
    # 舒适度参数
    noise_reduction_factor: float = 0.8       # 噪音衰减因子
    privacy_weight: float = 0.5               # 隐私权重
    social_area_bonus: float = 1.1           # 社交区域奖励


class BaseEvaluator(ABC):
    """评估器基类"""
    
    def __init__(self, config: EvaluationConfig, weight: float = 1.0):
        self.config = config
        self.weight = weight
    
    @abstractmethod
    def evaluate(self, layout: Layout) -> float:
        """评估布局得分"""
        pass
    
    def normalize_score(self, score: float, min_score: float, max_score: float) -> float:
        """归一化得分到[0,1]区间"""
        return max(0, min(1, (score - min_score) / (max_score - min_score)))


class SpaceEfficiencyEvaluator(BaseEvaluator):
    """空间效率评估器"""
    
    def evaluate(self, layout: Layout) -> float:
        """评估空间效率"""
        score = 0.0
        
        # 整体空间利用率
        utilization_rate = layout.utilization_rate
        utilization_score = self._evaluate_utilization_rate(utilization_rate)
        score += utilization_score * 0.3
        
        # 房间效率评估
        room_efficiency_score = self._evaluate_room_efficiency(layout)
        score += room_efficiency_score * 0.4
        
        # 走廊效率评估
        hallway_efficiency_score = self._evaluate_hallway_efficiency(layout)
        score += hallway_efficiency_score * 0.3
        
        return score
    
    def _evaluate_utilization_rate(self, rate: float) -> float:
        """评估整体利用率"""
        ideal = self.config.ideal_utilization_rate
        deviation = abs(rate - ideal)
        return max(0, 1 - deviation / ideal)
    
    def _evaluate_room_efficiency(self, layout: Layout) -> float:
        """评估房间效率"""
        if not layout.rooms:
            return 0.0
        
        total_efficiency = 0.0
        for room in layout.rooms:
            # 房间形状效率
            aspect_ratio = room.bounds.width / room.bounds.height
            shape_efficiency = self._evaluate_room_shape(aspect_ratio)
            
            # 家具布置效率
            furniture_efficiency = room.utilization_rate
            
            # 面积适切性
            area_efficiency = self._evaluate_area_appropriateness(room)
            
            room_score = (shape_efficiency + furniture_efficiency + area_efficiency) / 3
            total_efficiency += room_score
        
        return total_efficiency / len(layout.rooms)
    
    def _evaluate_room_shape(self, aspect_ratio: float) -> float:
        """评估房间形状"""
        # 理想长宽比在0.8-1.25之间
        if 0.8 <= aspect_ratio <= 1.25:
            return 1.0
        elif 0.6 <= aspect_ratio <= 1.67:
            return 0.8
        else:
            return 0.5
    
    def _evaluate_area_appropriateness(self, room: Room) -> float:
        """评估面积适切性"""
        area_standards = {
            RoomType.LIVING_ROOM: (15, 40),
            RoomType.BEDROOM: (8, 25),
            RoomType.KITCHEN: (6, 20),
            RoomType.BATHROOM: (3, 12),
            RoomType.DINING_ROOM: (10, 25),
            RoomType.STUDY: (6, 18),
        }
        
        standards = area_standards.get(room.room_type, (5, 30))
        min_area, max_area = standards
        
        if min_area <= room.area <= max_area:
            return 1.0
        elif room.area < min_area:
            return room.area / min_area
        else:
            return max(0, 1 - (room.area - max_area) / max_area)
    
    def _evaluate_hallway_efficiency(self, layout: Layout) -> float:
        """评估走廊效率"""
        if not layout.hallways:
            return 1.0  # 没有走廊则无需评估
        
        total_hallway_area = layout.hallway_area
        total_area = layout.total_area
        
        hallway_ratio = total_hallway_area / total_area
        
        # 走廊面积不宜过大
        if hallway_ratio < 0.05:
            return 1.0
        elif hallway_ratio < 0.1:
            return 0.8
        elif hallway_ratio < 0.15:
            return 0.6
        else:
            return 0.3


class LightingEvaluator(BaseEvaluator):
    """采光评估器"""
    
    def evaluate(self, layout: Layout) -> float:
        """评估采光效果"""
        score = 0.0
        
        # 窗户覆盖率
        window_coverage_score = self._evaluate_window_coverage(layout)
        score += window_coverage_score * 0.3
        
        # 采光均匀度
        uniformity_score = self._evaluate_lighting_uniformity(layout)
        score += uniformity_score * 0.4
        
        # 采光源配置
        source_config_score = self._evaluate_lighting_sources(layout)
        score += source_config_score * 0.3
        
        return score
    
    def _evaluate_window_coverage(self, layout: Layout) -> float:
        """评估窗户覆盖率"""
        if not layout.rooms:
            return 0.0
        
        total_window_area = 0.0
        total_wall_area = 0.0
        
        for room in layout.rooms:
            # 计算墙体面积
            perimeter = 2 * (room.bounds.width + room.bounds.height)
            wall_area = perimeter * 2.8  # 假设层高2.8米
            total_wall_area += wall_area
            
            # 计算窗户面积
            window_area = sum(w.width * w.height for w in room.windows)
            total_window_area += window_area
        
        if total_wall_area == 0:
            return 0.0
        
        window_ratio = total_window_area / total_wall_area
        ideal_ratio = self.config.window_area_ratio
        
        return max(0, 1 - abs(window_ratio - ideal_ratio) / ideal_ratio)
    
    def _evaluate_lighting_uniformity(self, layout: Layout) -> float:
        """评估采光均匀度"""
        room_scores = []
        
        for room in layout.rooms:
            if not room.windows:
                room_scores.append(0.3)  # 无窗户的房间得分较低
                continue
            
            # 计算房间内各点到最近窗户的距离
            center = room.bounds.center
            min_distance = float('inf')
            
            for window in room.windows:
                window_center = Point(
                    window.x + window.width / 2,
                    window.y + window.height / 2
                )
                distance = center.distance_to(window_center)
                min_distance = min(min_distance, distance)
            
            # 距离越近采光越好
            max_distance = self.config.max_depth_from_window
            distance_score = max(0, 1 - min_distance / max_distance)
            
            # 房间大小影响采光效果
            area_factor = min(1, 30 / room.area)  # 小房间采光更容易
            
            room_score = distance_score * area_factor
            room_scores.append(room_score)
        
        return sum(room_scores) / len(room_scores) if room_scores else 0.0
    
    def _evaluate_lighting_sources(self, layout: Layout) -> float:
        """评估采光源配置"""
        score = 0.0
        
        # 主要房间应该有良好采光
        important_rooms = [RoomType.LIVING_ROOM, RoomType.BEDROOM, RoomType.KITCHEN]
        
        for room_type in important_rooms:
            rooms = layout.get_rooms_by_type(room_type)
            for room in rooms:
                if room.windows:
                    # 检查窗户朝向分布
                    orientations = set()
                    for window in room.windows:
                        # 简化判断：根据窗户位置推断朝向
                        if window.x <= room.bounds.x + 0.1:  # 左墙
                            orientations.add(Orientation.WEST)
                        elif window.x + window.width >= room.bounds.right - 0.1:  # 右墙
                            orientations.add(Orientation.EAST)
                        elif window.y <= room.bounds.y + 0.1:  # 上墙
                            orientations.add(Orientation.NORTH)
                        elif window.y + window.height >= room.bounds.bottom - 0.1:  # 下墙
                            orientations.add(Orientation.SOUTH)
                    
                    # 多朝向采光更佳
                    orientation_score = min(1, len(orientations) / 2)
                    score += orientation_score
        
        return score / (len(important_rooms) * 2)  # 归一化


class VentilationEvaluator(BaseEvaluator):
    """通风评估器"""
    
    def evaluate(self, layout: Layout) -> float:
        """评估通风效果"""
        score = 0.0
        
        # 通风路径
        path_score = self._evaluate_ventilation_paths(layout)
        score += path_score * 0.4
        
        # 对流通风
        cross_ventilation_score = self._evaluate_cross_ventilation(layout)
        score += cross_ventilation_score * 0.3
        
        # 空气流通效率
        circulation_score = self._evaluate_air_circulation(layout)
        score += circulation_score * 0.3
        
        return score
    
    def _evaluate_ventilation_paths(self, layout: Layout) -> float:
        """评估通风路径"""
        if not layout.rooms:
            return 0.0
        
        room_scores = []
        
        for room in layout.rooms:
            # 检查是否有足够的通风路径（门、窗）
            ventilation_openings = len(room.doors) + len(room.windows)
            
            if ventilation_openings >= 2:
                room_score = 1.0
            elif ventilation_openings == 1:
                room_score = 0.6
            else:
                room_score = 0.2
            
            room_scores.append(room_score)
        
        return sum(room_scores) / len(room_scores)
    
    def _evaluate_cross_ventilation(self, layout: Layout) -> float:
        """评估对流通风"""
        cross_ventilation_count = 0
        total_rooms = len(layout.rooms)
        
        for room in layout.rooms:
            if len(room.windows) >= 2:
                # 检查窗户是否在不同墙面
                window_positions = []
                for window in room.windows:
                    if window.x <= room.bounds.x + 0.1:
                        window_positions.append('left')
                    elif window.x + window.width >= room.bounds.right - 0.1:
                        window_positions.append('right')
                    elif window.y <= room.bounds.y + 0.1:
                        window_positions.append('top')
                    elif window.y + window.height >= room.bounds.bottom - 0.1:
                        window_positions.append('bottom')
                
                # 有相对的窗户形成对流通风
                if (('left' in window_positions and 'right' in window_positions) or
                    ('top' in window_positions and 'bottom' in window_positions)):
                    cross_ventilation_count += 1
        
        if total_rooms == 0:
            return 0.0
        
        return (cross_ventilation_count / total_rooms) * self.config.cross_ventilation_bonus
    
    def _evaluate_air_circulation(self, layout: Layout) -> float:
        """评估空气流通效率"""
        # 基于房间连通性评估空气流通
        connectivity_score = 0.0
        
        for room in layout.rooms:
            # 计算房间与其他空间的连接度
            connections = len(room.doors)
            room_score = min(1, connections / 2)  # 最多2个门为满分
            
            connectivity_score += room_score
        
        return connectivity_score / len(layout.rooms) if layout.rooms else 0.0


class CirculationEvaluator(BaseEvaluator):
    """动线效率评估器"""
    
    def evaluate(self, layout: Layout) -> float:
        """评估动线效率"""
        score = 0.0
        
        # 连接效率
        connection_score = self._evaluate_connection_efficiency(layout)
        score += connection_score * 0.3
        
        # 路径长度
        path_length_score = self._evaluate_path_lengths(layout)
        score += path_length_score * 0.4
        
        # 动线交叉
        intersection_score = self._evaluate_circulation_intersections(layout)
        score += intersection_score * 0.3
        
        return score
    
    def _evaluate_connection_efficiency(self, layout: Layout) -> float:
        """评估连接效率"""
        # 评估重要房间之间的连接性
        important_rooms = [RoomType.LIVING_ROOM, RoomType.KITCHEN, RoomType.BEDROOM]
        room_dict = {room.room_type: room for room in layout.rooms}
        
        connection_score = 0.0
        total_connections = 0
        
        room_type_list = list(important_rooms)
        for i, room_type1 in enumerate(room_type_list):
            for room_type2 in room_type_list[i+1:]:  # 避免重复计算
                if room_type1 in room_dict and room_type2 in room_dict:
                    room1 = room_dict[room_type1]
                    room2 = room_dict[room_type2]
                    
                    # 计算房间中心距离
                    distance = room1.bounds.center.distance_to(room2.bounds.center)
                    
                    # 距离越近越好
                    max_distance = self.config.max_circulation_distance
                    distance_score = max(0, 1 - distance / max_distance)
                    
                    connection_score += distance_score
                    total_connections += 1
        
        return connection_score / total_connections if total_connections > 0 else 0.0
    
    def _evaluate_path_lengths(self, layout: Layout) -> float:
        """评估路径长度"""
        # 简化评估：基于走廊总长度
        if not layout.hallways:
            return 1.0
        
        total_hallway_length = sum(
            max(h.width, h.height) for h in layout.hallways
        )
        
        # 走廊总长度应该适中
        ideal_length = layout.total_area * 0.1  # 简化假设
        deviation = abs(total_hallway_length - ideal_length)
        
        return max(0, 1 - deviation / ideal_length)
    
    def _evaluate_circulation_intersections(self, layout: Layout) -> float:
        """评估动线交叉情况"""
        # 简化评估：基于走廊交叉情况
        intersections = 0
        
        for i, hallway1 in enumerate(layout.hallways):
            for hallway2 in layout.hallways[i+1:]:
                if hallway1.intersects(hallway2):
                    intersections += 1
        
        # 交叉越少越好
        max_intersections = len(layout.hallways) // 2
        intersection_score = max(0, 1 - intersections / max(1, max_intersections))
        
        return intersection_score


class ComfortEvaluator(BaseEvaluator):
    """舒适度评估器"""
    
    def evaluate(self, layout: Layout) -> float:
        """评估舒适度"""
        score = 0.0
        
        # 噪音隔离
        noise_score = self._evaluate_noise_isolation(layout)
        score += noise_score * 0.3
        
        # 隐私保护
        privacy_score = self._evaluate_privacy(layout)
        score += privacy_score * 0.3
        
        # 社交空间
        social_score = self._evaluate_social_spaces(layout)
        score += social_score * 0.2
        
        # 功能分区
        functional_score = self._evaluate_functional_zoning(layout)
        score += functional_score * 0.2
        
        return score
    
    def _evaluate_noise_isolation(self, layout: Layout) -> float:
        """评估噪音隔离"""
        # 评估噪音源（厨房、卫生间）与安静区域（卧室、书房）的分离
        noise_sources = [RoomType.KITCHEN, RoomType.BATHROOM]
        quiet_zones = [RoomType.BEDROOM, RoomType.STUDY]
        
        room_dict = {room.room_type: room for room in layout.rooms}
        isolation_scores = []
        
        for source_type in noise_sources:
            if source_type not in room_dict:
                continue
                
            source_room = room_dict[source_type]
            source_center = source_room.bounds.center
            
            for quiet_type in quiet_zones:
                if quiet_type not in room_dict:
                    continue
                    
                quiet_room = room_dict[quiet_type]
                quiet_center = quiet_room.bounds.center
                
                # 距离越远，噪音隔离越好
                distance = source_center.distance_to(quiet_center)
                isolation_score = min(1, distance / 5.0)  # 5米为满分
                
                isolation_scores.append(isolation_score)
        
        return sum(isolation_scores) / len(isolation_scores) if isolation_scores else 1.0
    
    def _evaluate_privacy(self, layout: Layout) -> float:
        """评估隐私保护"""
        # 评估私密房间（卧室、卫生间）的私密性
        private_rooms = [RoomType.BEDROOM, RoomType.BATHROOM]
        room_dict = {room.room_type: room for room in layout.rooms}
        
        privacy_scores = []
        
        for room_type in private_rooms:
            if room_type not in room_dict:
                continue
                
            room = room_dict[room_type]
            
            # 检查是否直接面向公共区域
            public_access = 0
            for door in room.doors:
                # 简化判断：检查门是否在主要墙面上
                if (door.x <= room.bounds.x + 0.5 or 
                    door.x + door.width >= room.bounds.right - 0.5 or
                    door.y <= room.bounds.y + 0.5 or 
                    door.y + door.height >= room.bounds.bottom - 0.5):
                    public_access += 1
            
            # 公共入口越少，私密性越好
            privacy_score = max(0, 1 - public_access / 2)
            privacy_scores.append(privacy_score)
        
        return sum(privacy_scores) / len(privacy_scores) if privacy_scores else 1.0
    
    def _evaluate_social_spaces(self, layout: Layout) -> float:
        """评估社交空间"""
        social_rooms = [RoomType.LIVING_ROOM, RoomType.DINING_ROOM]
        room_dict = {room.room_type: room for room in layout.rooms}
        
        social_score = 0.0
        
        for room_type in social_rooms:
            if room_type in room_dict:
                room = room_dict[room_type]
                
                # 社交空间应该相对宽敞
                ideal_area = 20 if room_type == RoomType.LIVING_ROOM else 15
                area_score = min(1, room.area / ideal_area)
                
                # 形状应该适合多人活动
                aspect_ratio = room.bounds.width / room.bounds.height
                shape_score = 1.0 if 0.8 <= aspect_ratio <= 1.25 else 0.7
                
                social_score += (area_score + shape_score) / 2
        
        return social_score / len(social_rooms) * self.config.social_area_bonus
    
    def _evaluate_functional_zoning(self, layout: Layout) -> float:
        """评估功能分区"""
        # 评估相关功能房间的聚集程度
        living_zone = [RoomType.LIVING_ROOM, RoomType.DINING_ROOM]
        private_zone = [RoomType.BEDROOM, RoomType.STUDY]
        service_zone = [RoomType.KITCHEN, RoomType.BATHROOM]
        
        zones = [living_zone, private_zone, service_zone]
        zone_scores = []
        
        for zone in zones:
            zone_rooms = []
            for room in layout.rooms:
                if room.room_type in zone:
                    zone_rooms.append(room)
            
            if len(zone_rooms) < 2:
                zone_scores.append(1.0)  # 单个房间无需评估聚集度
                continue
            
            # 计算区域内房间的聚集度
            centers = [room.bounds.center for room in zone_rooms]
            avg_center = Point(
                sum(c.x for c in centers) / len(centers),
                sum(c.y for c in centers) / len(centers)
            )
            
            avg_distance = sum(c.distance_to(avg_center) for c in centers) / len(centers)
            cluster_score = max(0, 1 - avg_distance / 10.0)  # 10米为基准
            
            zone_scores.append(cluster_score)
        
        return sum(zone_scores) / len(zone_scores)


class MultiDimensionalEvaluator:
    """多维度综合评估器"""
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()
        
        # 初始化各维度评估器
        self.evaluators = [
            SpaceEfficiencyEvaluator(self.config, self.config.space_efficiency_weight),
            LightingEvaluator(self.config, self.config.lighting_weight),
            VentilationEvaluator(self.config, self.config.ventilation_weight),
            CirculationEvaluator(self.config, self.config.circulation_weight),
            ComfortEvaluator(self.config, self.config.comfort_weight),
        ]
    
    def evaluate(self, layout: Layout) -> float:
        """综合评估布局，返回总分"""
        total_score = 0.0
        
        for evaluator in self.evaluators:
            score = evaluator.evaluate(layout)
            weighted_score = score * evaluator.weight
            total_score += weighted_score
        
        return total_score
    
    def evaluate_detailed(self, layout: Layout) -> Dict[str, float]:
        """综合评估布局，返回详细结果"""
        results = {}
        total_score = 0.0
        
        for evaluator in self.evaluators:
            score = evaluator.evaluate(layout)
            weighted_score = score * evaluator.weight
            
            # 获取评估器类型名称
            evaluator_name = evaluator.__class__.__name__.replace('Evaluator', '').lower()
            results[evaluator_name] = {
                'score': score,
                'weight': evaluator.weight,
                'weighted_score': weighted_score
            }
            
            total_score += weighted_score
        
        results['total'] = {
            'score': total_score,
            'weight': sum(evaluator.weight for evaluator in self.evaluators),
            'weighted_score': total_score
        }
        
        return results
    
    def get_detailed_report(self, layout: Layout) -> str:
        """获取详细评估报告"""
        results = self.evaluate_detailed(layout)
        
        report = "=== 住宅布局评估报告 ===\n\n"
        report += f"总分: {results['total']['weighted_score']:.2f}\n\n"
        
        dimension_names = {
            'spaceefficiency': '空间效率',
            'lighting': '采光效果',
            'ventilation': '通风效果',
            'circulation': '动线效率',
            'comfort': '舒适度'
        }
        
        for key, result in results.items():
            if key == 'total':
                continue
                
            name = dimension_names.get(key, key)
            report += f"{name}:\n"
            report += f"  得分: {result['score']:.2f}\n"
            report += f"  权重: {result['weight']:.2f}\n"
            report += f"  加权得分: {result['weighted_score']:.2f}\n\n"
        
        return report


if __name__ == "__main__":
    # 测试代码
    config = EvaluationConfig()
    evaluator = MultiDimensionalEvaluator(config)
    
    # 创建测试布局
    from core_data_structures import Rectangle, Room, RoomType, Layout
    
    bounds = Rectangle(0, 0, 20, 15)
    layout = Layout(bounds)
    
    # 添加房间
    living_room = Room(RoomType.LIVING_ROOM, Rectangle(2, 2, 8, 6))
    kitchen = Room(RoomType.KITCHEN, Rectangle(10, 2, 5, 4))
    bedroom = Room(RoomType.BEDROOM, Rectangle(2, 8, 6, 5))
    bathroom = Room(RoomType.BATHROOM, Rectangle(8, 8, 3, 3))
    
    layout.add_room(living_room)
    layout.add_room(kitchen)
    layout.add_room(bedroom)
    layout.add_room(bathroom)
    
    # 添加窗户
    living_room.add_window(Rectangle(2, 2, 2, 0.2))
    bedroom.add_window(Rectangle(2, 8, 2, 0.2))
    
    # 评估
    results = evaluator.evaluate(layout)
    report = evaluator.get_detailed_report(layout)
    
    print(report)