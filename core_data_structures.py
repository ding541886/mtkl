"""
核心数据结构模块
定义住宅自动化生成系统的基础类和接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from enum import Enum
import random


class RoomType(Enum):
    """房间类型枚举"""
    LIVING_ROOM = "living_room"
    BEDROOM = "bedroom"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    DINING_ROOM = "dining_room"
    STUDY = "study"
    BALCONY = "balcony"
    STORAGE = "storage"
    HALLWAY = "hallway"


class Orientation(Enum):
    """朝向枚举"""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


@dataclass
class Point:
    """二维点坐标"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """计算到另一点的距离"""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def __add__(self, other: 'Point') -> 'Point':
        return Point(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Point') -> 'Point':
        return Point(self.x - other.x, self.y - other.y)


@dataclass
class Rectangle:
    """矩形区域"""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def left(self) -> float:
        return self.x
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    @property
    def top(self) -> float:
        return self.y
    
    @property
    def bottom(self) -> float:
        return self.y + self.height
    
    @property
    def center(self) -> Point:
        return Point(self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    def contains_point(self, point: Point) -> bool:
        """检查点是否在矩形内"""
        return (self.left <= point.x <= self.right and 
                self.top <= point.y <= self.bottom)
    
    def intersects(self, other: 'Rectangle') -> bool:
        """检查是否与另一个矩形相交"""
        return not (self.right <= other.left or 
                   self.left >= other.right or 
                   self.bottom <= other.top or 
                   self.top >= other.bottom)
    
    def get_corners(self) -> List[Point]:
        """获取四个角点"""
        return [
            Point(self.left, self.top),
            Point(self.right, self.top),
            Point(self.right, self.bottom),
            Point(self.left, self.bottom)
        ]


class Furniture:
    """家具类"""
    def __init__(self, name: str, width: float, height: float, 
                 can_rotate: bool = True, category: str = "general"):
        self.name = name
        self.width = width
        self.height = height
        self.can_rotate = can_rotate
        self.category = category
        self.position = Point(0, 0)
        self.is_rotated = False
        self.is_placed = False
    
    @property
    def current_width(self) -> float:
        """获取当前宽度（考虑旋转）"""
        return self.height if self.is_rotated else self.width
    
    @property
    def current_height(self) -> float:
        """获取当前高度（考虑旋转）"""
        return self.width if self.is_rotated else self.height
    
    def rotate(self):
        """旋转家具"""
        if self.can_rotate:
            self.is_rotated = not self.is_rotated
    
    def get_bounds(self) -> Rectangle:
        """获取家具的边界矩形"""
        return Rectangle(self.position.x, self.position.y, 
                        self.current_width, self.current_height)


class Room:
    """房间类"""
    def __init__(self, room_type: RoomType, bounds: Rectangle, 
                 min_area: float = 0, orientation: Optional[Orientation] = None):
        self.room_type = room_type
        self.bounds = bounds
        self.min_area = min_area
        self.orientation = orientation
        self.furniture: List[Furniture] = []
        self.doors: List[Rectangle] = []
        self.windows: List[Rectangle] = []
        self.id = id(self)
    
    @property
    def area(self) -> float:
        """获取房间面积"""
        return self.bounds.area
    
    @property
    def used_area(self) -> float:
        """获取已使用面积（家具占用）"""
        return sum(furniture.current_width * furniture.current_height 
                  for furniture in self.furniture if furniture.is_placed)
    
    @property
    def free_area(self) -> float:
        """获取剩余可用面积"""
        return self.area - self.used_area
    
    @property
    def utilization_rate(self) -> float:
        """获取空间利用率"""
        return self.used_area / self.area if self.area > 0 else 0
    
    def add_furniture(self, furniture: Furniture):
        """添加家具"""
        self.furniture.append(furniture)
    
    def add_door(self, door: Rectangle):
        """添加门"""
        self.doors.append(door)
    
    def add_window(self, window: Rectangle):
        """添加窗户"""
        self.windows.append(window)
    
    def can_place_furniture(self, furniture: Furniture, position: Point) -> bool:
        """检查是否可以在指定位置放置家具"""
        test_rect = Rectangle(position.x, position.y, 
                            furniture.current_width, furniture.current_height)
        
        # 检查是否在房间内
        if not (self.bounds.left <= test_rect.left and 
                test_rect.right <= self.bounds.right and 
                self.bounds.top <= test_rect.top and 
                test_rect.bottom <= self.bounds.bottom):
            return False
        
        # 检查是否与其他家具冲突
        for existing_furniture in self.furniture:
            if existing_furniture.is_placed:
                existing_bounds = existing_furniture.get_bounds()
                if test_rect.intersects(existing_bounds):
                    return False
        
        # 检查是否挡住门
        for door in self.doors:
            if test_rect.intersects(door):
                return False
        
        return True
    
    def place_furniture(self, furniture: Furniture, position: Point) -> bool:
        """在指定位置放置家具"""
        if self.can_place_furniture(furniture, position):
            furniture.position = position
            furniture.is_placed = True
            return True
        return False


class Layout:
    """布局类"""
    def __init__(self, bounds: Rectangle):
        self.bounds = bounds
        self.rooms: List[Room] = []
        self.hallways: List[Rectangle] = []
        self.fitness_score = 0.0
        self.generation_id = 0
        self.metadata: Dict = {}
    
    @property
    def total_area(self) -> float:
        """获取总面积"""
        return self.bounds.area
    
    @property
    def room_area(self) -> float:
        """获取房间总面积"""
        return sum(room.area for room in self.rooms)
    
    @property
    def hallway_area(self) -> float:
        """获取走廊面积"""
        return sum(hallway.area for hallway in self.hallways)
    
    @property
    def utilization_rate(self) -> float:
        """获取整体空间利用率"""
        usable_area = self.room_area + self.hallway_area
        return usable_area / self.total_area if self.total_area > 0 else 0
    
    def add_room(self, room: Room):
        """添加房间"""
        self.rooms.append(room)
    
    def add_hallway(self, hallway: Rectangle):
        """添加走廊"""
        self.hallways.append(hallway)
    
    def get_rooms_by_type(self, room_type: RoomType) -> List[Room]:
        """根据类型获取房间"""
        return [room for room in self.rooms if room.room_type == room_type]
    
    def validate_layout(self) -> Tuple[bool, List[str]]:
        """验证布局是否有效"""
        errors = []
        
        # 检查房间是否重叠
        for i, room1 in enumerate(self.rooms):
            for room2 in self.rooms[i+1:]:
                if room1.bounds.intersects(room2.bounds):
                    errors.append(f"房间 {room1.room_type.value} 与 {room2.room_type.value} 重叠")
        
        # 检查房间是否在边界内
        for room in self.rooms:
            if not (self.bounds.left <= room.bounds.left and 
                   room.bounds.right <= self.bounds.right and 
                   self.bounds.top <= room.bounds.top and 
                   room.bounds.bottom <= self.bounds.bottom):
                errors.append(f"房间 {room.room_type.value} 超出边界")
        
        # 检查必要房间是否存在
        required_types = [RoomType.LIVING_ROOM, RoomType.BEDROOM, 
                         RoomType.KITCHEN, RoomType.BATHROOM]
        for required_type in required_types:
            if not self.get_rooms_by_type(required_type):
                errors.append(f"缺少必要房间类型: {required_type.value}")
        
        return len(errors) == 0, errors
    
    def copy(self) -> 'Layout':
        """创建布局的深拷贝"""
        new_layout = Layout(Rectangle(self.bounds.x, self.bounds.y, 
                                     self.bounds.width, self.bounds.height))
        
        for room in self.rooms:
            new_room = Room(room.room_type, 
                           Rectangle(room.bounds.x, room.bounds.y, 
                                   room.bounds.width, room.bounds.height),
                           room.min_area, room.orientation)
            new_layout.add_room(new_room)
        
        new_layout.hallways = [Rectangle(h.x, h.y, h.width, h.height) 
                              for h in self.hallways]
        new_layout.metadata = self.metadata.copy()
        
        return new_layout


class RoomTemplate:
    """房间模板类"""
    def __init__(self, room_type: RoomType, min_area: float, max_area: float,
                 aspect_ratio_min: float = 0.6, aspect_ratio_max: float = 1.67):
        self.room_type = room_type
        self.min_area = min_area
        self.max_area = max_area
        self.aspect_ratio_min = aspect_ratio_min
        self.aspect_ratio_max = aspect_ratio_max
    
    def generate_random_size(self) -> Tuple[float, float]:
        """生成随机房间尺寸"""
        area = random.uniform(self.min_area, self.max_area)
        aspect_ratio = random.uniform(self.aspect_ratio_min, self.aspect_ratio_max)
        
        width = (area * aspect_ratio) ** 0.5
        height = area / width
        
        return width, height


class LayoutConstraints:
    """布局约束类"""
    def __init__(self):
        self.min_room_distance = 1.0  # 房间间最小距离
        self.max_total_rooms = 15      # 最大房间数
        self.min_hallway_width = 1.2   # 最小走廊宽度
        self.max_corridor_length = 10.0 # 最大走廊长度
        self.adjacency_rules: Dict[RoomType, List[RoomType]] = {}
        self.separation_rules: Dict[Tuple[RoomType, RoomType], float] = {}
        
        # 默认邻接规则
        self._setup_default_adjacency_rules()
        
        # 默认分离规则
        self._setup_default_separation_rules()
    
    def _setup_default_adjacency_rules(self):
        """设置默认邻接规则"""
        self.adjacency_rules = {
            RoomType.KITCHEN: [RoomType.DINING_ROOM, RoomType.LIVING_ROOM],
            RoomType.BEDROOM: [RoomType.BATHROOM],
            RoomType.LIVING_ROOM: [RoomType.DINING_ROOM, RoomType.HALLWAY],
            RoomType.BATHROOM: [RoomType.BEDROOM, RoomType.HALLWAY]
        }
    
    def _setup_default_separation_rules(self):
        """设置默认分离规则"""
        self.separation_rules = {
            (RoomType.BEDROOM, RoomType.KITCHEN): 2.0,
            (RoomType.BATHROOM, RoomType.KITCHEN): 1.5,
            (RoomType.BEDROOM, RoomType.LIVING_ROOM): 1.0
        }
    
    def should_be_adjacent(self, room1_type: RoomType, room2_type: RoomType) -> bool:
        """检查两个房间是否应该相邻"""
        adjacent_to = self.adjacency_rules.get(room1_type, [])
        return room2_type in adjacent_to
    
    def get_min_separation(self, room1_type: RoomType, room2_type: RoomType) -> float:
        """获取两个房间间的最小分离距离"""
        key = (room1_type, room2_type)
        reverse_key = (room2_type, room1_type)
        return max(self.separation_rules.get(key, 0), 
                  self.separation_rules.get(reverse_key, 0))


class OptimizationTarget:
    """优化目标类"""
    def __init__(self, name: str, weight: float, maximize: bool = True):
        self.name = name
        self.weight = weight
        self.maximize = maximize
    
    def evaluate(self, layout: Layout) -> float:
        """评估布局在该目标下的得分（子类实现）"""
        raise NotImplementedError


if __name__ == "__main__":
    # 测试代码
    room_template = RoomTemplate(RoomType.LIVING_ROOM, 20, 40)
    width, height = room_template.generate_random_size()
    print(f"生成的客厅尺寸: {width:.2f} x {height:.2f}")
    
    bounds = Rectangle(0, 0, 100, 100)
    layout = Layout(bounds)
    
    living_room = Room(RoomType.LIVING_ROOM, Rectangle(10, 10, width, height))
    layout.add_room(living_room)
    
    print(f"布局总面积: {layout.total_area:.2f}")
    print(f"房间总面积: {layout.room_area:.2f}")
    print(f"空间利用率: {layout.utilization_rate:.2%}")