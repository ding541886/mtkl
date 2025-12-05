"""
结果导出系统
支持PNG、SVG、DXF等多种格式的平面图输出
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import tempfile

# 图像导出
import matplotlib.pyplot as plt
from matplotlib.backends.backend_svg import FigureCanvasSVG
from PIL import Image, ImageDraw, ImageFont

# SVG导出
import xml.etree.ElementTree as ET

# DXF导出
try:
    import ezdxf
    from ezdxf import entities
    DXF_AVAILABLE = True
except ImportError:
    DXF_AVAILABLE = False
    print("警告: ezdxf 未安装，DXF导出功能将不可用")

# PDF导出
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.units import mm
    from reportlab.lib.colors import black, white, lightgrey
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("警告: reportlab 未安装，PDF导出功能将不可用")

from core_data_structures import (
    Layout, Room, RoomType, Rectangle, Point, Furniture
)
from visualization_engine import VisualizationConfig


class ExportConfig:
    """导出配置"""
    def __init__(self):
        # 图像配置
        self.image_dpi = 300
        self.image_format = 'PNG'
        self.image_quality = 95
        
        # 尺寸配置
        self.scale_factor = 100  # 1:100 比例
        self.margin = 20  # 边距(像素)
        
        # 样式配置
        self.show_grid = False
        self.show_dimensions = True
        self.show_annotations = True
        self.show_legend = True
        
        # 颜色配置
        self.use_colors = True
        self.black_white_mode = False
        
        # 元数据配置
        self.include_metadata = True
        self.include_evaluation = True


class BaseExporter:
    """导出器基类"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
    
    def export(self, layout: Layout, filename: str, 
               evaluation_results: Optional[Dict] = None) -> bool:
        """导出布局"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _get_room_color(self, room_type: RoomType) -> str:
        """获取房间颜色"""
        if self.config.black_white_mode:
            return "#FFFFFF"
        
        colors = {
            RoomType.LIVING_ROOM: '#E8F5E9',
            RoomType.BEDROOM: '#E3F2FD',
            RoomType.KITCHEN: '#FFF3E0',
            RoomType.BATHROOM: '#F3E5F5',
            RoomType.DINING_ROOM: '#FFEBEE',
            RoomType.STUDY: '#E0F2F1',
            RoomType.BALCONY: '#F1F8E9',
            RoomType.STORAGE: '#FAFAFA',
            RoomType.HALLWAY: '#F5F5F5',
        }
        return colors.get(room_type, '#FFFFFF')
    
    def _get_room_name(self, room_type: RoomType) -> str:
        """获取房间名称"""
        names = {
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
        return names.get(room_type, room_type.value)


class PNGExporter(BaseExporter):
    """PNG图像导出器"""
    
    def export(self, layout: Layout, filename: str, 
               evaluation_results: Optional[Dict] = None) -> bool:
        """导出为PNG格式"""
        try:
            # 使用可视化引擎生成图像
            from visualization_engine import LayoutRenderer
            
            config = VisualizationConfig()
            config.show_dimensions = self.config.show_dimensions
            config.show_areas = self.config.show_annotations
            config.show_furniture = True
            
            renderer = LayoutRenderer(config)
            renderer.render_layout(layout, 
                                show_evaluation=self.config.include_evaluation,
                                evaluation_results=evaluation_results)
            
            # 保存图像
            renderer.fig.savefig(
                filename,
                dpi=self.config.image_dpi,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none',
                format='PNG'
            )
            
            plt.close(renderer.fig)
            return True
            
        except Exception as e:
            print(f"PNG导出失败: {str(e)}")
            return False


class SVGExporter(BaseExporter):
    """SVG矢量图导出器"""
    
    def export(self, layout: Layout, filename: str, 
               evaluation_results: Optional[Dict] = None) -> bool:
        """导出为SVG格式"""
        try:
            # 创建SVG根元素
            svg = ET.Element('svg', {
                'xmlns': 'http://www.w3.org/2000/svg',
                'version': '1.1',
                'width': f'{layout.bounds.width * self.config.scale_factor}px',
                'height': f'{layout.bounds.height * self.config.scale_factor}px',
                'viewBox': f'0 0 {layout.bounds.width * self.config.scale_factor} {layout.bounds.height * self.config.scale_factor}'
            })
            
            # 添加样式定义
            self._add_svg_styles(svg)
            
            # 绘制房间
            self._draw_svg_rooms(svg, layout.rooms)
            
            # 绘制走廊
            self._draw_svg_hallways(svg, layout.hallways)
            
            # 绘制标注
            if self.config.show_annotations:
                self._draw_svg_annotations(svg, layout.rooms)
            
            # 保存文件
            tree = ET.ElementTree(svg)
            tree.write(filename, encoding='utf-8', xml_declaration=True)
            
            return True
            
        except Exception as e:
            print(f"SVG导出失败: {str(e)}")
            return False
    
    def _add_svg_styles(self, svg: ET.Element):
        """添加SVG样式"""
        style = ET.SubElement(svg, 'defs')
        
        # 墙体样式
        wall_style = ET.SubElement(style, 'style')
        wall_style.text = """
        .wall { stroke: #37474F; stroke-width: 3; fill: none; }
        .room-fill { opacity: 0.8; }
        .room-text { font-family: Arial, sans-serif; font-size: 12px; fill: #263238; text-anchor: middle; }
        .area-text { font-family: Arial, sans-serif; font-size: 10px; fill: #666666; text-anchor: middle; }
        .door { stroke: #8D6E63; stroke-width: 2; fill: #8D6E63; }
        .window { stroke: #64B5F6; stroke-width: 2; fill: none; }
        """
    
    def _draw_svg_rooms(self, svg: ET.Element, rooms: List[Room]):
        """绘制SVG房间"""
        for room in rooms:
            # 转换坐标
            x = room.bounds.x * self.config.scale_factor
            y = room.bounds.y * self.config.scale_factor
            width = room.bounds.width * self.config.scale_factor
            height = room.bounds.height * self.config.scale_factor
            
            # 绘制房间填充
            fill_color = self._get_room_color(room.room_type)
            rect_fill = ET.SubElement(svg, 'rect', {
                'x': str(x),
                'y': str(y),
                'width': str(width),
                'height': str(height),
                'fill': fill_color,
                'class': 'room-fill'
            })
            
            # 绘制房间边框
            rect_stroke = ET.SubElement(svg, 'rect', {
                'x': str(x),
                'y': str(y),
                'width': str(width),
                'height': str(height),
                'class': 'wall'
            })
            
            # 绘制门窗
            self._draw_svg_doors(svg, room.doors)
            self._draw_svg_windows(svg, room.windows)
    
    def _draw_svg_hallways(self, svg: ET.Element, hallways: List[Rectangle]):
        """绘制SVG走廊"""
        for hallway in hallways:
            x = hallway.x * self.config.scale_factor
            y = hallway.y * self.config.scale_factor
            width = hallway.width * self.config.scale_factor
            height = hallway.height * self.config.scale_factor
            
            rect = ET.SubElement(svg, 'rect', {
                'x': str(x),
                'y': str(y),
                'width': str(width),
                'height': str(height),
                'fill': '#F5F5F5',
                'stroke': '#37474F',
                'stroke-width': '3'
            })
    
    def _draw_svg_doors(self, svg: ET.Element, doors: List[Rectangle]):
        """绘制SVG门"""
        for door in doors:
            x = door.x * self.config.scale_factor
            y = door.y * self.config.scale_factor
            width = door.width * self.config.scale_factor
            height = door.height * self.config.scale_factor
            
            rect = ET.SubElement(svg, 'rect', {
                'x': str(x),
                'y': str(y),
                'width': str(width),
                'height': str(height),
                'class': 'door'
            })
    
    def _draw_svg_windows(self, svg: ET.Element, windows: List[Rectangle]):
        """绘制SVG窗户"""
        for window in windows:
            x = window.x * self.config.scale_factor
            y = window.y * self.config.scale_factor
            width = window.width * self.config.scale_factor
            height = window.height * self.config.scale_factor
            
            rect = ET.SubElement(svg, 'rect', {
                'x': str(x),
                'y': str(y),
                'width': str(width),
                'height': str(height),
                'class': 'window'
            })
    
    def _draw_svg_annotations(self, svg: ET.Element, rooms: List[Room]):
        """绘制SVG标注"""
        for room in rooms:
            center_x = room.bounds.center.x * self.config.scale_factor
            center_y = room.bounds.center.y * self.config.scale_factor
            
            # 房间名称
            room_name = self._get_room_name(room.room_type)
            text = ET.SubElement(svg, 'text', {
                'x': str(center_x),
                'y': str(center_y - 10),
                'class': 'room-text'
            })
            text.text = room_name
            
            # 房间面积
            area_text = f'{room.area:.1f}m²'
            text_area = ET.SubElement(svg, 'text', {
                'x': str(center_x),
                'y': str(center_y + 10),
                'class': 'area-text'
            })
            text_area.text = area_text


class DXFExporter(BaseExporter):
    """DXF CAD文件导出器"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        super().__init__(config)
        if not DXF_AVAILABLE:
            raise ImportError("需要安装 ezdxf 库来使用DXF导出功能")
    
    def export(self, layout: Layout, filename: str, 
               evaluation_results: Optional[Dict] = None) -> bool:
        """导出为DXF格式"""
        try:
            # 创建DXF文档
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # 设置图层
            self._setup_dxf_layers(doc)
            
            # 绘制房间
            self._draw_dxf_rooms(msp, layout.rooms)
            
            # 绘制走廊
            self._draw_dxf_hallways(msp, layout.hallways)
            
            # 添加标注
            if self.config.show_annotations:
                self._draw_dxf_annotations(msp, layout.rooms)
            
            # 添加元数据
            if self.config.include_metadata:
                self._add_dxf_metadata(doc, layout, evaluation_results)
            
            # 保存文件
            doc.saveas(filename)
            return True
            
        except Exception as e:
            print(f"DXF导出失败: {str(e)}")
            return False
    
    def _setup_dxf_layers(self, doc):
        """设置DXF图层"""
        # 墙体图层
        doc.layers.new('WALLS', dxfattribs={'color': 7, 'lineweight': 50})
        
        # 房间填充图层
        doc.layers.new('ROOMS', dxfattribs={'color': 2, 'lineweight': 25})
        
        # 门窗图层
        doc.layers.new('DOORS', dxfattribs={'color': 3, 'lineweight': 30})
        doc.layers.new('WINDOWS', dxfattribs={'color': 5, 'lineweight': 30})
        
        # 标注图层
        doc.layers.new('TEXT', dxfattribs={'color': 7, 'lineweight': 0})
        doc.layers.new('DIMENSIONS', dxfattribs={'color': 7, 'lineweight': 13})
    
    def _draw_dxf_rooms(self, msp, rooms: List[Room]):
        """绘制DXF房间"""
        for room in rooms:
            # 转换坐标和尺寸
            x = room.bounds.x * self.config.scale_factor
            y = room.bounds.y * self.config.scale_factor
            width = room.bounds.width * self.config.scale_factor
            height = room.bounds.height * self.config.scale_factor
            
            # 绘制房间填充
            msp.add_lwpolyline([
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y + height)
            ], close=True, dxfattribs={'layer': 'ROOMS'})
            
            # 绘制墙体
            msp.add_lwpolyline([
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y + height)
            ], close=True, dxfattribs={'layer': 'WALLS'})
            
            # 绘制门窗
            self._draw_dxf_doors(msp, room.doors)
            self._draw_dxf_windows(msp, room.windows)
    
    def _draw_dxf_hallways(self, msp, hallways: List[Rectangle]):
        """绘制DXF走廊"""
        for hallway in hallways:
            x = hallway.x * self.config.scale_factor
            y = hallway.y * self.config.scale_factor
            width = hallway.width * self.config.scale_factor
            height = hallway.height * self.config.scale_factor
            
            msp.add_lwpolyline([
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y + height)
            ], close=True, dxfattribs={'layer': 'ROOMS'})
    
    def _draw_dxf_doors(self, msp, doors: List[Rectangle]):
        """绘制DXF门"""
        for door in doors:
            x = door.x * self.config.scale_factor
            y = door.y * self.config.scale_factor
            width = door.width * self.config.scale_factor
            height = door.height * self.config.scale_factor
            
            msp.add_lwpolyline([
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y + height)
            ], close=True, dxfattribs={'layer': 'DOORS'})
    
    def _draw_dxf_windows(self, msp, windows: List[Rectangle]):
        """绘制DXF窗户"""
        for window in windows:
            x = window.x * self.config.scale_factor
            y = window.y * self.config.scale_factor
            width = window.width * self.config.scale_factor
            height = window.height * self.config.scale_factor
            
            msp.add_lwpolyline([
                (x, y),
                (x + width, y),
                (x + width, y + height),
                (x, y + height)
            ], close=True, dxfattribs={'layer': 'WINDOWS'})
    
    def _draw_dxf_annotations(self, msp, rooms: List[Room]):
        """绘制DXF标注"""
        for room in rooms:
            center_x = room.bounds.center.x * self.config.scale_factor
            center_y = room.bounds.center.y * self.config.scale_factor
            
            # 房间名称
            room_name = self._get_room_name(room.room_type)
            msp.add_text(
                room_name,
                dxfattribs={'layer': 'TEXT', 'height': 50}
            ).set_pos((center_x, center_y + 100))
            
            # 房间面积
            area_text = f'{room.area:.1f}m²'
            msp.add_text(
                area_text,
                dxfattribs={'layer': 'TEXT', 'height': 30}
            ).set_pos((center_x, center_y))
    
    def _add_dxf_metadata(self, doc, layout: Layout, 
                          evaluation_results: Optional[Dict] = None):
        """添加DXF元数据"""
        # 添加文档属性
        doc.summary.title = "住宅平面图"
        doc.summary.author = "蒙特卡洛住宅生成系统"
        doc.summary.subject = f"总面积: {layout.total_area:.1f}m²"
        doc.summary.comments = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 添加评估结果
        if evaluation_results:
            total_score = evaluation_results.get('total', {}).get('weighted_score', 0)
            doc.summary.keywords = f"评估得分: {total_score:.2f}"


class PDFExporter(BaseExporter):
    """PDF文档导出器"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        super().__init__(config)
        if not PDF_AVAILABLE:
            raise ImportError("需要安装 reportlab 库来使用PDF导出功能")
    
    def export(self, layout: Layout, filename: str, 
               evaluation_results: Optional[Dict] = None) -> bool:
        """导出为PDF格式"""
        try:
            # 创建PDF画布
            canvas = pdf_canvas.Canvas(filename, pagesize=A4)
            width, height = A4
            
            # 设置边距
            margin = 20 * mm
            usable_width = width - 2 * margin
            usable_height = height - 2 * margin
            
            # 计算缩放比例
            layout_width = layout.bounds.width * self.config.scale_factor
            layout_height = layout.bounds.height * self.config.scale_factor
            scale = min(usable_width / layout_width, usable_height / layout_height)
            
            # 绘制布局
            draw_x = margin + (usable_width - layout_width * scale) / 2
            draw_y = margin + (usable_height - layout_height * scale) / 2
            
            self._draw_pdf_layout(canvas, layout, draw_x, draw_y, scale)
            
            # 添加标题和信息
            self._add_pdf_header(canvas, layout, evaluation_results)
            
            # 添加图例
            if self.config.show_legend:
                self._add_pdf_legend(canvas, margin, height - margin)
            
            # 保存PDF
            canvas.save()
            return True
            
        except Exception as e:
            print(f"PDF导出失败: {str(e)}")
            return False
    
    def _draw_pdf_layout(self, canvas, layout: Layout, x: float, y: float, scale: float):
        """绘制PDF布局"""
        # 绘制房间
        for room in layout.rooms:
            # 转换坐标
            room_x = x + room.bounds.x * self.config.scale_factor * scale
            room_y = y + room.bounds.y * self.config.scale_factor * scale
            room_width = room.bounds.width * self.config.scale_factor * scale
            room_height = room.bounds.height * self.config.scale_factor * scale
            
            # 绘制房间填充
            fill_color = self._get_pdf_color(self._get_room_color(room.room_type))
            canvas.setFillColor(fill_color)
            canvas.rect(room_x, room_y, room_width, room_height, fill=1, stroke=0)
            
            # 绘制房间边框
            canvas.setStrokeColor(black)
            canvas.setLineWidth(2)
            canvas.rect(room_x, room_y, room_width, room_height, fill=0, stroke=1)
            
            # 绘制标注
            if self.config.show_annotations:
                center_x = room_x + room_width / 2
                center_y = room_y + room_height / 2
                
                room_name = self._get_room_name(room.room_type)
                area_text = f'{room.area:.1f}m²'
                
                canvas.setFont("Helvetica-Bold", 12)
                canvas.drawCentredString(center_x, center_y + 10, room_name)
                
                canvas.setFont("Helvetica", 10)
                canvas.drawCentredString(center_x, center_y - 10, area_text)
        
        # 绘制走廊
        for hallway in layout.hallways:
            hall_x = x + hallway.x * self.config.scale_factor * scale
            hall_y = y + hallway.y * self.config.scale_factor * scale
            hall_width = hallway.width * self.config.scale_factor * scale
            hall_height = hallway.height * self.config.scale_factor * scale
            
            canvas.setFillColor(lightgrey)
            canvas.rect(hall_x, hall_y, hall_width, hall_height, fill=1, stroke=1)
    
    def _add_pdf_header(self, canvas, layout: Layout, 
                       evaluation_results: Optional[Dict] = None):
        """添加PDF页眉"""
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(300, 800, "住宅平面图")
        
        canvas.setFont("Helvetica", 12)
        canvas.drawString(50, 780, f"总面积: {layout.total_area:.1f}m²")
        canvas.drawString(50, 765, f"房间数量: {len(layout.rooms)}")
        canvas.drawString(50, 750, f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if evaluation_results:
            total_score = evaluation_results.get('total', {}).get('weighted_score', 0)
            canvas.drawString(50, 735, f"评估得分: {total_score:.2f}")
    
    def _add_pdf_legend(self, canvas, x: float, y: float):
        """添加PDF图例"""
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(x, y, "图例:")
        
        y_offset = y - 20
        room_types = [
            (RoomType.LIVING_ROOM, '客厅'),
            (RoomType.BEDROOM, '卧室'),
            (RoomType.KITCHEN, '厨房'),
            (RoomType.BATHROOM, '卫生间')
        ]
        
        canvas.setFont("Helvetica", 10)
        for room_type, name in room_types:
            fill_color = self._get_pdf_color(self._get_room_color(room_type))
            canvas.setFillColor(fill_color)
            canvas.rect(x, y_offset, 15, 15, fill=1, stroke=1)
            canvas.drawString(x + 20, y_offset + 3, name)
            y_offset -= 20
    
    def _get_pdf_color(self, hex_color: str) -> Tuple[float, float, float]:
        """将十六进制颜色转换为PDF RGB值"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b)


class DataExporter(BaseExporter):
    """数据导出器"""
    
    def export(self, layout: Layout, filename: str, 
               evaluation_results: Optional[Dict] = None) -> bool:
        """导出为JSON数据格式"""
        try:
            # 构建导出数据
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'total_area': layout.total_area,
                    'room_count': len(layout.rooms),
                    'generation_id': layout.generation_id
                },
                'layout': {
                    'bounds': {
                        'x': layout.bounds.x,
                        'y': layout.bounds.y,
                        'width': layout.bounds.width,
                        'height': layout.bounds.height
                    },
                    'rooms': self._serialize_rooms(layout.rooms),
                    'hallways': self._serialize_rectangles(layout.hallways)
                }
            }
            
            # 添加评估结果
            if evaluation_results:
                export_data['evaluation'] = evaluation_results
            
            # 添加布局元数据
            if layout.metadata:
                export_data['layout_metadata'] = layout.metadata
            
            # 保存JSON文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"数据导出失败: {str(e)}")
            return False
    
    def _serialize_rooms(self, rooms: List[Room]) -> List[Dict]:
        """序列化房间数据"""
        serialized = []
        for room in rooms:
            room_data = {
                'type': room.room_type.value,
                'bounds': {
                    'x': room.bounds.x,
                    'y': room.bounds.y,
                    'width': room.bounds.width,
                    'height': room.bounds.height
                },
                'area': room.area,
                'utilization_rate': room.utilization_rate,
                'furniture': self._serialize_furniture(room.furniture),
                'doors': self._serialize_rectangles(room.doors),
                'windows': self._serialize_rectangles(room.windows)
            }
            serialized.append(room_data)
        return serialized
    
    def _serialize_furniture(self, furniture_list: List[Furniture]) -> List[Dict]:
        """序列化家具数据"""
        serialized = []
        for furniture in furniture_list:
            furniture_data = {
                'name': furniture.name,
                'width': furniture.width,
                'height': furniture.height,
                'position': {'x': furniture.position.x, 'y': furniture.position.y},
                'is_rotated': furniture.is_rotated,
                'is_placed': furniture.is_placed,
                'category': furniture.category
            }
            serialized.append(furniture_data)
        return serialized
    
    def _serialize_rectangles(self, rectangles: List[Rectangle]) -> List[Dict]:
        """序列化矩形数据"""
        return [
            {
                'x': rect.x,
                'y': rect.y,
                'width': rect.width,
                'height': rect.height
            }
            for rect in rectangles
        ]


