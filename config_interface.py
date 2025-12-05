"""
参数配置界面
提供房间数量、尺寸、优化权重等设置选项的图形化界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict

from core_data_structures import RoomType
from monte_carlo_engine import MonteCarloConfig
from evaluation_system import EvaluationConfig


@dataclass
class LayoutParameters:
    """布局参数"""
    # 基础尺寸
    total_width: float = 20.0
    total_height: float = 15.0
    wall_thickness: float = 0.2
    
    # 房间配置
    room_requirements: Dict[str, int] = None
    min_room_area: Dict[str, float] = None
    max_room_area: Dict[str, float] = None
    
    def __post_init__(self):
        if self.room_requirements is None:
            self.room_requirements = {
                'living_room': 1,
                'bedroom': 2,
                'kitchen': 1,
                'bathroom': 1,
                'dining_room': 0,
                'study': 0,
                'balcony': 0,
                'storage': 0
            }
        
        if self.min_room_area is None:
            self.min_room_area = {
                'living_room': 15.0,
                'bedroom': 8.0,
                'kitchen': 6.0,
                'bathroom': 3.0,
                'dining_room': 10.0,
                'study': 6.0,
                'balcony': 4.0,
                'storage': 2.0
            }
        
        if self.max_room_area is None:
            self.max_room_area = {
                'living_room': 40.0,
                'bedroom': 25.0,
                'kitchen': 20.0,
                'bathroom': 12.0,
                'dining_room': 25.0,
                'study': 18.0,
                'balcony': 15.0,
                'storage': 8.0
            }


class ParameterConfigWindow:
    """参数配置窗口"""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.window = None
        
        # 参数对象
        self.layout_params = LayoutParameters()
        self.monte_carlo_config = MonteCarloConfig()
        self.evaluation_config = EvaluationConfig()
        
        # 回调函数
        self.on_start_optimization: Optional[Callable] = None
        self.on_load_preset: Optional[Callable] = None
        
        # 预设配置
        self.presets = {
            '小型公寓': self._create_small_apartment_preset(),
            '标准住宅': self._create_standard_house_preset(),
            '大户型': self._create_large_house_preset(),
            '豪华别墅': self._create_luxury_villa_preset()
        }
    
    def show(self) -> None:
        """显示配置窗口"""
        if self.window:
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("参数配置")
        self.window.geometry("900x700")
        self.window.resizable(True, True)
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 基础配置页
        self._create_basic_config_tab(notebook)
        
        # 算法参数页
        self._create_algorithm_config_tab(notebook)
        
        # 评估权重页
        self._create_evaluation_config_tab(notebook)
        
        # 预设配置页
        self._create_preset_config_tab(notebook)
        
        # 按钮区域
        self._create_button_area(main_frame)
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _create_basic_config_tab(self, parent: ttk.Notebook) -> None:
        """创建基础配置标签页"""
        frame = ttk.Frame(parent, padding="10")
        parent.add(frame, text="基础配置")
        
        # 基础尺寸区域
        size_frame = ttk.LabelFrame(frame, text="基础尺寸", padding="10")
        size_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 总宽度
        ttk.Label(size_frame, text="总宽度 (米):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.width_var = tk.DoubleVar(value=self.layout_params.total_width)
        width_spinbox = ttk.Spinbox(size_frame, from_=10, to=50, textvariable=self.width_var, width=15)
        width_spinbox.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 总高度
        ttk.Label(size_frame, text="总高度 (米):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.height_var = tk.DoubleVar(value=self.layout_params.total_height)
        height_spinbox = ttk.Spinbox(size_frame, from_=10, to=50, textvariable=self.height_var, width=15)
        height_spinbox.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 墙体厚度
        ttk.Label(size_frame, text="墙体厚度 (米):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.wall_var = tk.DoubleVar(value=self.layout_params.wall_thickness)
        wall_spinbox = ttk.Spinbox(size_frame, from_=0.1, to=0.5, increment=0.05, 
                                   textvariable=self.wall_var, width=15)
        wall_spinbox.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        size_frame.columnconfigure(1, weight=1)
        
        # 房间配置区域
        room_frame = ttk.LabelFrame(frame, text="房间配置", padding="10")
        room_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建滚动区域
        canvas = tk.Canvas(room_frame)
        scrollbar = ttk.Scrollbar(room_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 房间类型标题
        headers = ["房间类型", "数量", "最小面积", "最大面积"]
        for i, header in enumerate(headers):
            ttk.Label(scrollable_frame, text=header, font=('Arial', 9, 'bold')).grid(
                row=0, column=i, padx=5, pady=5
            )
        
        # 房间配置变量
        self.room_vars = {}
        self.min_area_vars = {}
        self.max_area_vars = {}
        
        room_names = {
            'living_room': '客厅',
            'bedroom': '卧室',
            'kitchen': '厨房',
            'bathroom': '卫生间',
            'dining_room': '餐厅',
            'study': '书房',
            'balcony': '阳台',
            'storage': '储物间'
        }
        
        row = 1
        for room_type, room_name in room_names.items():
            # 房间名称
            ttk.Label(scrollable_frame, text=room_name).grid(row=row, column=0, padx=5, pady=2, sticky=tk.W)
            
            # 数量
            self.room_vars[room_type] = tk.IntVar(value=self.layout_params.room_requirements.get(room_type, 0))
            ttk.Spinbox(scrollable_frame, from_=0, to=5, textvariable=self.room_vars[room_type], 
                       width=10).grid(row=row, column=1, padx=5, pady=2)
            
            # 最小面积
            self.min_area_vars[room_type] = tk.DoubleVar(
                value=self.layout_params.min_room_area.get(room_type, 5.0)
            )
            ttk.Spinbox(scrollable_frame, from_=2, to=50, increment=0.5, 
                       textvariable=self.min_area_vars[room_type], width=10).grid(
                       row=row, column=2, padx=5, pady=2)
            
            # 最大面积
            self.max_area_vars[room_type] = tk.DoubleVar(
                value=self.layout_params.max_room_area.get(room_type, 20.0)
            )
            ttk.Spinbox(scrollable_frame, from_=2, to=50, increment=0.5, 
                       textvariable=self.max_area_vars[room_type], width=10).grid(
                       row=row, column=3, padx=5, pady=2)
            
            row += 1
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        room_frame.columnconfigure(0, weight=1)
        room_frame.rowconfigure(0, weight=1)
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
    
    def _create_algorithm_config_tab(self, parent: ttk.Notebook) -> None:
        """创建算法配置标签页"""
        frame = ttk.Frame(parent, padding="10")
        parent.add(frame, text="算法参数")
        
        # 蒙特卡洛参数
        mc_frame = ttk.LabelFrame(frame, text="蒙特卡洛算法参数", padding="10")
        mc_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 创建算法参数变量
        self.algo_vars = {
            'max_iterations': tk.IntVar(value=self.monte_carlo_config.max_iterations),
            'population_size': tk.IntVar(value=self.monte_carlo_config.population_size),
            'mutation_rate': tk.DoubleVar(value=self.monte_carlo_config.mutation_rate),
            'crossover_rate': tk.DoubleVar(value=self.monte_carlo_config.crossover_rate),
            'temperature_start': tk.DoubleVar(value=self.monte_carlo_config.temperature_start),
            'temperature_end': tk.DoubleVar(value=self.monte_carlo_config.temperature_end),
            'cooling_rate': tk.DoubleVar(value=self.monte_carlo_config.cooling_rate),
            'elite_ratio': tk.DoubleVar(value=self.monte_carlo_config.elite_ratio)
        }
        
        param_labels = {
            'max_iterations': '最大迭代次数',
            'population_size': '种群大小',
            'mutation_rate': '变异率',
            'crossover_rate': '交叉率',
            'temperature_start': '起始温度',
            'temperature_end': '结束温度',
            'cooling_rate': '冷却速率',
            'elite_ratio': '精英比例'
        }
        
        row = 0
        for param, label in param_labels.items():
            ttk.Label(mc_frame, text=label + ":").grid(row=row, column=0, sticky=tk.W, pady=2)
            
            if param in ['max_iterations', 'population_size']:
                ttk.Spinbox(mc_frame, from_=10, to=1000, textvariable=self.algo_vars[param], 
                           width=15).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            else:
                ttk.Scale(mc_frame, from_=0.0, to=1.0, variable=self.algo_vars[param], 
                         orient=tk.HORIZONTAL, length=200).grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
                ttk.Label(mc_frame, textvariable=self.algo_vars[param]).grid(row=row, column=2, pady=2)
            
            row += 1
        
        mc_frame.columnconfigure(1, weight=1)
        
        # 高级选项
        advanced_frame = ttk.LabelFrame(frame, text="高级选项", padding="10")
        advanced_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.enable_parallel_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="启用并行计算", 
                       variable=self.enable_parallel_var).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(advanced_frame, text="线程数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.num_threads_var = tk.IntVar(value=4)
        ttk.Spinbox(advanced_frame, from_=1, to=8, textvariable=self.num_threads_var, 
                   width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
    
    def _create_evaluation_config_tab(self, parent: ttk.Notebook) -> None:
        """创建评估配置标签页"""
        frame = ttk.Frame(parent, padding="10")
        parent.add(frame, text="评估权重")
        
        # 权重配置
        weight_frame = ttk.LabelFrame(frame, text="评估维度权重", padding="10")
        weight_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 创建权重变量
        self.weight_vars = {
            'space_efficiency': tk.DoubleVar(value=self.evaluation_config.space_efficiency_weight),
            'lighting': tk.DoubleVar(value=self.evaluation_config.lighting_weight),
            'ventilation': tk.DoubleVar(value=self.evaluation_config.ventilation_weight),
            'circulation': tk.DoubleVar(value=self.evaluation_config.circulation_weight),
            'comfort': tk.DoubleVar(value=self.evaluation_config.comfort_weight)
        }
        
        weight_labels = {
            'space_efficiency': '空间效率',
            'lighting': '采光效果',
            'ventilation': '通风效果',
            'circulation': '动线效率',
            'comfort': '舒适度'
        }
        
        row = 0
        for weight, label in weight_labels.items():
            ttk.Label(weight_frame, text=label + ":").grid(row=row, column=0, sticky=tk.W, pady=5)
            
            # 滑块
            scale = ttk.Scale(weight_frame, from_=0.0, to=1.0, variable=self.weight_vars[weight], 
                           orient=tk.HORIZONTAL, length=200)
            scale.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
            
            # 数值显示
            ttk.Label(weight_frame, textvariable=self.weight_vars[weight]).grid(row=row, column=2, pady=5)
            
            # 归一化按钮
            ttk.Button(weight_frame, text="归一化", 
                      command=lambda w=weight: self._normalize_weights(w)).grid(row=row, column=3, padx=5, pady=5)
            
            row += 1
        
        weight_frame.columnconfigure(1, weight=1)
        
        # 总权重显示
        total_weight_label = ttk.Label(frame, text="总权重: 0.00", font=('Arial', 10, 'bold'))
        total_weight_label.grid(row=1, column=0, sticky=tk.W, pady=10)
        
        self.total_weight_label = total_weight_label
        
        # 绑定权重变化事件
        for var in self.weight_vars.values():
            var.trace('w', self._update_total_weight)
        
        # 初始化总权重显示
        self._update_total_weight()
    
    def _create_preset_config_tab(self, parent: ttk.Notebook) -> None:
        """创建预设配置标签页"""
        frame = ttk.Frame(parent, padding="10")
        parent.add(frame, text="预设配置")
        
        # 预设选择
        preset_frame = ttk.LabelFrame(frame, text="选择预设", padding="10")
        preset_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(preset_frame, text="选择预设配置:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, 
                                   values=list(self.presets.keys()), width=20, state="readonly")
        preset_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(preset_frame, text="应用预设", 
                  command=self._apply_preset).grid(row=0, column=2, padx=5, pady=5)
        
        preset_frame.columnconfigure(1, weight=1)
        
        # 预设详情显示
        details_frame = ttk.LabelFrame(frame, text="预设详情", padding="10")
        details_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.preset_details_text = tk.Text(details_frame, height=15, width=60, wrap=tk.WORD)
        details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.preset_details_text.yview)
        self.preset_details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.preset_details_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        
        # 绑定预设选择事件
        self.preset_var.trace('w', self._update_preset_details)
        
        # 配置管理
        config_frame = ttk.LabelFrame(frame, text="配置管理", padding="10")
        config_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(config_frame, text="保存配置", 
                  command=self._save_config).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(config_frame, text="加载配置", 
                  command=self._load_config).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text="重置默认", 
                  command=self._reset_to_default).grid(row=0, column=2, padx=5, pady=5)
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
    
    def _create_button_area(self, parent: ttk.Frame) -> None:
        """创建按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="开始优化", 
                  command=self._start_optimization).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="保存预设", 
                  command=self._save_as_preset).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", 
                  command=self._cancel).pack(side=tk.RIGHT, padx=5)
        
        button_frame.columnconfigure(0, weight=1)
    
    def _normalize_weights(self, changed_weight: str) -> None:
        """归一化权重"""
        total = sum(var.get() for var in self.weight_vars.values())
        if total > 0:
            for name, var in self.weight_vars.items():
                current = var.get()
                if name == changed_weight and current > 0:
                    # 保持当前权重，调整其他权重
                    ratio = (total - current) / (total - self.weight_vars[changed_weight].get())
                    for other_name, other_var in self.weight_vars.items():
                        if other_name != changed_weight:
                            other_var.set(other_var.get() * ratio)
                    break
    
    def _update_total_weight(self, *args) -> None:
        """更新总权重显示"""
        total = sum(var.get() for var in self.weight_vars.values())
        if self.total_weight_label:
            self.total_weight_label.config(text=f"总权重: {total:.2f}")
    
    def _apply_preset(self) -> None:
        """应用预设配置"""
        preset_name = self.preset_var.get()
        if preset_name not in self.presets:
            messagebox.showwarning("警告", "请选择一个有效的预设配置")
            return
        
        preset = self.presets[preset_name]
        
        # 应用基础配置
        self.width_var.set(preset['layout']['total_width'])
        self.height_var.set(preset['layout']['total_height'])
        
        # 应用房间配置
        for room_type, count in preset['layout']['room_requirements'].items():
            if room_type in self.room_vars:
                self.room_vars[room_type].set(count)
        
        # 应用算法配置
        for param, value in preset['algorithm'].items():
            if param in self.algo_vars:
                self.algo_vars[param].set(value)
        
        # 应用评估配置
        for weight, value in preset['evaluation'].items():
            if weight in self.weight_vars:
                self.weight_vars[weight].set(value)
        
        messagebox.showinfo("成功", f"已应用预设配置: {preset_name}")
    
    def _update_preset_details(self, *args) -> None:
        """更新预设详情显示"""
        preset_name = self.preset_var.get()
        if preset_name not in self.presets:
            return
        
        preset = self.presets[preset_name]
        
        details = f"预设名称: {preset_name}\n\n"
        details += "基础配置:\n"
        details += f"  总尺寸: {preset['layout']['total_width']} x {preset['layout']['total_height']} 米\n\n"
        
        details += "房间配置:\n"
        room_names = {
            'living_room': '客厅',
            'bedroom': '卧室',
            'kitchen': '厨房',
            'bathroom': '卫生间',
            'dining_room': '餐厅',
            'study': '书房',
            'balcony': '阳台',
            'storage': '储物间'
        }
        
        for room_type, count in preset['layout']['room_requirements'].items():
            if count > 0:
                room_name = room_names.get(room_type, room_type)
                details += f"  {room_name}: {count} 个\n"
        
        details += "\n算法配置:\n"
        details += f"  迭代次数: {preset['algorithm']['max_iterations']}\n"
        details += f"  种群大小: {preset['algorithm']['population_size']}\n"
        
        self.preset_details_text.delete(1.0, tk.END)
        self.preset_details_text.insert(1.0, details)
    
    def _start_optimization(self) -> None:
        """开始优化"""
        # 收集参数
        params = self._collect_parameters()
        
        # 验证参数
        if not self._validate_parameters(params):
            return
        
        # 关闭窗口
        self._close_window()
        
        # 调用回调函数
        if self.on_start_optimization:
            self.on_start_optimization(params)
    
    def _collect_parameters(self) -> Dict[str, Any]:
        """收集所有参数"""
        return {
            'layout': {
                'total_width': self.width_var.get(),
                'total_height': self.height_var.get(),
                'wall_thickness': self.wall_var.get(),
                'room_requirements': {k: v.get() for k, v in self.room_vars.items()},
                'min_room_area': {k: v.get() for k, v in self.min_area_vars.items()},
                'max_room_area': {k: v.get() for k, v in self.max_area_vars.items()}
            },
            'algorithm': {
                'max_iterations': self.algo_vars['max_iterations'].get(),
                'population_size': self.algo_vars['population_size'].get(),
                'mutation_rate': self.algo_vars['mutation_rate'].get(),
                'crossover_rate': self.algo_vars['crossover_rate'].get(),
                'temperature_start': self.algo_vars['temperature_start'].get(),
                'temperature_end': self.algo_vars['temperature_end'].get(),
                'cooling_rate': self.algo_vars['cooling_rate'].get(),
                'elite_ratio': self.algo_vars['elite_ratio'].get()
            },
            'evaluation': {
                'space_efficiency_weight': self.weight_vars['space_efficiency'].get(),
                'lighting_weight': self.weight_vars['lighting'].get(),
                'ventilation_weight': self.weight_vars['ventilation'].get(),
                'circulation_weight': self.weight_vars['circulation'].get(),
                'comfort_weight': self.weight_vars['comfort'].get()
            },
            'parallel': {
                'enabled': self.enable_parallel_var.get(),
                'num_threads': self.num_threads_var.get()
            }
        }
    
    def _validate_parameters(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        # 检查是否有至少一个房间
        room_count = sum(params['layout']['room_requirements'].values())
        if room_count == 0:
            messagebox.showerror("错误", "请至少配置一个房间")
            return False
        
        # 检查面积约束
        for room_type in params['layout']['room_requirements']:
            if params['layout']['room_requirements'][room_type] > 0:
                min_area = params['layout']['min_room_area'][room_type]
                max_area = params['layout']['max_room_area'][room_type]
                if min_area >= max_area:
                    messagebox.showerror("错误", f"房间最小面积不能大于等于最大面积")
                    return False
        
        # 检查权重总和
        total_weight = sum(params['evaluation'].values())
        if abs(total_weight - 1.0) > 0.01:
            result = messagebox.askyesno("警告", 
                                       f"评估权重总和为 {total_weight:.2f}，不等于1.0。\n是否继续？")
            if not result:
                return False
        
        return True
    
    def _save_config(self) -> None:
        """保存配置到文件"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                params = self._collect_parameters()
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(params, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("成功", "配置已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def _load_config(self) -> None:
        """从文件加载配置"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    params = json.load(f)
                
                # 应用加载的配置
                self._apply_loaded_params(params)
                messagebox.showinfo("成功", "配置已加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def _apply_loaded_params(self, params: Dict[str, Any]) -> None:
        """应用加载的参数"""
        # 应用基础配置
        if 'layout' in params:
            layout = params['layout']
            self.width_var.set(layout.get('total_width', 20.0))
            self.height_var.set(layout.get('total_height', 15.0))
            self.wall_var.set(layout.get('wall_thickness', 0.2))
            
            for room_type, count in layout.get('room_requirements', {}).items():
                if room_type in self.room_vars:
                    self.room_vars[room_type].set(count)
            
            for room_type, area in layout.get('min_room_area', {}).items():
                if room_type in self.min_area_vars:
                    self.min_area_vars[room_type].set(area)
            
            for room_type, area in layout.get('max_room_area', {}).items():
                if room_type in self.max_area_vars:
                    self.max_area_vars[room_type].set(area)
        
        # 应用算法配置
        if 'algorithm' in params:
            algorithm = params['algorithm']
            for param, value in algorithm.items():
                if param in self.algo_vars:
                    self.algo_vars[param].set(value)
        
        # 应用评估配置
        if 'evaluation' in params:
            evaluation = params['evaluation']
            for weight, value in evaluation.items():
                weight_key = weight.replace('_weight', '')
                if weight_key in self.weight_vars:
                    self.weight_vars[weight_key].set(value)
        
        # 应用并行配置
        if 'parallel' in params:
            parallel = params['parallel']
            self.enable_parallel_var.set(parallel.get('enabled', False))
            self.num_threads_var.set(parallel.get('num_threads', 4))
    
    def _reset_to_default(self) -> None:
        """重置为默认值"""
        result = messagebox.askyesno("确认", "确定要重置所有参数为默认值吗？")
        if result:
            # 重新创建参数对象
            self.layout_params = LayoutParameters()
            self.monte_carlo_config = MonteCarloConfig()
            self.evaluation_config = EvaluationConfig()
            
            # 重新初始化界面
            self.window.destroy()
            self.window = None
            self.show()
    
    def _save_as_preset(self) -> None:
        """保存为预设"""
        name = tk.simpledialog.askstring("保存预设", "请输入预设名称:")
        if name:
            params = self._collect_parameters()
            self.presets[name] = params
            messagebox.showinfo("成功", f"预设 '{name}' 已保存")
    
    def _cancel(self) -> None:
        """取消配置"""
        self._close_window()
    
    def _close_window(self) -> None:
        """关闭窗口"""
        if self.window:
            self.window.destroy()
            self.window = None
    
    def _on_window_close(self) -> None:
        """窗口关闭事件"""
        self._close_window()
    
    # 预设配置方法
    def _create_small_apartment_preset(self) -> Dict[str, Any]:
        """创建小户型公寓预设"""
        return {
            'layout': {
                'total_width': 15.0,
                'total_height': 12.0,
                'wall_thickness': 0.15,
                'room_requirements': {
                    'living_room': 1,
                    'bedroom': 1,
                    'kitchen': 1,
                    'bathroom': 1,
                    'dining_room': 0,
                    'study': 0,
                    'balcony': 1,
                    'storage': 0
                }
            },
            'algorithm': {
                'max_iterations': 500,
                'population_size': 30,
                'mutation_rate': 0.4,
                'crossover_rate': 0.6
            },
            'evaluation': {
                'space_efficiency_weight': 0.35,
                'lighting_weight': 0.25,
                'ventilation_weight': 0.15,
                'circulation_weight': 0.15,
                'comfort_weight': 0.10
            }
        }
    
    def _create_standard_house_preset(self) -> Dict[str, Any]:
        """创建标准住宅预设"""
        return {
            'layout': {
                'total_width': 20.0,
                'total_height': 15.0,
                'wall_thickness': 0.2,
                'room_requirements': {
                    'living_room': 1,
                    'bedroom': 2,
                    'kitchen': 1,
                    'bathroom': 1,
                    'dining_room': 1,
                    'study': 0,
                    'balcony': 1,
                    'storage': 0
                }
            },
            'algorithm': {
                'max_iterations': 1000,
                'population_size': 50,
                'mutation_rate': 0.3,
                'crossover_rate': 0.7
            },
            'evaluation': {
                'space_efficiency_weight': 0.25,
                'lighting_weight': 0.20,
                'ventilation_weight': 0.15,
                'circulation_weight': 0.20,
                'comfort_weight': 0.20
            }
        }
    
    def _create_large_house_preset(self) -> Dict[str, Any]:
        """创建大户型预设"""
        return {
            'layout': {
                'total_width': 25.0,
                'total_height': 20.0,
                'wall_thickness': 0.25,
                'room_requirements': {
                    'living_room': 1,
                    'bedroom': 3,
                    'kitchen': 1,
                    'bathroom': 2,
                    'dining_room': 1,
                    'study': 1,
                    'balcony': 2,
                    'storage': 1
                }
            },
            'algorithm': {
                'max_iterations': 1500,
                'population_size': 60,
                'mutation_rate': 0.25,
                'crossover_rate': 0.75
            },
            'evaluation': {
                'space_efficiency_weight': 0.20,
                'lighting_weight': 0.25,
                'ventilation_weight': 0.20,
                'circulation_weight': 0.20,
                'comfort_weight': 0.15
            }
        }
    
    def _create_luxury_villa_preset(self) -> Dict[str, Any]:
        """创建豪华别墅预设"""
        return {
            'layout': {
                'total_width': 30.0,
                'total_height': 25.0,
                'wall_thickness': 0.3,
                'room_requirements': {
                    'living_room': 2,
                    'bedroom': 4,
                    'kitchen': 1,
                    'bathroom': 3,
                    'dining_room': 1,
                    'study': 2,
                    'balcony': 3,
                    'storage': 2
                }
            },
            'algorithm': {
                'max_iterations': 2000,
                'population_size': 80,
                'mutation_rate': 0.2,
                'crossover_rate': 0.8
            },
            'evaluation': {
                'space_efficiency_weight': 0.15,
                'lighting_weight': 0.25,
                'ventilation_weight': 0.20,
                'circulation_weight': 0.25,
                'comfort_weight': 0.15
            }
        }


if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    config_window = ParameterConfigWindow(root)
    config_window.show()
    
    root.mainloop()