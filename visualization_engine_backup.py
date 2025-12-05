"""
2D可视化渲染引擎
使用Matplotlib实现住宅平面图的实时绘制和展示
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle as MplRectangle, FancyBboxPatch
import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib.colors as mcolors

from core_data_structures import (
    Layout, Room, RoomType, Rectangle, Point
)


class VisualizationConfig:
    """可视化配置"""
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
            RoomType.STORAGE: '#FAFAFA',          # 浅灰色 - 储物间
            RoomType.HALLWAY: '#F5F5F5',          # 灰白色 - 走廊
        }
        
        self.wall_color = '#37474F'               # 墙体颜色
        self.door_color = '#8D6E63'               # 门颜色
        self.window_color = '#64B5F6'             # 窗户颜色
        self.furniture_color = '#795548'          # 家具颜色
        self.text_color = '#263238'               # 文字颜色
        
        # 线条配置
        self.wall_width = 3                       # 墙体线宽
        self.door_width = 2                       # 门线宽
        self.window_width = 2                     # 窗户线宽
        self.furniture_width = 1                 # 家具线宽
        
        # 字体配置
        self.room_font_size = 10                  # 房间标签字体大小
        self.area_font_size = 8                   # 面积标签字体大小
        self.font_family = 'SimHei'               # 中文字体
        
        # 尺寸配置
        self.door_arc_radius = 0.5                # 门开启弧线半径
        self.window_thickness = 0.2               # 窗户厚度
        self.furniture_alpha = 0.7                # 家具透明度
        
        # 布局配置
        self.margin = 0.5                         # 边距
        self.grid_alpha = 0.1                     # 网格透明度
        self.show_dimensions = True               # 显示尺寸
        self.show_areas = True                    # 显示面积
        self.show_furniture = True                # 显示家具


class LayoutRenderer:
    """布局渲染器"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.fig = None
        self.ax = None
        self.canvas = None
        
        # 交互状态
        self.selected_room = None
        self.highlighted_rooms = []
        self.zoom_level = 1.0
        self.pan_offset = [0, 0]
        
    def setup_figure(self, figsize: Tuple[int, int] = (12, 8)) -> None:
        """设置图形"""
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=self.config.grid_alpha)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = [self.config.font_family, 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
    
    def render_layout(self, layout: Layout, 
                     show_evaluation: bool = False,
                     evaluation_results: Optional[Dict] = None) -> None:
        """渲染布局"""
        if self.ax is None:
            self.setup_figure()
        
        self.ax.clear()
        
        # 计算布局边界和设置坐标轴
        self._setup_axes(layout)
        
        # 绘制背景网格
        self._draw_grid()
        
        # 绘制房间
        self._draw_rooms(layout.rooms)
        
        # 绘制走廊
        self._draw_hallways(layout.hallways)
        
        # 绘制家具
        if self.config.show_furniture:
            self._draw_furniture(layout.rooms)
        
        # 绘制评估结果
        if show_evaluation and evaluation_results:
            self._draw_evaluation_info(evaluation_results)
        
        # 设置标题和标签
        self.ax.set_title('住宅平面图', fontsize=16, fontweight='bold', color=self.config.text_color)
        self.ax.set_xlabel('宽度 (米)', fontsize=12, color=self.config.text_color)
        self.ax.set_ylabel('深度 (米)', fontsize=12, color=self.config.text_color)
        
        # 添加图例
        self._add_legend()
    
    def _setup_axes(self, layout: Layout) -> None:
        """设置坐标轴"""
        margin = self.config.margin
        
        x_min = layout.bounds.x - margin
        x_max = layout.bounds.right + margin
        y_min = layout.bounds.y - margin
        y_max = layout.bounds.bottom + margin
        
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        
        # 设置坐标轴刻度
        self.ax.set_xticks(np.arange(x_min, x_max + 1, 1))
        self.ax.set_yticks(np.arange(y_min, y_max + 1, 1))
    
    def _draw_grid(self) -> None:
        """绘制背景网格"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # 垂直网格线
        for x in np.arange(int(xlim[0]), int(xlim[1]) + 1, 1):
            self.ax.axvline(x=x, color='gray', alpha=self.config.grid_alpha, linestyle='--')
        
        # 水平网格线
        for y in np.arange(int(ylim[0]), int(ylim[1]) + 1, 1):
            self.ax.axhline(y=y, color='gray', alpha=self.config.grid_alpha, linestyle='--')
    
    def _draw_rooms(self, rooms: List[Room]) -> None:
        """绘制房间"""
        for room in rooms:
            # 获取房间颜色
            room_color = self.config.room_colors.get(room.room_type, '#FFFFFF')
            
            # 检查是否为高亮房间
            is_highlighted = room in self.highlighted_rooms
            edge_color = 'red' if is_highlighted else self.config.wall_color
            edge_width = self.config.wall_width * 1.5 if is_highlighted else self.config.wall_width
            
            # 绘制房间主体
            rect = FancyBboxPatch(
                (room.bounds.x, room.bounds.y),
                room.bounds.width,
                room.bounds.height,
                boxstyle="round,pad=0.02",
                facecolor=room_color,
                edgecolor=edge_color,
                linewidth=edge_width,
                alpha=0.8 if is_highlighted else 1.0
            )
            self.ax.add_patch(rect)
            
            # 绘制房间标签
            self._draw_room_label(room)
            
            # 绘制门窗
            self._draw_doors(room.doors)
            self._draw_windows(room.windows)
    
    def _draw_room_label(self, room: Room) -> None:
        """绘制房间标签"""
        center_x = room.bounds.center.x
        center_y = room.bounds.center.y
        
        # 房间类型名称
        room_names = {
            RoomType.LIVING_ROOM: '客厅',
            RoomType.BEDROOM: '卧室',
            RoomType.KITCHEN: '厨房',
            RoomType.BATHROOM: '卫生间',
            RoomType.DINING_ROOM: '餐厅',
            RoomType.STUDY: '书房',
            RoomType.BALCONY: '阳台',
            RoomType.STORAGE: '储物间',
            RoomType.HALLWAY: '走廊',
        }
        
        room_name = room_names.get(room.room_type, room.room_type.value)
        
        # 绘制房间名称
        self.ax.text(center_x, center_y + 0.5, room_name,
                    ha='center', va='center',
                    fontsize=self.config.room_font_size,
                    fontweight='bold',
                    color=self.config.text_color)
        
        # 绘制面积信息
        if self.config.show_areas:
            area_text = f'{room.area:.1f}m²'
            self.ax.text(center_x, center_y - 0.5, area_text,
                        ha='center', va='center',
                        fontsize=self.config.area_font_size,
                        color=self.config.text_color)
        
        # 绘制尺寸标注
        if self.config.show_dimensions:
            self._draw_dimensions(room.bounds)
    
    def _draw_dimensions(self, bounds: Rectangle) -> None:
        """绘制尺寸标注"""
        # 水平尺寸
        self.ax.text(bounds.center.x, bounds.y - 0.2,
                    f'{bounds.width:.1f}m',
                    ha='center', va='top',
                    fontsize=self.config.area_font_size - 1,
                    color='gray')
        
        # 垂直尺寸
        self.ax.text(bounds.x - 0.2, bounds.center.y,
                    f'{bounds.height:.1f}m',
                    ha='right', va='center',
                    fontsize=self.config.area_font_size - 1,
                    color='gray',
                    rotation=90)
    
    def _draw_doors(self, doors: List[Rectangle]) -> None:
        """绘制门"""
        for door in doors:
            # 绘制门扇
            door_rect = MplRectangle(
                (door.x, door.y),
                door.width,
                door.height,
                facecolor=self.config.door_color,
                edgecolor=self.config.door_color,
                linewidth=self.config.door_width
            )
            self.ax.add_patch(door_rect)
            
            # 绘制门开启弧线（简化版）
            if door.width > door.height:
                # 水平门
                arc_center = (door.right, door.y) if door.width > 1 else (door.x, door.y)
                arc_angle = 90 if door.width > 1 else -90
            else:
                # 垂直门
                arc_center = (door.x, door.bottom) if door.height > 1 else (door.x, door.y)
                arc_angle = 180 if door.height > 1 else -180
            
            # 简化：只绘制一条线表示门开启方向
            if door.width > door.height:
                self.ax.plot([door.x, door.x + self.config.door_arc_radius],
                           [door.y, door.y + self.config.door_arc_radius],
                           color=self.config.door_color, linewidth=1, linestyle='--')
            else:
                self.ax.plot([door.x, door.x + self.config.door_arc_radius],
                           [door.y, door.y + self.config.door_arc_radius],
                           color=self.config.door_color, linewidth=1, linestyle='--')
    
    def _draw_windows(self, windows: List[Rectangle]) -> None:
        """绘制窗户"""
        for window in windows:
            # 绘制窗户
            window_rect = MplRectangle(
                (window.x, window.y),
                window.width,
                window.height,
                facecolor='none',
                edgecolor=self.config.window_color,
                linewidth=self.config.window_width,
                linestyle='-'
            )
            self.ax.add_patch(window_rect)
            
            # 绘制窗户玻璃效果（多条平行线）
            if window.width > window.height:
                # 水平窗户
                for i in range(1, 4):
                    y_pos = window.y + window.height * i / 4
                    self.ax.plot([window.x, window.x + window.width],
                               [y_pos, y_pos],
                               color=self.config.window_color, linewidth=0.5, alpha=0.7)
            else:
                # 垂直窗户
                for i in range(1, 4):
                    x_pos = window.x + window.width * i / 4
                    self.ax.plot([x_pos, x_pos],
                               [window.y, window.y + window.height],
                               color=self.config.window_color, linewidth=0.5, alpha=0.7)
    
    def _draw_hallways(self, hallways: List[Rectangle]) -> None:
        """绘制走廊"""
        for hallway in hallways:
            hallway_rect = MplRectangle(
                (hallway.x, hallway.y),
                hallway.width,
                hallway.height,
                facecolor=self.config.room_colors[RoomType.HALLWAY],
                edgecolor=self.config.wall_color,
                linewidth=self.config.wall_width,
                alpha=0.6
            )
            self.ax.add_patch(hallway_rect)
            
            # 添加走廊标签
            if hallway.area > 2:  # 只为大走廊添加标签
                self.ax.text(hallway.center.x, hallway.center.y, '走廊',
                           ha='center', va='center',
                           fontsize=self.config.area_font_size,
                           color=self.config.text_color)
    
    def _draw_furniture(self, rooms: List[Room]) -> None:
        """绘制家具"""
        for room in rooms:
            for furniture in room.furniture:
                if furniture.is_placed:
                    # 绘制家具
                    furniture_rect = MplRectangle(
                        (furniture.position.x, furniture.position.y),
                        furniture.current_width,
                        furniture.current_height,
                        facecolor=self.config.furniture_color,
                        edgecolor=self.config.furniture_color,
                        linewidth=self.config.furniture_width,
                        alpha=self.config.furniture_alpha
                    )
                    self.ax.add_patch(furniture_rect)
                    
                    # 添加家具标签
                    self.ax.text(furniture.position.x + furniture.current_width / 2,
                               furniture.position.y + furniture.current_height / 2,
                               furniture.name[:2],  # 只显示前两个字
                               ha='center', va='center',
                               fontsize=6,
                               color='white',
                               fontweight='bold')
    
    def _draw_evaluation_info(self, evaluation_results: Dict) -> None:
        """绘制评估信息"""
        # 在右上角显示评估结果
        info_text = "评估结果:\n"
        
        dimension_names = {
            'spaceefficiency': '空间效率',
            'lighting': '采光',
            'ventilation': '通风',
            'circulation': '动线',
            'comfort': '舒适度'
        }
        
        for key, result in evaluation_results.items():
            if key == 'total':
                info_text += f"\n总分: {result['weighted_score']:.2f}"
            elif key in dimension_names:
                name = dimension_names[key]
                score = result['score']
                info_text += f"{name}: {score:.2f}\n"
        
        # 在图中显示文本框
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        self.ax.text(xlim[1] - 2, ylim[1] - 2, info_text,
                    fontsize=9,
                    verticalalignment='top',
                    horizontalalignment='right',
                    bbox=dict(boxstyle='round,pad=0.5', 
                             facecolor='white', 
                             edgecolor='gray',
                             alpha=0.8))
    
    def _add_legend(self) -> None:
        """添加图例"""
        legend_elements = []
        
        room_names = {
            RoomType.LIVING_ROOM: '客厅',
            RoomType.BEDROOM: '卧室',
            RoomType.KITCHEN: '厨房',
            RoomType.BATHROOM: '卫生间',
            RoomType.DINING_ROOM: '餐厅',
        }
        
        for room_type, name in room_names.items():
            color = self.config.room_colors.get(room_type, '#FFFFFF')
            legend_elements.append(
                patches.Patch(facecolor=color, edgecolor=self.config.wall_color, label=name)
            )
        
        self.ax.legend(handles=legend_elements, loc='upper left', fontsize=8)
    
    def save_image(self, filename: str, dpi: int = 300) -> None:
        """保存图像"""
        if self.fig:
            self.fig.savefig(filename, dpi=dpi, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
    
    def clear(self) -> None:
        """清除画布"""
        if self.ax:
            self.ax.clear()
    
    def highlight_room(self, room: Room) -> None:
        """高亮房间"""
        self.highlighted_rooms.append(room)
    
    def clear_highlights(self) -> None:
        """清除高亮"""
        self.highlighted_rooms = []
    
    def zoom(self, factor: float) -> None:
        """缩放"""
        self.zoom_level *= factor
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        center_x = (xlim[0] + xlim[1]) / 2
        center_y = (ylim[0] + ylim[1]) / 2
        width = (xlim[1] - xlim[0]) / factor
        height = (ylim[1] - ylim[0]) / factor
        
        self.ax.set_xlim(center_x - width / 2, center_x + width / 2)
        self.ax.set_ylim(center_y - height / 2, center_y + height / 2)
    
    def pan(self, dx: float, dy: float) -> None:
        """平移"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)


class InteractiveVisualization:
    """交互式可视化"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.renderer = LayoutRenderer(config)
        self.current_layout = None
        self.evaluation_results = None
        
        # 鼠标交互状态
        self.mouse_pressed = False
        self.last_mouse_pos = None
    
    def setup_interactive_canvas(self, parent_widget) -> FigureCanvasTkAgg:
        """设置交互式画布"""
        self.renderer.setup_figure()
        canvas = FigureCanvasTkAgg(self.renderer.fig, parent_widget)
        canvas.draw()
        
        # 绑定鼠标事件
        canvas.mpl_connect('button_press_event', self.on_mouse_press)
        canvas.mpl_connect('button_release_event', self.on_mouse_release)
        canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)
        canvas.mpl_connect('scroll_event', self.on_mouse_scroll)
        
        self.renderer.canvas = canvas
        return canvas
    
    def update_layout(self, layout: Layout, 
                     show_evaluation: bool = False,
                     evaluation_results: Optional[Dict] = None) -> None:
        """更新布局显示"""
        self.current_layout = layout
        self.evaluation_results = evaluation_results
        
        self.renderer.render_layout(layout, show_evaluation, evaluation_results)
        
        if self.renderer.canvas:
            self.renderer.canvas.draw()
    
    def on_mouse_press(self, event):
        """鼠标按下事件"""
        if event.button == 1:  # 左键
            self.mouse_pressed = True
            self.last_mouse_pos = (event.xdata, event.ydata)
            
            # 检查是否点击了房间
            if self.current_layout and event.xdata and event.ydata:
                point = Point(event.xdata, event.ydata)
                for room in self.current_layout.rooms:
                    if room.bounds.contains_point(point):
                        self.renderer.highlight_room(room)
                        self.update_layout(self.current_layout, True, self.evaluation_results)
                        break
    
    def on_mouse_release(self, event):
        """鼠标释放事件"""
        self.mouse_pressed = False
        self.last_mouse_pos = None
        self.renderer.clear_highlights()
    
    def on_mouse_motion(self, event):
        """鼠标移动事件"""
        if self.mouse_pressed and self.last_mouse_pos and event.xdata and event.ydata:
            # 平移
            dx = event.xdata - self.last_mouse_pos[0]
            dy = event.ydata - self.last_mouse_pos[1]
            self.renderer.pan(dx, dy)
            
            if self.renderer.canvas:
                self.renderer.canvas.draw()
    
    def on_mouse_scroll(self, event):
        """鼠标滚轮事件"""
        if event.xdata and event.ydata:
            # 缩放
            scale_factor = 1.1 if event.button == 'up' else 0.9
            self.renderer.zoom(scale_factor)
            
            if self.renderer.canvas:
                self.renderer.canvas.draw()


class ComparisonVisualization:
    """对比可视化"""
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
    
    def compare_layouts(self, layouts: List[Layout], 
                        titles: List[str],
                        evaluations: Optional[List[Dict]] = None) -> None:
        """对比多个布局"""
        n = len(layouts)
        cols = min(3, n)
        rows = (n + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
        if n == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        for i, (layout, title) in enumerate(zip(layouts, titles)):
            if i >= len(axes):
                break
                
            ax = axes[i]
            
            # 渲染单个布局
            renderer = LayoutRenderer(self.config)
            renderer.ax = ax
            
            # 设置坐标轴
            margin = self.config.margin
            x_min = layout.bounds.x - margin
            x_max = layout.bounds.right + margin
            y_min = layout.bounds.y - margin
            y_max = layout.bounds.bottom + margin
            
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            ax.set_aspect('equal')
            
            # 绘制布局
            renderer._draw_rooms(layout.rooms)
            renderer._draw_hallways(layout.hallways)
            
            # 添加评估信息
            if evaluations and i < len(evaluations):
                total_score = evaluations[i].get('total', {}).get('weighted_score', 0)
                title += f' (得分: {total_score:.2f})'
            
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.1)
        
        # 隐藏多余的子图
        for i in range(n, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    # 测试代码
    from core_data_structures import Rectangle, Room, RoomType, Layout
    
    # 创建测试布局
    bounds = Rectangle(0, 0, 20, 15)
    layout = Layout(bounds)
    
    # 添加房间
    living_room = Room(RoomType.LIVING_ROOM, Rectangle(2, 2, 8, 6))
    kitchen = Room(RoomType.KITCHEN, Rectangle(10, 2, 5, 4))
    bedroom = Room(RoomType.BEDROOM, Rectangle(2, 8, 6, 5))
    bathroom = Room(RoomType.BATHROOM, Rectangle(8, 8, 3, 3))
    
    # 添加门窗
    living_room.add_window(Rectangle(2, 2, 2, 0.2))
    living_room.add_door(Rectangle(8, 4, 0.8, 0.1))
    bedroom.add_window(Rectangle(2, 8, 2, 0.2))
    bedroom.add_door(Rectangle(6, 10, 0.8, 0.1))
    bathroom.add_door(Rectangle(8, 9, 0.8, 0.1))
    
    layout.add_room(living_room)
    layout.add_room(kitchen)
    layout.add_room(bedroom)
    layout.add_room(bathroom)
    
    # 创建可视化
    renderer = LayoutRenderer()
    renderer.render_layout(layout)
    
    # 保存图像
    renderer.save_image('test_layout.png')
    
    print("可视化测试完成，图像已保存为 test_layout.png")