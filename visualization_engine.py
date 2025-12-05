"""
简化的2D可视化渲染引擎
使用Matplotlib实现住宅平面图的基本绘制功能
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import Dict, List, Tuple, Optional

from core_data_structures import (
    Layout, Room, RoomType, Rectangle, Point
)


class SimpleVisualizationConfig:
    """简化的可视化配置"""
    def __init__(self):
        # 颜色配置
        self.room_colors = {
            RoomType.LIVING_ROOM: '#E8F5E9',      # 浅绿色 - 客厅
            RoomType.BEDROOM: '#E3F2FD',          # 浅蓝色 - 卧室
            RoomType.KITCHEN: '#FFF3E0',          # 浅橙色 - 厨房
            RoomType.BATHROOM: '#F3E5F5',         # 浅紫色 - 卫生间
            RoomType.DINING_ROOM: '#FFEBEE',      # 浅红色 - 餐厅
            RoomType.STUDY: '#E0F2F1',            # 浅青色 - 书房
            RoomType.BALCONY: '#F1F8E9',          # 浅黄绿色 - 阳台
            RoomType.HALLWAY: '#FAFAFA',          # 浅灰色 - 走廊
            RoomType.STORAGE: '#EFEBE9'           # 浅棕色 - 储藏室
        }
        
        # 绘制配置
        self.wall_color = '#333333'
        self.door_color = '#8B4513'
        self.window_color = '#87CEEB'
        self.text_color = '#333333'
        self.wall_width = 2
        self.door_width = 1.5
        self.window_width = 1.0
        self.margin = 0.5
        self.show_areas = True
        self.font_size = 10
        self.font_family = 'SimHei'


class SimpleLayoutRenderer:
    """简化的布局渲染器"""
    
    def __init__(self, config: Optional[SimpleVisualizationConfig] = None):
        self.config = config or SimpleVisualizationConfig()
        self.fig = None
        self.ax = None
    
    def setup_figure(self, figsize: Tuple[int, int] = (12, 8)) -> None:
        """设置图形"""
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_aspect('equal')
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = [self.config.font_family, 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
    
    def render_layout(self, layout: Layout, 
                     show_evaluation: bool = False,
                     evaluation_results: Optional[Dict] = None) -> None:
        """渲染布局"""
        if self.fig is None:
            self.setup_figure()
        
        # 清除当前图形
        self.ax.clear()
        
        # 设置坐标轴
        margin = self.config.margin
        self.ax.set_xlim(-margin, layout.bounds.width + margin)
        self.ax.set_ylim(-margin, layout.bounds.height + margin)
        self.ax.set_xlabel('宽度 (米)', fontsize=12)
        self.ax.set_ylabel('深度 (米)', fontsize=12)
        
        # 绘制房间
        self._draw_rooms(layout.rooms)
        
        # 绘制走廊
        if layout.hallways:
            self._draw_hallways(layout.hallways)
        
        # 绘制门窗
        self._draw_doors_and_windows(layout.rooms)
        
        # 显示房间信息
        if self.config.show_areas:
            self._draw_room_info(layout.rooms)
        
        # 设置标题
        title = '住宅平面图'
        if show_evaluation and evaluation_results:
            if isinstance(evaluation_results, dict) and 'total' in evaluation_results:
                score = evaluation_results['total'].get('weighted_score', 0)
                title += f' (评分: {score:.3f})'
            elif isinstance(evaluation_results, (int, float)):
                title += f' (评分: {evaluation_results:.3f})'
        
        self.ax.set_title(title, fontsize=16, fontweight='bold')
        
        # 设置网格
        self.ax.grid(True, alpha=0.3)
        
        # 设置方向
        self.ax.invert_yaxis()
    
    def _draw_rooms(self, rooms: List[Room]) -> None:
        """绘制房间"""
        for room in rooms:
            # 获取房间颜色
            color = self.config.room_colors.get(room.room_type, '#FFFFFF')
            
            # 绘制房间矩形
            rect = patches.Rectangle(
                (room.bounds.x, room.bounds.y),
                room.bounds.width,
                room.bounds.height,
                linewidth=self.config.wall_width,
                edgecolor=self.config.wall_color,
                facecolor=color,
                alpha=0.7
            )
            self.ax.add_patch(rect)
    
    def _draw_hallways(self, hallways: List[Rectangle]) -> None:
        """绘制走廊"""
        for hallway in hallways:
            rect = patches.Rectangle(
                (hallway.x, hallway.y),
                hallway.width,
                hallway.height,
                linewidth=self.config.wall_width,
                edgecolor=self.config.wall_color,
                facecolor=self.config.room_colors[RoomType.HALLWAY],
                alpha=0.5
            )
            self.ax.add_patch(rect)
    
    def _draw_doors_and_windows(self, rooms: List[Room]) -> None:
        """绘制门窗"""
        for room in rooms:
            # 绘制门（简化版本，暂时跳过具体绘制）
            for door in room.doors:
                # 简化的门绘制 - 跳过，避免属性错误
                pass
            
            # 绘制窗户（简化版本，暂时跳过具体绘制）
            for window in room.windows:
                # 简化的窗户绘制 - 跳过，避免属性错误
                pass
    
    def _draw_room_info(self, rooms: List[Room]) -> None:
        """绘制房间信息"""
        for room in rooms:
            # 计算房间中心
            center_x = room.bounds.x + room.bounds.width / 2
            center_y = room.bounds.y + room.bounds.height / 2
            
            # 房间名称
            room_names = {
                RoomType.LIVING_ROOM: '客厅',
                RoomType.BEDROOM: '卧室',
                RoomType.KITCHEN: '厨房',
                RoomType.BATHROOM: '卫生间',
                RoomType.DINING_ROOM: '餐厅',
                RoomType.STUDY: '书房',
                RoomType.BALCONY: '阳台',
                RoomType.HALLWAY: '走廊',
                RoomType.STORAGE: '储藏室'
            }
            
            room_name = room_names.get(room.room_type, '房间')
            area = room.bounds.width * room.bounds.height
            
            # 添加文本
            text = f'{room_name}\\n{area:.1f}m²'
            self.ax.text(
                center_x, center_y,
                text,
                ha='center',
                va='center',
                fontsize=self.config.font_size,
                fontweight='bold',
                color=self.config.text_color
            )
    
    def save_image(self, filename: str, dpi: int = 300) -> None:
        """保存图像"""
        if self.fig is None:
            raise ValueError("请先调用 render_layout 方法")
        
        self.fig.savefig(
            filename,
            dpi=dpi,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
    
    def show(self) -> None:
        """显示图形"""
        if self.fig is not None:
            plt.show()
    
    def close(self) -> None:
        """关闭图形"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None


