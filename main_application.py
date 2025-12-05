"""
主应用程序框架
将所有功能模块整合成完整的桌面应用
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
import queue

# 导入自定义模块
from core_data_structures import Layout, RoomType, Rectangle
from monte_carlo_engine import MonteCarloOptimizer, MonteCarloConfig, ParallelMonteCarloOptimizer
from evaluation_system import MultiDimensionalEvaluator, EvaluationConfig
from visualization_engine import LayoutRenderer, InteractiveVisualization
from config_interface import ParameterConfigWindow
from export_system import ExportManager, ExportConfig


class StatusBar(ttk.Frame):
    """状态栏"""
    
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.parent = parent
        
        # 创建状态标签
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        # 创建进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, 
                                           length=200, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # 创建时间标签
        self.time_var = tk.StringVar()
        self.time_label = ttk.Label(self, textvariable=self.time_var, relief=tk.SUNKEN, width=20)
        self.time_label.pack(side=tk.RIGHT, padx=2, pady=2)
        
        # 更新时间
        self.update_time()
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_var.set(current_time)
        self.parent.after(1000, self.update_time)
    
    def set_status(self, message: str):
        """设置状态消息"""
        self.status_var.set(message)
    
    def set_progress(self, value: float):
        """设置进度条"""
        self.progress_var.set(value)
    
    def start_progress(self):
        """开始进度动画"""
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
    
    def stop_progress(self):
        """停止进度动画"""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_var.set(0)


class ResultWindow:
    """结果显示窗口"""
    
    def __init__(self, parent: tk.Tk, layout: Layout, evaluation_results: Dict):
        self.parent = parent
        self.layout = layout
        self.evaluation_results = evaluation_results
        self.window = None
        
        # 导出管理器
        self.export_manager = ExportManager()
        
        # 交互式可视化
        self.visualization = None
    
    def show(self):
        """显示结果窗口"""
        if self.window:
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("优化结果")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 创建左右分栏
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        # 左侧：可视化区域
        self._create_visualization_area(left_frame)
        
        # 右侧：信息和控制区域
        self._create_info_area(right_frame)
        
        # 底部：按钮区域
        self._create_button_area(main_frame)
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # 显示布局
        self._display_layout()
    
    def _create_visualization_area(self, parent: ttk.Frame):
        """创建可视化区域"""
        # 可视化标签
        viz_label = ttk.Label(parent, text="平面图预览", font=('Arial', 12, 'bold'))
        viz_label.pack(pady=(0, 5))
        
        # 创建交互式可视化
        self.visualization = InteractiveVisualization()
        self.canvas = self.visualization.setup_interactive_canvas(parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_info_area(self, parent: ttk.Frame):
        """创建信息区域"""
        # 信息标签
        info_label = ttk.Label(parent, text="评估结果", font=('Arial', 12, 'bold'))
        info_label.pack(pady=(0, 10))
        
        # 创建滚动文本框显示评估报告
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.info_text = tk.Text(text_frame, wrap=tk.WORD, height=15, 
                                yscrollcommand=scrollbar.set)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.info_text.yview)
        
        # 显示评估结果
        self._display_evaluation_results()
    
    def _create_button_area(self, parent: ttk.Frame):
        """创建按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 导出按钮
        ttk.Button(button_frame, text="导出PNG", 
                  command=lambda: self._export_layout('PNG')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出SVG", 
                  command=lambda: self._export_layout('SVG')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出DXF", 
                  command=lambda: self._export_layout('DXF')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出PDF", 
                  command=lambda: self._export_layout('PDF')).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出数据", 
                  command=lambda: self._export_layout('JSON')).pack(side=tk.LEFT, padx=5)
        
        # 其他按钮
        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Button(button_frame, text="保存结果", 
                  command=self._save_result).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", 
                  command=self._on_window_close).pack(side=tk.RIGHT, padx=5)
    
    def _display_layout(self):
        """显示布局"""
        if self.visualization and self.layout:
            self.visualization.update_layout(self.layout, True, self.evaluation_results)
    
    def _display_evaluation_results(self):
        """显示评估结果"""
        evaluator = MultiDimensionalEvaluator()
        report = evaluator.get_detailed_report(self.layout)
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, report)
        
        # 添加布局统计信息
        stats_text = "\n=== 布局统计 ===\n\n"
        stats_text += f"总面积: {self.layout.total_area:.1f}m²\n"
        stats_text += f"房间数量: {len(self.layout.rooms)}\n"
        stats_text += f"空间利用率: {self.layout.utilization_rate:.2%}\n"
        
        # 统计各类型房间
        room_counts = {}
        for room in self.layout.rooms:
            room_type = room.room_type.value
            room_counts[room_type] = room_counts.get(room_type, 0) + 1
        
        stats_text += "\n房间分布:\n"
        for room_type, count in room_counts.items():
            stats_text += f"  {room_type}: {count}个\n"
        
        self.info_text.insert(tk.END, stats_text)
    
    def _export_layout(self, format_type: str):
        """导出布局"""
        filename = filedialog.asksaveasfilename(
            defaultextension=f".{format_type.lower()}",
            filetypes=[(f"{format_type} files", f"*.{format_type.lower()}"), 
                     ("All files", "*.*")]
        )
        
        if filename:
            try:
                success = self.export_manager.export(
                    self.layout, filename, format_type, self.evaluation_results
                )
                
                if success:
                    messagebox.showinfo("成功", f"布局已导出为 {format_type} 格式")
                else:
                    messagebox.showerror("错误", f"{format_type} 导出失败")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def _save_result(self):
        """保存完整结果"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # 创建结果数据
                result_data = {
                    'metadata': {
                        'save_time': datetime.now().isoformat(),
                        'layout_info': {
                            'total_area': self.layout.total_area,
                            'room_count': len(self.layout.rooms),
                            'utilization_rate': self.layout.utilization_rate
                        }
                    },
                    'evaluation_results': self.evaluation_results,
                    'layout_data': self._serialize_layout()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("成功", "结果已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def _serialize_layout(self) -> Dict:
        """序列化布局数据"""
        return {
            'bounds': {
                'x': self.layout.bounds.x,
                'y': self.layout.bounds.y,
                'width': self.layout.bounds.width,
                'height': self.layout.bounds.height
            },
            'rooms': [
                {
                    'type': room.room_type.value,
                    'bounds': {
                        'x': room.bounds.x,
                        'y': room.bounds.y,
                        'width': room.bounds.width,
                        'height': room.bounds.height
                    },
                    'area': room.area
                }
                for room in self.layout.rooms
            ]
        }
    
    def _on_window_close(self):
        """窗口关闭事件"""
        if self.window:
            self.window.destroy()
    
    def _close_window(self):
        """关闭结果窗口（兼容主应用调用）"""
        self._on_window_close()


class MainApplication:
    """主应用程序"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("蒙特卡洛住宅自动化生成及优化系统")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        
        # 应用程序状态
        self.current_layout = None
        self.current_evaluation = None
        self.optimization_thread = None
        self.result_window = None
        
        # 组件实例
        self.config_window = None
        self.status_bar = None
        
        # 参数队列（线程间通信）
        self.parameter_queue = queue.Queue()
        
        # 初始化界面
        self._setup_ui()
        self._setup_menu()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 创建欢迎区域
        self._create_welcome_area(main_frame)
        
        # 创建快捷操作区域
        self._create_quick_actions(main_frame)
        
        # 创建状态栏
        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def _create_welcome_area(self, parent: ttk.Frame):
        """创建欢迎区域"""
        welcome_frame = ttk.LabelFrame(parent, text="欢迎使用", padding="20")
        welcome_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 欢迎标题
        title_label = ttk.Label(welcome_frame, 
                               text="蒙特卡洛住宅自动化生成及优化系统",
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 功能介绍
        intro_text = """本系统基于蒙特卡洛算法，为您提供智能化的住宅平面图生成和优化服务。

主要功能：
• 自动生成住宅平面图布局
• 多维度评估优化（空间效率、采光、通风、动线、舒适度）
• 实时可视化预览和交互操作
• 多格式结果导出（PNG、SVG、DXF、PDF等）
• 参数化配置和预设方案

使用流程：
1. 点击"参数配置"设置生成参数
2. 点击"开始生成"进行布局生成和优化
3. 在结果窗口中查看和导出优化结果"""
        
        intro_label = ttk.Label(welcome_frame, text=intro_text, justify=tk.LEFT)
        intro_label.pack(pady=(0, 20))
        
        # 快速开始按钮
        start_frame = ttk.Frame(welcome_frame)
        start_frame.pack()
        
        ttk.Button(start_frame, text="快速开始（小户型）", 
                  command=self._quick_start_small).pack(side=tk.LEFT, padx=5)
        ttk.Button(start_frame, text="快速开始（标准户型）", 
                  command=self._quick_start_standard).pack(side=tk.LEFT, padx=5)
        ttk.Button(start_frame, text="快速开始（大户型）", 
                  command=self._quick_start_large).pack(side=tk.LEFT, padx=5)
    
    def _create_quick_actions(self, parent: ttk.Frame):
        """创建快捷操作区域"""
        actions_frame = ttk.LabelFrame(parent, text="操作面板", padding="20")
        actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 主要操作按钮
        button_frame1 = ttk.Frame(actions_frame)
        button_frame1.pack(pady=(0, 10))
        
        ttk.Button(button_frame1, text="参数配置", 
                  command=self._show_config_window,
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame1, text="开始生成", 
                  command=self._start_optimization,
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame1, text="加载结果", 
                  command=self._load_result,
                  width=20).pack(side=tk.LEFT, padx=5)
        
        # 次要操作按钮
        button_frame2 = ttk.Frame(actions_frame)
        button_frame2.pack(pady=(0, 10))
        
        ttk.Button(button_frame2, text="批量处理", 
                  command=self._batch_process,
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="预设管理", 
                  command=self._manage_presets,
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame2, text="帮助文档", 
                  command=self._show_help,
                  width=20).pack(side=tk.LEFT, padx=5)
        
        # 最近使用区域
        recent_frame = ttk.LabelFrame(actions_frame, text="最近使用", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True)
        
        self.recent_listbox = tk.Listbox(recent_frame, height=5)
        self.recent_listbox.pack(fill=tk.BOTH, expand=True)
        
        # 绑定双击事件
        self.recent_listbox.bind('<Double-Button-1>', self._on_recent_double_click)
    
    def _setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建项目", command=self._new_project)
        file_menu.add_command(label="打开项目", command=self._open_project)
        file_menu.add_command(label="保存项目", command=self._save_project)
        file_menu.add_separator()
        file_menu.add_command(label="加载布局", command=self._load_result)
        file_menu.add_command(label="导出结果", command=self._export_current_result)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)
        
        # 生成菜单
        generate_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="生成", menu=generate_menu)
        generate_menu.add_command(label="参数配置", command=self._show_config_window)
        generate_menu.add_command(label="开始生成", command=self._start_optimization)
        generate_menu.add_separator()
        generate_menu.add_command(label="小户型预设", command=self._quick_start_small)
        generate_menu.add_command(label="标准户型预设", command=self._quick_start_standard)
        generate_menu.add_command(label="大户型预设", command=self._quick_start_large)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="显示结果", command=self._show_result_window)
        view_menu.add_command(label="查看评估报告", command=self._show_evaluation_report)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="批量处理", command=self._batch_process)
        tools_menu.add_command(label="预设管理", command=self._manage_presets)
        tools_menu.add_command(label="性能监控", command=self._show_performance_monitor)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _show_config_window(self):
        """显示配置窗口"""
        if not self.config_window:
            self.config_window = ParameterConfigWindow(self.root)
            self.config_window.on_start_optimization = self._on_parameters_configured
        self.config_window.show()
    
    def _on_parameters_configured(self, params: Dict[str, Any]):
        """参数配置完成回调"""
        # 将参数放入队列，等待优化线程使用
        self.parameter_queue.put(params)
        
        # 显示配置窗口隐藏，开始优化
        if self.config_window:
            self.config_window._close_window()
        
        # 启动优化过程
        self._start_optimization_with_params(params)
    
    def _start_optimization(self):
        """开始优化（使用当前配置）"""
        # 首先显示配置窗口
        self._show_config_window()
    
    def _start_optimization_with_params(self, params: Dict[str, Any]):
        """使用指定参数开始优化"""
        if self.optimization_thread and self.optimization_thread.is_alive():
            messagebox.showwarning("警告", "优化正在进行中，请等待完成")
            return
        
        # 启动优化线程
        self.optimization_thread = threading.Thread(
            target=self._optimization_worker,
            args=(params,),
            daemon=True
        )
        self.optimization_thread.start()
        
        # 更新状态
        self.status_bar.set_status("正在优化中...")
        self.status_bar.start_progress()
    
    def _optimization_worker(self, params: Dict[str, Any]):
        """优化工作线程"""
        try:
            # 解析参数
            layout_params = params['layout']
            algo_params = params['algorithm']
            eval_params = params['evaluation']
            parallel_params = params['parallel']
            
            # 创建配置对象
            layout_bounds = Rectangle(0, 0, 
                                    layout_params['total_width'], 
                                    layout_params['total_height'])
            
            monte_carlo_config = MonteCarloConfig(
                max_iterations=algo_params['max_iterations'],
                population_size=algo_params['population_size'],
                mutation_rate=algo_params['mutation_rate'],
                crossover_rate=algo_params['crossover_rate'],
                temperature_start=algo_params['temperature_start'],
                temperature_end=algo_params['temperature_end'],
                cooling_rate=algo_params['cooling_rate'],
                elite_ratio=algo_params['elite_ratio']
            )
            
            evaluation_config = EvaluationConfig(
                space_efficiency_weight=eval_params['space_efficiency_weight'],
                lighting_weight=eval_params['lighting_weight'],
                ventilation_weight=eval_params['ventilation_weight'],
                circulation_weight=eval_params['circulation_weight'],
                comfort_weight=eval_params['comfort_weight']
            )
            
            # 创建房间需求字典
            room_requirements = {}
            for room_type_str, count in layout_params['room_requirements'].items():
                if count > 0:
                    room_type = RoomType(room_type_str)
                    room_requirements[room_type] = count
            
            # 创建评估器和约束
            evaluator = MultiDimensionalEvaluator(evaluation_config)
            from core_data_structures import LayoutConstraints
            constraints = LayoutConstraints()
            
            # 创建优化器
            if parallel_params['enabled']:
                optimizer = ParallelMonteCarloOptimizer(
                    monte_carlo_config, 
                    evaluator.evaluate,
                    parallel_params['num_threads'],
                    constraints
                )
            else:
                optimizer = MonteCarloOptimizer(
                    monte_carlo_config,
                    evaluator.evaluate,
                    constraints
                )
            
            # 执行优化
            best_layout = optimizer.optimize(layout_bounds, room_requirements, room_requirements)
            
            # 评估最佳布局
            evaluation_results = evaluator.evaluate(best_layout)
            
            # 更新UI（在主线程中）
            self.root.after(0, self._on_optimization_complete, best_layout, evaluation_results)
            
        except Exception as e:
            # 错误处理
            self.root.after(0, self._on_optimization_error, str(e))
    
    def _on_optimization_complete(self, layout: Layout, evaluation_results: Dict):
        """优化完成回调"""
        self.current_layout = layout
        self.current_evaluation = evaluation_results
        
        # 更新状态
        self.status_bar.set_status("优化完成")
        self.status_bar.stop_progress()
        
        # 显示结果
        self._show_result_window()
        
        # 添加到最近使用
        timestamp = datetime.now().strftime("%H:%M:%S")
        total_score = evaluation_results.get('total', {}).get('weighted_score', 0)
        recent_item = f"{timestamp} - 得分: {total_score:.2f}"
        
        self.recent_listbox.insert(0, recent_item)
        # 限制最近项目数量
        if self.recent_listbox.size() > 10:
            self.recent_listbox.delete(10, tk.END)
        
        messagebox.showinfo("成功", f"优化完成！\n总得分: {total_score:.2f}")
    
    def _on_optimization_error(self, error_message: str):
        """优化错误回调"""
        self.status_bar.set_status("优化失败")
        self.status_bar.stop_progress()
        
        messagebox.showerror("错误", f"优化过程中发生错误:\n{error_message}")
    
    def _show_result_window(self):
        """显示结果窗口"""
        if not self.current_layout:
            messagebox.showwarning("警告", "没有可显示的结果")
            return
        
        if self.result_window:
            self.result_window._close_window()
        
        self.result_window = ResultWindow(self.root, self.current_layout, self.current_evaluation)
        self.result_window.show()
    
    def _quick_start_small(self):
        """快速开始（小户型）"""
        params = self._get_small_apartment_params()
        self._start_optimization_with_params(params)
    
    def _quick_start_standard(self):
        """快速开始（标准户型）"""
        params = self._get_standard_house_params()
        self._start_optimization_with_params(params)
    
    def _quick_start_large(self):
        """快速开始（大户型）"""
        params = self._get_large_house_params()
        self._start_optimization_with_params(params)
    
    def _get_small_apartment_params(self) -> Dict[str, Any]:
        """获取小户型参数"""
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
                'crossover_rate': 0.6,
                'temperature_start': 100.0,
                'temperature_end': 0.01,
                'cooling_rate': 0.995,
                'elite_ratio': 0.2
            },
            'evaluation': {
                'space_efficiency_weight': 0.35,
                'lighting_weight': 0.25,
                'ventilation_weight': 0.15,
                'circulation_weight': 0.15,
                'comfort_weight': 0.10
            },
            'parallel': {
                'enabled': False,
                'num_threads': 4
            }
        }
    
    def _get_standard_house_params(self) -> Dict[str, Any]:
        """获取标准户型参数"""
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
                'crossover_rate': 0.7,
                'temperature_start': 100.0,
                'temperature_end': 0.01,
                'cooling_rate': 0.995,
                'elite_ratio': 0.2
            },
            'evaluation': {
                'space_efficiency_weight': 0.25,
                'lighting_weight': 0.20,
                'ventilation_weight': 0.15,
                'circulation_weight': 0.20,
                'comfort_weight': 0.20
            },
            'parallel': {
                'enabled': False,
                'num_threads': 4
            }
        }
    
    def _get_large_house_params(self) -> Dict[str, Any]:
        """获取大户型参数"""
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
                'crossover_rate': 0.75,
                'temperature_start': 100.0,
                'temperature_end': 0.01,
                'cooling_rate': 0.995,
                'elite_ratio': 0.2
            },
            'evaluation': {
                'space_efficiency_weight': 0.20,
                'lighting_weight': 0.25,
                'ventilation_weight': 0.20,
                'circulation_weight': 0.20,
                'comfort_weight': 0.15
            },
            'parallel': {
                'enabled': True,
                'num_threads': 4
            }
        }
    
    # 其他方法实现（占位符）
    def _load_result(self):
        """加载结果"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            messagebox.showinfo("提示", "结果加载功能待实现")
    
    def _export_current_result(self):
        """导出当前结果"""
        if not self.current_layout:
            messagebox.showwarning("警告", "没有可导出的结果")
            return
        
        if self.result_window:
            self.result_window._close_window()
        
        self.result_window = ResultWindow(self.root, self.current_layout, self.current_evaluation)
        self.result_window.show()
    
    def _show_evaluation_report(self):
        """显示评估报告"""
        if not self.current_evaluation:
            messagebox.showwarning("警告", "没有可显示的评估报告")
            return
        
        # 创建报告窗口
        report_window = tk.Toplevel(self.root)
        report_window.title("评估报告")
        report_window.geometry("600x400")
        
        text_widget = tk.Text(report_window, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(report_window, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        evaluator = MultiDimensionalEvaluator()
        report = evaluator.get_detailed_report(self.current_layout)
        text_widget.insert(1.0, report)
        text_widget.config(state=tk.DISABLED)
    
    def _batch_process(self):
        """批量处理"""
        messagebox.showinfo("提示", "批量处理功能待实现")
    
    def _manage_presets(self):
        """管理预设"""
        messagebox.showinfo("提示", "预设管理功能待实现")
    
    def _show_performance_monitor(self):
        """显示性能监控"""
        messagebox.showinfo("提示", "性能监控功能待实现")
    
    def _show_help(self):
        """显示帮助"""
        help_text = """蒙特卡洛住宅自动化生成及优化系统