class ExportManager:
    """导出管理器"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
        
        # 初始化导出器
        self.exporters = {
            'PNG': PNGExporter(self.config),
            'SVG': SVGExporter(self.config),
            'JSON': DataExporter(self.config)
        }
        
        # 条件性初始化导出器
        if DXF_AVAILABLE:
            self.exporters['DXF'] = DXFExporter(self.config)
        
        if PDF_AVAILABLE:
            self.exporters['PDF'] = PDFExporter(self.config)
    
    def get_available_formats(self) -> List[str]:
        """获取可用的导出格式"""
        return list(self.exporters.keys())
    
    def export(self, layout: Layout, filename: str, format_type: str,
               evaluation_results: Optional[Dict] = None) -> bool:
        """导出布局"""
        if format_type not in self.exporters:
            print(f"不支持的导出格式: {format_type}")
            return False
        
        exporter = self.exporters[format_type]
        return exporter.export(layout, filename, evaluation_results)
    
    def export_multiple(self, layout: Layout, base_filename: str,
                       formats: List[str],
                       evaluation_results: Optional[Dict] = None) -> Dict[str, bool]:
        """导出多种格式"""
        results = {}
        
        for format_type in formats:
            if format_type in self.exporters:
                filename = f"{base_filename}.{format_type.lower()}"
                success = self.export(layout, filename, format_type, evaluation_results)
                results[format_type] = success
            else:
                results[format_type] = False
        
        return results
    
    def export_with_config(self, layout: Layout, filename: str,
                          format_type: str, config: ExportConfig,
                          evaluation_results: Optional[Dict] = None) -> bool:
        """使用自定义配置导出"""
        # 临时更新配置
        old_config = self.config
        self.config = config
        
        # 更新导出器配置
        for exporter in self.exporters.values():
            exporter.config = config
        
        try:
            result = self.export(layout, filename, format_type, evaluation_results)
            return result
        finally:
            # 恢复原配置
            self.config = old_config
            for exporter in self.exporters.values():
                exporter.config = old_config


class BatchExporter:
    """批量导出器"""
    
    def __init__(self, export_manager: ExportManager):
        self.export_manager = export_manager
    
    def export_layout_batch(self, layouts: List[Layout], output_dir: str,
                           formats: List[str],
                           evaluation_results_list: Optional[List[Dict]] = None) -> Dict[str, List[bool]]:
        """批量导出多个布局"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        results = {format_type: [] for format_type in formats}
        
        for i, layout in enumerate(layouts):
            base_filename = os.path.join(output_dir, f"layout_{i+1:03d}")
            eval_results = evaluation_results_list[i] if evaluation_results_list and i < len(evaluation_results_list) else None
            
            for format_type in formats:
                filename = f"{base_filename}.{format_type.lower()}"
                success = self.export_manager.export(layout, filename, format_type, eval_results)
                results[format_type].append(success)
        
        return results