class InteractiveVisualization:
    """交互式可视化（简化版本）"""
    
    def __init__(self, config: Optional[SimpleVisualizationConfig] = None):
        self.renderer = SimpleLayoutRenderer(config)
        self.current_layout = None
        self.evaluation_results = None
    
    def setup_interactive_canvas(self, parent_widget):
        """设置交互式画布（简化版本）"""
        self.renderer.setup_figure()
        
        # 简化版本 - 直接返回基本的画布
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(self.renderer.fig, parent_widget)
        canvas.draw()
        self.renderer.canvas = canvas
        return canvas
    
    def update_layout(self, layout: Layout, 
                     show_evaluation: bool = False,
                     evaluation_results: Optional[Dict] = None) -> None:
        """更新布局"""
        self.current_layout = layout
        self.evaluation_results = evaluation_results
        self.renderer.render_layout(layout, show_evaluation, evaluation_results)
        
        if self.renderer.canvas:
            self.renderer.canvas.draw()
    
    # 简化的鼠标事件处理（占位符）
    def on_mouse_press(self, event):
        pass
    
    def on_mouse_release(self, event):
        pass
    
    def on_mouse_motion(self, event):
        pass
    
    def on_mouse_scroll(self, event):
        pass


# 为了兼容性，创建别名
LayoutRenderer = SimpleLayoutRenderer
VisualizationConfig = SimpleVisualizationConfig