使用说明：
1. 点击"参数配置"设置生成参数
2. 选择房间类型和数量，调整优化权重
3. 点击"开始生成"进行布局生成和优化
4. 在结果窗口中查看优化结果
5. 使用导出功能保存结果

技术特点：
• 基于蒙特卡洛算法的智能布局生成
• 多维度评估体系
• 实时可视化预览
• 多格式结果导出

如有问题，请联系技术支持。"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("500x400")
        
        text_widget = tk.Text(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(1.0, help_text)
        text_widget.config(state=tk.DISABLED)
    
    def _show_about(self):
        """显示关于"""
        about_text = """蒙特卡洛住宅自动化生成及优化系统

版本：1.0.0
开发时间：2024年

本系统采用先进的蒙特卡洛算法，
为您提供智能化的住宅布局设计和优化服务。

主要功能：
• 自动化布局生成
• 多维度优化评估  
• 实时可视化
• 多格式导出

技术栈：
• Python 3.9+
• Tkinter (GUI)
• Matplotlib (可视化)
• NumPy (数值计算)

版权所有 © 2024"""
        
        messagebox.showinfo("关于", about_text)
    
    def _new_project(self):
        """新建项目"""
        # 清除当前结果
        self.current_layout = None
        self.current_evaluation = None
        if self.result_window:
            self.result_window._close_window()
        self.status_bar.set_status("已新建项目")
    
    def _open_project(self):
        """打开项目"""
        messagebox.showinfo("提示", "项目打开功能待实现")
    
    def _save_project(self):
        """保存项目"""
        messagebox.showinfo("提示", "项目保存功能待实现")
    
    def _on_recent_double_click(self, event):
        """最近项目双击事件"""
        messagebox.showinfo("提示", "最近项目加载功能待实现")
    
    def _on_closing(self):
        """应用程序关闭事件"""
        if self.optimization_thread and self.optimization_thread.is_alive():
            result = messagebox.askyesno("确认", "优化正在进行中，确定要退出吗？")
            if not result:
                return
        
        # 关闭所有子窗口
        if self.config_window:
            self.config_window._close_window()
        if self.result_window:
            self.result_window._close_window()
        
        # 退出应用程序
        self.root.destroy()
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_closing()


def main():
    """主函数"""
    app = MainApplication()
    app.run()


if __name__ == "__main__":
    main()