if __name__ == "__main__":
    # 测试代码
    from core_data_structures import Rectangle, Room, RoomType, Layout
    
    # 创建测试布局
    bounds = Rectangle(0, 0, 20, 15)
    layout = Layout(bounds)
    
    # 添加房间
    living_room = Room(RoomType.LIVING_ROOM, Rectangle(2, 2, 8, 6))
    bedroom = Room(RoomType.BEDROOM, Rectangle(12, 2, 6, 5))
    kitchen = Room(RoomType.KITCHEN, Rectangle(2, 8, 5, 4))
    bathroom = Room(RoomType.BATHROOM, Rectangle(8, 8, 3, 3))
    
    layout.add_room(living_room)
    layout.add_room(bedroom)
    layout.add_room(kitchen)
    layout.add_room(bathroom)
    
    # 创建导出管理器
    export_manager = ExportManager()
    
    print("可用的导出格式:", export_manager.get_available_formats())
    
    # 测试导出
    test_results = {}
    
    # PNG导出
    png_success = export_manager.export(layout, "test_layout.png", "PNG")
    test_results['PNG'] = png_success
    
    # SVG导出
    svg_success = export_manager.export(layout, "test_layout.svg", "SVG")
    test_results['SVG'] = svg_success
    
    # JSON导出
    json_success = export_manager.export(layout, "test_layout.json", "JSON")
    test_results['JSON'] = json_success
    
    # DXF导出（如果可用）
    if 'DXF' in export_manager.get_available_formats():
        dxf_success = export_manager.export(layout, "test_layout.dxf", "DXF")
        test_results['DXF'] = dxf_success
    
    print("导出测试结果:")
    for format_type, success in test_results.items():
        status = "成功" if success else "失败"
        print(f"  {format_type}: {status}")