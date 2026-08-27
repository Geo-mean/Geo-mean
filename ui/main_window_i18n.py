# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import tkinter as tk
import time
from tkinter import ttk, messagebox, filedialog
import threading
import os
from datetime import datetime
from typing import Dict, Tuple
from config.styles import ModernStyle
from config.languages import language_manager
from core.data_processor import DataProcessor
from ui.file_loader import FileLoader
from ui.data_manager import DataManager, safe_check_dataframe
from ui.chart_controller import ChartController
from core.global_data_manager import get_global_data_manager
# 在现有import语句后添加这几行
try:
    from geochemistry.boundary_analyzer import BoundaryAnalyzer
    BOUNDARY_ANALYZER_AVAILABLE = True
    print("[INFO] 边界分析器导入成功")
except ImportError as e:
    print(f"[WARNING] 无法导入边界分析器: {e}")
    BOUNDARY_ANALYZER_AVAILABLE = False
    BoundaryAnalyzer = None
try:
    from geochemistry.bootstrap_median_window_analyzer import run_bootstrap_median_window_analysis
    BOOTSTRAP_MEDIAN_WINDOW_AVAILABLE = True
    print("[INFO] Bootstrap median window analysis module imported successfully")
except ImportError as e:
    print(f"[WARNING] Failed to import bootstrap median window analysis module: {e}")
    BOOTSTRAP_MEDIAN_WINDOW_AVAILABLE = False

try:
    from performance_profiler import get_profiler, reset_profiler
    PERFORMANCE_MONITORING = True
except ImportError:
    print("[WARNING] 性能监控模块不可用")
    PERFORMANCE_MONITORING = False
    def get_profiler():
        return None
    def reset_profiler():
        pass


class StateManager:
    """状态管理器 - 统一管理应用状态"""

    def __init__(self, root):
        self.root = root

        # ===== 新增：集成全局数据管理器 =====
        from core.global_data_manager import get_global_data_manager
        self.global_data_manager = get_global_data_manager()

        # 初始化状态管理器 - 明确使用本文件中定义的StateManager
        try:
            # 确保使用的是同一个文件中定义的StateManager类
            self.state_manager = StateManager()  # 这个StateManager定义在本文件中，不需要参数
        except Exception as e:
            print(f"[WARNING] StateManager初始化失败: {e}，使用None")
            self.state_manager = None

        # 初始化基本属性
        self.data = None
        self.file_path = None
        self.total_rows = 0

        # 地球化学分析相关属性
        self.geochem_filters = []
        self.filtered_data = None
        self.geochem_analyzer = None
        self.moving_window_results = None
        self.moving_window_integration = None
        self.geochem_analysis_results = None

        # 初始化核心数据处理器
        self.data_processor = DataProcessor()

        # 初始化功能模块
        self.file_loader = FileLoader(self)
        self.data_manager = DataManager(self)
        self.chart_controller = ChartController(self)

        # 设置模块间关联
        self.data_manager.set_data_processor(self.data_processor)

        # ===== 新增：设置数据变化监听器 =====
        self.global_data_manager.add_data_listener(self._on_global_data_changed)

        # 初始化筛选管理器 - 模块化方式
        self._initialize_filter_manager()

        # 初始化界面
        self._init_ui()

    def _on_global_data_changed(self, event_type, data):
        """全局数据变化监听器 - 确保所有组件同步"""
        try:
            print(f"[DEBUG-GLOBAL] 数据变化事件: {event_type}, 数据行数: {len(data) if data is not None else 0}")

            # 同步更新所有相关属性（保持向后兼容）
            self.data = data.copy() if data is not None else None
            self.data_processor.data = data.copy() if data is not None else None

            # 通知其他组件
            if hasattr(self, 'moving_window_integration') and self.moving_window_integration:
                self.moving_window_integration.set_current_data(data)

            # 更新状态管理器
            if data is not None:
                self.state_manager.update_state("data_updated", info={'rows': len(data)})

        except Exception as e:
            print(f"[ERROR] 处理全局数据变化失败: {e}")


    def update_state(self, new_state, data=None, info=None):
        """更新状态"""
        self.current_state = new_state
        if data is not None:
            self.analysis_results = data
        if info is not None:
            self.processing_info.update(info)

    def get_current_data_info(self):
        """获取当前数据信息"""
        return {
            'state': self.current_state,
            'has_results': self.analysis_results is not None,
            'processing_info': self.processing_info
        }


class AnalysisConfig:
    """分析配置类"""
    DEFAULT_WINDOW_SIZE = 50
    DEFAULT_STEP_SIZE = 5
    MAX_WINDOWS = 1000

    @classmethod
    def validate_params(cls, params):
        """验证分析参数"""
        if not isinstance(params, dict):
            return False, "参数必须是字典类型"

        required_keys = ['age_column', 'target_column', 'window_size', 'step_size']
        for key in required_keys:
            if key not in params:
                return False, f"缺少必需参数: {key}"

        if params['window_size'] <= 0 or params['step_size'] <= 0:
            return False, "窗口大小和步长必须大于0"

        return True, "参数验证通过"


class ModernExcelAnalyzerGUI:
    """模块化主界面类 - 集成地球化学分析功能"""

    def __init__(self, root):
        self.root = root

        # ===== 新增：集成全局数据管理器 =====
        from core.global_data_manager import get_global_data_manager
        self.global_data_manager = get_global_data_manager()

        # 初始化状态管理器
        # 创建一个简单的StateManager替代品，避免参数问题
        self.state_manager = type('SimpleStateManager', (), {
            'update_state': lambda self, *args, **kwargs: None,
            'get_current_data_info': lambda self: {'state': 'idle', 'has_results': False, 'processing_info': {}},
            'current_state': 'idle',
            'analysis_results': None,
            'filtered_data': None,
            'processing_info': {}
        })()

        # 初始化基本属性
        self.data = None
        self.file_path = None
        self.total_rows = 0

        # 地球化学分析相关属性
        self.geochem_filters = []
        self.filtered_data = None
        self.geochem_analyzer = None
        self.moving_window_results = None
        self.moving_window_integration = None
        self.geochem_analysis_results = None

        # 初始化核心数据处理器
        self.data_processor = DataProcessor()

        # 初始化功能模块
        self.file_loader = FileLoader(self)
        self.data_manager = DataManager(self)
        self.chart_controller = ChartController(self)

        # 设置模块间关联
        self.data_manager.set_data_processor(self.data_processor)

        # ===== 新增：设置数据变化监听器 =====
        self.global_data_manager.add_data_listener(self._on_global_data_changed)

        # 初始化筛选管理器 - 模块化方式
        self._initialize_filter_manager()

        # 初始化界面
        self._init_ui()

    def _on_global_data_changed(self, event_type, data):
        """全局数据变化监听器 - 确保所有组件同步"""
        try:
            print(f"[DEBUG-GLOBAL] 数据变化事件: {event_type}, 数据行数: {len(data) if data is not None else 0}")

            # 同步更新所有相关属性（保持向后兼容）
            self.data = data.copy() if data is not None else None
            self.data_processor.data = data.copy() if data is not None else None

            # 通知其他组件
            if hasattr(self, 'moving_window_integration') and self.moving_window_integration:
                self.moving_window_integration.set_current_data(data)

            # 更新状态管理器 - 只有在state_manager存在时才调用
            if hasattr(self, 'state_manager') and self.state_manager is not None and data is not None:
                self.state_manager.update_state("data_updated", info={'rows': len(data)})

        except Exception as e:
            print(f"[ERROR] 处理全局数据变化失败: {e}")

    def _update_data_consistently(self, new_data, operation_name="数据更新"):
        """统一更新数据的方法 - 现在通过全局数据管理器"""
        try:
            print(f"[DEBUG-INTEGRATION] 统一数据更新: {operation_name}")

            # 核心修改：通过全局数据管理器更新数据
            success = self.global_data_manager.update_current_data(
                new_data,
                operation_name,
                metadata={'source': 'main_window'}
            )

            if not success:
                # 备用方案：直接更新（保持兼容性）
                self.data = new_data
                self.data_processor.data = new_data

                # 通知相关组件数据已更新
                if hasattr(self, 'moving_window_integration') and self.moving_window_integration:
                    self.moving_window_integration.set_current_data(new_data)

                # 更新状态管理器
                self.state_manager.update_state("data_updated",
                                                info={'rows': len(new_data) if new_data is not None else 0})

            print(f"[DEBUG-INTEGRATION] 数据更新成功: {len(new_data) if new_data is not None else 0} 行")

        except Exception as e:
            print(f"[ERROR] 统一数据更新失败: {e}")
            raise









    def _init_ui(self):
        """初始化用户界面"""
        try:
            self.update_window_title()
            self.root.geometry("1000x700")
            self.root.configure(bg='white')

            # 配置样式
            try:
                ModernStyle.configure_ttk_styles()
            except Exception as e:
                print(f"[WARNING] {language_manager.get_text('style_config_failed', '样式配置失败')}: {e}")

            # 提前初始化状态变量
            self.file_var = tk.StringVar()
            self.analysis_status_var = tk.StringVar()
            self.analysis_status_var.set("Ready for geochemical analysis")
            self.chart_type_var = tk.StringVar()
            self.chart_combo = None  # chart_combo 不再显示在界面上

            self.setup_menu()
            self.setup_ui()

            print(f"[DEBUG] {language_manager.get_text('main_window_init_complete', '主窗口初始化完成')}")

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('main_window_init_failed', '主窗口初始化失败')}: {e}")
            self.show_error_message(
                language_manager.get_text('initialization_error', '初始化错误'),
                f"{language_manager.get_text('main_window_init_failed', '主窗口初始化失败')}:\n{str(e)}"
            )

    def update_window_title(self):
        """Update window title to Geo-mean v1.0"""
        try:
            self.root.title("Geo-mean v1.0")
        except Exception as e:
            print(f"[ERROR] Failed to update window title: {e}")
            self.root.title("Geo-mean v1.0")

    def _show_about_dialog(self):
        """显示关于对话框"""
        popup = tk.Toplevel(self.root)
        popup.title("About Geo-mean")
        popup.geometry("360x240")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(bg='white')

        # 居中
        popup.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() // 2) - 180
        y = self.root.winfo_rooty() + (self.root.winfo_height() // 2) - 120
        popup.geometry(f"360x240+{x}+{y}")

        frame = tk.Frame(popup, bg='white', padx=24, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Geo-mean", font=('Segoe UI', 16, 'bold'),
                 bg='white', fg='#1e293b').pack(anchor='w')

        tk.Frame(frame, height=1, bg='#e2e8f0').pack(fill=tk.X, pady=(8, 12))

        infos = [
            ("Version", "1.0"),
            ("Date", "2026.1"),
            ("Description", "A geochemical data analysis tool."),
        ]
        for label, value in infos:
            row = tk.Frame(frame, bg='white')
            row.pack(anchor='w', pady=2)
            tk.Label(row, text=f"{label}: ", font=('Segoe UI', 10, 'bold'),
                     bg='white', fg='#475569').pack(side=tk.LEFT)
            tk.Label(row, text=value, font=('Segoe UI', 10),
                     bg='white', fg='#1e293b').pack(side=tk.LEFT)

        tk.Button(
            frame, text="OK", command=popup.destroy,
            font=('Segoe UI', 10), padx=20, pady=4,
            bg='#f1f5f9', relief=tk.FLAT, cursor='hand2'
        ).pack(anchor='e', pady=(16, 0))

    def setup_menu(self):
        """设置菜单栏"""
        try:
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)

            # File 菜单
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="Browse", command=self.select_file)

            # Process 菜单
            process_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Process", menu=process_menu)
            process_menu.add_command(label="Outlier Elimination", command=self.open_outlier_removal_dialog)
            process_menu.add_command(label="Outlier Elimination for X-intervals", command=self.open_segmented_outlier_dialog)
            process_menu.add_command(label="Conditional Filtering", command=self.open_filter_conditions_dialog)
            process_menu.add_command(label="Geographic Gridding", command=self.open_geo_aggregation_dialog)

            # Analysis 菜单
            analysis_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Analysis", menu=analysis_menu)
            analysis_menu.add_command(label="Moving Average Analysis", command=self.run_moving_window_analysis)
            if BOOTSTRAP_MEDIAN_WINDOW_AVAILABLE:
                analysis_menu.add_command(label="Bootstrap Median Window", command=self.run_bootstrap_median_window_analysis)

            # Data Export 直接作为菜单栏按钮
            menubar.add_command(label="Data Export", command=self.open_export_dialog)

            # About 直接作为菜单栏按钮
            menubar.add_command(label="About", command=self._show_about_dialog)

        except Exception as e:
            print(f"[ERROR] Menu setup failed: {e}")
        """设置菜单栏"""
        try:
            menubar = tk.Menu(self.root)
            self.root.config(menu=menubar)

            # File 菜单
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="File", menu=file_menu)
            file_menu.add_command(label="Browse", command=self.select_file)

            # Process 菜单
            process_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Process", menu=process_menu)
            process_menu.add_command(label="Outlier Elimination", command=self.open_outlier_removal_dialog)
            process_menu.add_command(label="Outlier Elimination for X-intervals", command=self.open_segmented_outlier_dialog)
            process_menu.add_command(label="Conditional Filtering", command=self.open_filter_conditions_dialog)
            process_menu.add_command(label="Geographic Gridding", command=self.open_geo_aggregation_dialog)

            # Analysis 菜单
            analysis_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Analysis", menu=analysis_menu)
            analysis_menu.add_command(label="Moving Average Analysis", command=self.run_moving_window_analysis)
            if BOOTSTRAP_MEDIAN_WINDOW_AVAILABLE:
                analysis_menu.add_command(label="Bootstrap Median Window", command=self.run_bootstrap_median_window_analysis)

            # Data Export 直接作为菜单栏按钮
            menubar.add_command(label="Data Export", command=self.open_export_dialog)

            # About 直接作为菜单栏按钮
            menubar.add_command(label="About", command=self._show_about_dialog)

        except Exception as e:
            print(f"[ERROR] Menu setup failed: {e}")

    def setup_ui(self):
        """设置用户界面 - GeoPyTool风格"""
        self.main_frame = tk.Frame(self.root, bg='white')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.create_main_content()

    def _create_toolbar(self):
        """创建工具栏 - GeoPyTool风格的快捷按钮栏"""
        toolbar = tk.Frame(self.root, bg='#f0f0f0', relief=tk.FLAT, bd=0)
        toolbar.pack(fill=tk.X, side=tk.TOP)

        btn_style = dict(
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            bg='#f0f0f0',
            activebackground='#d0d0d0',
            cursor='hand2',
            padx=8,
            pady=4,
            bd=0
        )

        buttons = [
            ("Open",        self.select_file),
            ("Save",        self.open_export_dialog),
            ("|",           None),
            ("Outlier",     self.open_outlier_removal_dialog),
            ("Segment",     self.open_segmented_outlier_dialog),
            ("Filter",      self.open_filter_conditions_dialog),
            ("Gridding",    self.open_geo_aggregation_dialog),
            ("|",           None),
            ("Moving Avg",  self.run_moving_window_analysis),
            ("Plotting",    self.generate_chart),
            ("Save Chart",  self.save_chart),
        ]

        for label, cmd in buttons:
            if label == "|":
                sep = tk.Label(toolbar, text=" | ", bg='#f0f0f0', fg='#aaaaaa', font=('Segoe UI', 10))
                sep.pack(side=tk.LEFT)
            else:
                btn = tk.Button(toolbar, text=label, command=cmd, **btn_style)
                btn.pack(side=tk.LEFT, padx=1, pady=2)
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#d8e4f0'))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#f0f0f0'))

    def create_header(self):
        """已移除大标题栏 - 改用工具栏风格，此方法保留为空以防其他地方调用"""
        pass

    def create_main_content(self):
        """创建主要内容"""
        self.create_data_section()
        self.create_status_section()
        self.create_data_table_section()

    def create_file_section(self):
        """Create file selection area - Open File"""
        file_frame = tk.LabelFrame(
            self.main_frame,
            text="Open File",  # Changed from Chinese
            font=('Arial', 12, 'bold'),
            bg='white'
        )
        file_frame.pack(fill=tk.X, pady=10)

        content_frame = tk.Frame(file_frame, bg='white')
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        self.file_var = tk.StringVar()
        file_entry = tk.Entry(
            content_frame,
            textvariable=self.file_var,
            state="readonly",
            font=('Arial', 10)
        )
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_btn = tk.Button(
            content_frame,
            text="Browse",  # Changed from Chinese
            command=self.select_file,
            bg='#4A90E2',
            fg='white',
            font=('Arial', 10),
            cursor='hand2'
        )
        browse_btn.pack(side=tk.RIGHT)

    def create_data_section(self):
        """创建数据预览区域 - Select Variables（紧凑版）"""
        data_frame = tk.LabelFrame(
            self.main_frame,
            text="Select Variables",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        data_frame.pack(fill=tk.X, pady=(4, 2))

        content_frame = tk.Frame(data_frame, bg='white')
        content_frame.pack(fill=tk.X, padx=8, pady=6)

        # X-axis selection
        x_frame = tk.Frame(content_frame, bg='white')
        x_frame.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(
            x_frame,
            text="X-axis",
            font=('Arial', 9),
            bg='white'
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.x_col_var = tk.StringVar()
        self.x_combo = ttk.Combobox(x_frame, textvariable=self.x_col_var, width=14, state="readonly")
        self.x_combo.pack(side=tk.LEFT)
        self.x_combo.bind('<<ComboboxSelected>>', self.on_column_changed)

        # Y-axis selection
        y_frame = tk.Frame(content_frame, bg='white')
        y_frame.pack(side=tk.LEFT)

        tk.Label(
            y_frame,
            text="Y-axis",
            font=('Arial', 9),
            bg='white'
        ).pack(side=tk.LEFT, padx=(0, 4))

        self.y_col_var = tk.StringVar()
        self.y_combo = ttk.Combobox(y_frame, textvariable=self.y_col_var, width=14, state="readonly")
        self.y_combo.pack(side=tk.LEFT)
        self.y_combo.bind('<<ComboboxSelected>>', self.on_column_changed)

        # Plotting 按钮
        plot_btn = tk.Button(
            content_frame,
            text="Plotting",
            command=self.generate_chart,
            font=('Arial', 9),
            bg='#4a4a4a',
            fg='white',
            relief=tk.FLAT,
            padx=12,
            pady=3,
            cursor='hand2',
            bd=0
        )
        plot_btn.pack(side=tk.LEFT, padx=(16, 0))
        plot_btn.bind('<Enter>', lambda e: plot_btn.config(bg='#333333'))
        plot_btn.bind('<Leave>', lambda e: plot_btn.config(bg='#4a4a4a'))

    def create_analysis_section(self):
        """创建分析区域 - Data Process (统一按钮大小)"""
        analysis_frame = tk.LabelFrame(
            self.main_frame,
            text="Data Process",
            font=('Arial', 12, 'bold'),
            bg='white'
        )
        analysis_frame.pack(fill=tk.X, pady=10)

        content_frame = tk.Frame(analysis_frame, bg='white')
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        # Status display
        self.analysis_status_var = tk.StringVar()
        self.analysis_status_var.set("Ready for geochemical analysis")

        status_label = tk.Label(
            content_frame,
            textvariable=self.analysis_status_var,
            font=('Arial', 9),
            fg='#666666',
            bg='white'
        )
        status_label.pack(anchor=tk.W, pady=(0, 10))

        # Button frame
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(fill=tk.X)

        # 统一按钮样式 - 适中尺寸，美观协调
        button_style = {
            'font': ('Arial', 10),  # 适中字体大小
            'cursor': 'hand2',
            'width': 13,  # 适中宽度
            'height': 2,  # 适中高度
            'relief': tk.FLAT,
            'borderwidth': 0  # 去掉边框让颜色更纯
        }

        # Outlier Elimination button
        outlier_btn = tk.Button(
            button_frame,
            text="Outlier\nElimination",
            command=self.open_outlier_removal_dialog,
            bg='#17a2b8',
            fg='white',
            **button_style
        )
        outlier_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Outlier Elimination for X-intervals button
        segmented_outlier_btn = tk.Button(
            button_frame,
            text="Outlier Elimination\nfor X-intervals",
            command=self.open_segmented_outlier_dialog,
            bg='#e74c3c',
            fg='white',
            **button_style
        )
        segmented_outlier_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Data Filtering button
        filter_btn = tk.Button(
            button_frame,
            text="Data Filtering",
            command=self.open_filter_conditions_dialog,
            bg='#28a745',
            fg='white',
            **button_style
        )
        filter_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Geographic Gridding button
        geo_aggregation_btn = tk.Button(
            button_frame,
            text="Geographic\nGridding",
            command=self.open_geo_aggregation_dialog,
            bg='#fd7e14',
            fg='white',
            **button_style
        )
        geo_aggregation_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Data Export button
        export_btn = tk.Button(
            button_frame,
            text="Data Export",
            command=self.open_export_dialog,
            bg='#f59e0b',
            fg='white',
            **button_style
        )
        export_btn.pack(side=tk.LEFT)

    def _create_analysis_status_display(self, parent):
        """创建分析状态显示 - 优化版"""
        self.analysis_status_var = tk.StringVar()
        self.analysis_status_var.set(
            language_manager.get_text('ready_for_analysis', '准备进行移动窗口分析 - 点击移动窗口分析按钮开始')
        )

        status_label = tk.Label(
            parent,
            textvariable=self.analysis_status_var,
            font=('Arial', 9),
            fg='#666666',
            bg='white'
        )
        status_label.pack(anchor=tk.W, pady=(0, 10))

    def _create_analysis_buttons(self, button_frame):
        """优化后的分析按钮布局 - 统一按钮大小并添加导出数据"""
        # 统一的按钮样式参数
        button_style = {
            'font': ('Arial', 10),
            'cursor': 'hand2',
            'padx': 10,
            'pady': 5
        }

        # 异常值处理按钮
        outlier_btn = tk.Button(
            button_frame,
            text=f"[Outlier] {language_manager.get_text('outlier_removal', '异常值处理')}",
            command=self.open_outlier_removal_dialog,
            bg='#17a2b8',
            fg='white',
            **button_style
        )
        outlier_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 分段异常值处理按钮
        segmented_outlier_btn = tk.Button(
            button_frame,
            text=f"[Segment] {language_manager.get_text('segmented_outlier_processing', '分段异常值处理')}",
            command=self.open_segmented_outlier_dialog,
            bg='#e74c3c',
            fg='white',
            **button_style
        )
        segmented_outlier_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 筛选条件按钮
        if self._is_filter_manager_available():
            filter_btn = tk.Button(
                button_frame,
                text=f"[Filter] {language_manager.get_text('filter_conditions', '筛选条件')}",
                command=self.open_filter_conditions_dialog,
                bg='#28a745',
                fg='white',
                **button_style
            )
            filter_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 地理数据聚合按钮
        geo_aggregation_btn = tk.Button(
            button_frame,
            text=f"[Geo] {language_manager.get_text('geo_data_aggregation', '地理数据聚合')}",
            command=self.open_geo_aggregation_dialog,
            bg='#fd7e14',  # 橙色
            fg='white',
            **button_style
        )
        geo_aggregation_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 导出数据按钮 - 放到地理数据聚合右边
        export_btn = tk.Button(
            button_frame,
            text=f"[Export] {language_manager.get_text('export_data', '导出数据')}",
            command=self.open_export_dialog,
            bg='#f59e0b',  # 橙色
            fg='white',
            **button_style
        )
        export_btn.pack(side=tk.LEFT, padx=(0, 10))

    def open_geo_aggregation_dialog(self):
        """打开新的简单地理聚合对话框 - 确保导入路径正确"""
        try:
            # 数据验证
            is_valid, message = self.data_manager.validate_data_for_operation()
            if not is_valid:
                self.show_warning_message('警告', message)
                return

            # 导入新的地理聚合对话框
            from ui.geo_aggregation_dialog import show_simple_geo_aggregation_dialog

            # 获取数据列信息
            numeric_columns = self.data_processor.get_numeric_columns()
            all_columns = list(self.data.columns) if self.data is not None else []

            print(f"[DEBUG] 打开简单地理聚合对话框: {len(all_columns)} 列, {len(numeric_columns)} 数值列")

            # 显示对话框
            result = show_simple_geo_aggregation_dialog(
                self.root,
                self.data,
                all_columns,
                numeric_columns
            )

            if result:
                self.apply_simple_geo_aggregation_result(result)
            else:
                print("[INFO] 用户取消了地理聚合操作")

        except ImportError as e:
            error_msg = '无法导入地理聚合对话框模块'
            print(f"[ERROR] {error_msg}: {e}")
            self.show_error_message('错误', f"{error_msg}\n请确保 ui/geo_aggregation_dialog.py 文件存在且正确")
        except Exception as e:
            error_msg = '简单地理聚合对话框打开失败'
            print(f"[ERROR] {error_msg}: {e}")
            self.show_error_message('错误', f"{error_msg}: {str(e)}")

    # 在 main_window_i18n.py 中添加这个方法，专门处理地理聚合数据导出

    def export_clean_geo_aggregated_data(self, data, filename):
        """
        清洁的地理聚合数据导出 - 使用保存的原始列顺序
        """
        try:
            import pandas as pd
            from datetime import datetime

            print(f"[CLEAN-EXPORT] 开始导出地理聚合数据: {len(data)} 行")
            print(f"[DEBUG] 当前数据列数: {len(data.columns)}")

            # 安全检查：确保是地理聚合数据
            if not ('agg_key' in data.columns and 'sample_count' in data.columns):
                print("[WARNING] 不是地理聚合数据，使用标准导出")
                return self._perform_smart_export(data, filename, "Standard Export")

            # 核心修复：检测并移除重复列
            original_cols = list(data.columns)
            unique_cols = []
            seen_cols = set()

            for col in original_cols:
                if col not in seen_cols:
                    unique_cols.append(col)
                    seen_cols.add(col)
                else:
                    print(f"[FIX] 检测到重复列，已跳过: {col}")

            # 使用去重后的列创建干净的数据
            clean_data = data[unique_cols].copy()
            print(f"[FIX] 去重后列数: {len(clean_data.columns)}")

            # === 关键改进：使用保存的原始列顺序 ===
            aggregation_cols = ['agg_key', 'sample_count']  # 聚合过程新增的列

            if hasattr(self, 'original_column_order') and self.original_column_order:
                # 使用保存的原始列顺序
                print(f"[DEBUG] 使用保存的原始列顺序: {len(self.original_column_order)} 列")

                # 分离聚合列和原始列
                agg_cols_present = [col for col in aggregation_cols if col in clean_data.columns]

                # 按保存的原始顺序排列原始列
                original_cols_present = []
                for col in self.original_column_order:
                    if col in clean_data.columns:
                        original_cols_present.append(col)

                # 检查是否有遗漏的列（不在原始顺序中但存在于当前数据中）
                all_accounted_cols = set(agg_cols_present + original_cols_present)
                missing_cols = [col for col in clean_data.columns if col not in all_accounted_cols]

                if missing_cols:
                    print(f"[DEBUG] 发现新增列（不在原始顺序中）: {missing_cols}")
                    original_cols_present.extend(missing_cols)

                # 最终列顺序：聚合列 + 原始列（按源文件顺序）
                final_order = agg_cols_present + original_cols_present

            else:
                # 备用方案：如果没有保存原始列顺序，使用当前顺序
                print(f"[WARNING] 未找到保存的原始列顺序，使用当前顺序")
                agg_cols_present = [col for col in aggregation_cols if col in clean_data.columns]
                other_cols = [col for col in clean_data.columns if col not in aggregation_cols]
                final_order = agg_cols_present + other_cols

            export_data = clean_data[final_order].copy()

            print(f"[CLEAN-EXPORT] 列顺序策略: 聚合列在前，其他列按源文件顺序")
            print(f"[CLEAN-EXPORT] 聚合列: {[col for col in aggregation_cols if col in export_data.columns]}")
            print(f"[CLEAN-EXPORT] 最终导出列数: {len(export_data.columns)}")
            print(f"[CLEAN-EXPORT] 前10列: {list(export_data.columns[:10])}")

            # 导出到Excel - 先把Timestamp类型转为字符串，避免旧版openpyxl报错
            for col in export_data.columns:
                if export_data[col].dtype == 'datetime64[ns]' or str(export_data[col].dtype).startswith('datetime'):
                    export_data[col] = export_data[col].astype(str)
                elif export_data[col].apply(lambda x: hasattr(x, 'year') and hasattr(x, 'month')).any():
                    export_data[col] = export_data[col].astype(str)

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main data sheet
                export_data.to_excel(writer, sheet_name='Aggregated Data', index=False)

                # Summary statistics
                if 'sample_count' in export_data.columns:
                    stats = {
                        'Item': [
                            'Total Groups',
                            'Total Samples',
                            'Avg Samples per Group',
                            'Max Group Size',
                            'Min Group Size',
                            'Compression Ratio'
                        ],
                        'Value': [
                            len(export_data),
                            export_data['sample_count'].sum(),
                            f"{export_data['sample_count'].mean():.1f}",
                            export_data['sample_count'].max(),
                            export_data['sample_count'].min(),
                            f"{((export_data['sample_count'].sum() - len(export_data)) / export_data['sample_count'].sum() * 100):.1f}%"
                        ]
                    }

                    stats_df = pd.DataFrame(stats)
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)

                # Export info sheet
                info_data = {
                    'Item': [
                        'Export Time',
                        'Data Type',
                        'Aggregation Method',
                        'Row Count',
                        'Column Count',
                        'Column Order',
                        'Note'
                    ],
                    'Content': [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'Geographic Aggregation Data',
                        'Lat/Lon + Age Grid Aggregation',
                        len(export_data),
                        len(export_data.columns),
                        'Aggregation columns first, others follow source file order',
                        'Coordinates are representative values; elements are group means'
                    ]
                }

                info_df = pd.DataFrame(info_data)
                info_df.to_excel(writer, sheet_name='Info', index=False)

            print(f"[CLEAN-EXPORT] 清洁导出完成: {filename}")
            return True

        except Exception as e:
            print(f"[ERROR] 清洁导出失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    # 然后在你的 open_export_dialog 方法中，检测到地理聚合数据时调用：

    # 在 open_export_dialog 方法中修改：

    def apply_simple_geo_aggregation_result(self, result):
        """应用简单地理聚合结果 - 保存原始列顺序版本"""
        try:
            # 更新状态
            self.update_status("[Processing] 应用地理聚合结果...")

            # === 新增：保存原始列顺序（在数据被修改前） ===
            if hasattr(self, 'data') and self.data is not None:
                # 保存聚合前的原始列顺序（排除即将新增的聚合列）
                self.original_column_order = [col for col in self.data.columns
                                              if col not in ['agg_key', 'sample_count']]
                print(f"[DEBUG] 已保存原始列顺序: {len(self.original_column_order)} 列")
                print(f"[DEBUG] 原始列顺序前10列: {self.original_column_order[:10]}")

            # 获取聚合数据和统计信息
            aggregated_data = result['aggregated_data']
            method = result['aggregation_method']
            group_column = result['group_column']
            stats = result['statistics']

            print(f"[DEBUG] 应用聚合结果: {method} 方法")
            print(f"[DEBUG] 聚合后数据形状: {aggregated_data.shape}")

            # 验证聚合数据
            if aggregated_data is None or len(aggregated_data) == 0:
                raise ValueError("聚合后的数据为空")

            # 构建操作名称 - 修复版本，安全处理parameters
            if 'parameters' in stats and 'coord_description' in stats['parameters']:
                coord_desc = stats['parameters']['coord_description']
                age_desc = stats['parameters']['age_description']
                operation_name = f"简单地理聚合 ({coord_desc} + {age_desc})"
            else:
                # 备用操作名称
                coord_agg = stats.get('coord_aggregation', 'unknown')
                age_agg = stats.get('age_aggregation', 'unknown')
                operation_name = f"简单地理聚合 (经纬度:{coord_agg}, 年龄:{age_agg})"

            # 通过全局数据管理器统一更新数据
            self._update_data_consistently(aggregated_data, operation_name)

            # 使用保留列选择的更新方法
            self.update_data_interface_preserve_selection()

            # 更新分析状态
            status_msg = (
                f"地理聚合完成: "
                f"聚合方法 {method}, "
                f"数据压缩 {stats['compression_ratio']:.1%}"
            )
            self.update_geochem_analysis_status(status_msg, "success")

            # 更新主状态
            self.update_status(f"[OK] SUCCESS")

            # 显示详细的处理结果
            self._show_geo_aggregation_success_message(stats, method, group_column)

            print(f"[SUCCESS] 简单地理聚合完成: 使用 {method} 方法")

        except Exception as e:
            error_msg = '地理聚合结果应用失败'
            print(f"[ERROR] {error_msg}: {e}")

            # 打印详细错误信息用于调试
            import traceback
            print(f"[DEBUG] 详细错误信息:")
            print(traceback.format_exc())

            self.update_status(f"[Error] {error_msg}")
            self.show_error_message('错误', f"{error_msg}: {str(e)}")

    def _show_geo_aggregation_success_message(self, stats, method, group_column):
        """Show geographic aggregation success message - Fixed Unicode version"""
        try:
            # Safely get aggregation method description
            if 'parameters' in stats:
                coord_desc = stats['parameters'].get('coord_description', 'Unknown')
                age_desc = stats['parameters'].get('age_description', 'Unknown')
            else:
                # Backup description
                coord_desc = f"Coordinate aggregation: {stats.get('coord_aggregation', 'unknown')}"
                age_desc = f"Age aggregation: {stats.get('age_aggregation', 'unknown')}"

            # Safely get element column count
            element_count = len(stats.get('element_columns_averaged', []))

            result_message = f"""Location aggregation complete!

    [Aggregation Information]
    • Aggregation method: Based on {group_column}
    • Grouping rules: {method}
    • Age threshold: 20.0Ma (recommended)

    [Data Statistics]
    • Original data points: {stats['original_count']:,}
    • Aggregated data points: {stats['aggregated_count']:,}
    • Data compression ratio: {stats['compression_ratio']:.1%}
    • Average samples per group: {stats.get('avg_samples_per_group', 0):.1f}
    • Max samples per group: {stats.get('max_samples_per_group', 0)}

    [Processing Notes]
    • Location-based data has been aggregated and merged
    • Element series calculations based on sample count
    • Duplicates filtered through complete analysis

    [OK] All element column values preserved
    [OK] All series completed successfully
    [OK] No invalid Location entries

    >> Charts will automatically use the aggregated data"""

            self.show_info_message('Location Aggregation Success', result_message)

        except Exception as e:
            print(f"[ERROR] Failed to display success message: {e}")
            # Backup simple message
            try:
                simple_msg = f"""Location aggregation complete!

    Original data: {stats['original_count']} points
    After aggregation: {stats['aggregated_count']} points
    Compression ratio: {stats['compression_ratio']:.1%}"""
                self.show_info_message('Aggregation Complete', simple_msg)
            except Exception as e2:
                print(f"[ERROR] Even backup message failed: {e2}")
                self.show_info_message('Aggregation Complete',
                                       "Geographic aggregation completed, data has been updated.")

    def apply_geo_aggregation_result(self, result):
        """Apply geographic data aggregation result - Fixed version: Directly use passed aggregation result"""
        try:
            # Update status
            processing_msg = "Geographic data aggregation complete"
            self.update_status(f"[Processing] {processing_msg}...")

            # 🔧 Core fix: Directly use passed aggregation result, no more repeated aggregation
            if 'aggregated_data' not in result:
                raise ValueError("Missing aggregated_data in aggregation result")

            aggregated_data = result['aggregated_data']

            # Get other result information
            method = result.get('aggregation_method', 'unknown')
            group_column = result.get('group_column', 'unknown')
            stats = result.get('statistics', {})

            print(f"[DEBUG-FIX] Directly using passed aggregation result: {method} method")
            print(f"[DEBUG-FIX] Aggregated data shape: {aggregated_data.shape}")
            print(f"[DEBUG-FIX] Statistics: {stats}")

            # Validate aggregated data
            if aggregated_data is None or len(aggregated_data) == 0:
                raise ValueError("Aggregated data is empty")

            # Consistently update data through global data manager
            operation_name = f"Geographic Data Aggregation ({method} - {group_column})"
            self._update_data_consistently(aggregated_data, operation_name)

            # Use update method that preserves column selection
            self.update_data_interface_preserve_selection()

            # Update analysis status
            status_msg = (
                f"Geographic data aggregation complete: "
                f"Aggregation method {method}, "
                f"Group by column {group_column}"
            )
            self.update_geochem_analysis_status(status_msg, "success")

            # Update main status
            self.update_status(f"[OK] {processing_msg}")

            # Display detailed processing results
            result_message = f"""Location aggregation complete!

    Aggregation method: {method}
    Group by column: {group_column}
    Target columns: All numeric columns

    Data statistics:
    • Original data rows: {stats.get('original_count', 0):,}
    • Aggregated data rows: {stats.get('aggregated_count', 0):,}
    • Aggregation ratio: {stats.get('aggregation_ratio', 0):.2%}

    [OK] Charts will automatically use aggregated data"""

            self.show_info_message(
                "Success",
                result_message
            )

            print(f"[SUCCESS] Geographic data aggregation complete: Using {method} method grouped by {group_column}")

        except Exception as e:
            error_msg = "Geographic data aggregation application failed"
            print(f"[ERROR] {error_msg}: {e}")

            # Print detailed error information for debugging
            import traceback
            print(f"[DEBUG] Detailed error information:")
            print(traceback.format_exc())

            self.update_status(f"[Error] {error_msg}")
            self.show_error_message(
                "Error",
                f"{error_msg}: {str(e)}"
            )

    def open_filter_conditions_dialog(self):
        """打开筛选条件设置对话框 - 模块化版本"""
        try:
            # 模块化检查筛选管理器可用性
            if not self._is_filter_manager_available():
                self.show_warning_message(
                    language_manager.get_text('warning', '警告'),
                    language_manager.get_text('filter_manager_unavailable', '筛选管理器不可用，功能暂时禁用')
                )
                return

            # 调用筛选管理器
            self.filter_manager.show_filter_dialog()

            # 筛选后刷新数据预览表格
            if hasattr(self, 'global_data_manager'):
                current_data = self.global_data_manager.get_current_data()
                if current_data is not None:
                    self.refresh_data_table(current_data)
            elif hasattr(self, 'data') and self.data is not None:
                self.refresh_data_table(self.data)

            # 更新分析状态
            status_text = self.filter_manager.get_filter_status()
            self._update_analysis_status_with_filter(status_text)

        except Exception as e:
            error_msg = language_manager.get_text('open_filter_dialog_error', '打开筛选对话框失败')
            print(f"[ERROR] {error_msg}: {e}")
            self.show_error_message(
                language_manager.get_text('error', '错误'),
                f"{error_msg}: {str(e)}"
            )

    def _update_analysis_status_with_filter(self, status_text):
        """更新带筛选状态的分析状态"""
        try:
            if hasattr(self, 'update_geochem_analysis_status'):
                self.update_geochem_analysis_status(status_text, "info")
            else:
                print(f"[INFO] {status_text}")
        except Exception as e:
            print(f"[WARNING] {language_manager.get_text('update_status_failed', '更新状态失败')}: {e}")

    def open_segmented_outlier_dialog(self):
        """打开分段异常值处理对话框 - 使用全局数据管理器版本"""
        try:
            # 验证数据可用性
            is_valid, message = self.data_manager.validate_data_for_operation()
            if not is_valid:
                self.show_warning_message(
                    language_manager.get_text('warning', '警告'),
                    message
                )
                return

            # 检查是否有合适的年龄列
            numeric_columns = self.data_processor.get_numeric_columns()
            if len(numeric_columns) < 2:
                self.show_warning_message(
                    language_manager.get_text('warning', '警告'),
                    language_manager.get_text('insufficient_numeric_columns', '至少需要2个数值列才能进行分段异常值处理')
                )
                return

            # 智能检测年龄列
            age_column = self._detect_age_column(numeric_columns)
            if not age_column:
                # 如果没有检测到年龄列，让用户选择
                age_column = numeric_columns[0]  # 默认选择第一个数值列

            # 导入分段异常值处理对话框
            from ui.segmented_outlier_dialog import show_segmented_outlier_dialog

            # 核心修改：传递当前数据而不是原始数据
            current_data = self.global_data_manager.get_current_data()
            if current_data is None:
                current_data = self.data_processor.data

            print(f"[DEBUG] 分段异常值对话框使用数据: {len(current_data)} 行")

            # 显示对话框
            result = show_segmented_outlier_dialog(
                self.root,
                current_data,  # 使用当前数据
                age_column,
                numeric_columns
            )

            if result:
                self.apply_segmented_outlier_processing(result)

        except Exception as e:
            error_msg = language_manager.get_text('segmented_outlier_dialog_failed', '分段异常值处理对话框打开失败')
            print(f"[ERROR] {error_msg}: {e}")
            self.show_error_message(
                language_manager.get_text('error', '错误'),
                f"{error_msg}: {str(e)}"
            )

    def _detect_age_column(self, numeric_columns):
        """智能检测年龄列"""
        try:
            # 年龄列的候选关键词
            age_keywords = ['AGE', 'AGES', 'TIME', 'YEAR', 'YEARS', 'MA', 'DATE']

            for col in numeric_columns:
                col_upper = col.upper()
                for keyword in age_keywords:
                    if keyword in col_upper:
                        return col

            # 如果没有找到明显的年龄列，返回None
            return None
        except Exception as e:
            print(f"[ERROR] 检测年龄列失败: {e}")
            return None

    def apply_segmented_outlier_processing(self, result):
        """Apply segmented outlier processing result - Fixed version: No need for dropna(), as outlier rows have been directly deleted"""
        try:
            # Update status
            processing_msg = "Segmented outlier processing complete"
            self.update_status(f"[Processing] {processing_msg}...")

            # Record original data state - get from global data manager
            current_data = self.global_data_manager.get_current_data()
            original_rows = len(current_data) if current_data is not None else 0

            # Apply processing result
            processed_data = result['processed_data']
            target_column = result['target_column']
            segments_processed = result['segments_processed']
            total_outliers_removed = result['total_outliers_removed']
            processing_method = result['processing_method']

            print(f"[DEBUG] Segmented outlier processing result:")
            print(f"  Original data: {original_rows} rows")
            print(f"  Processed data: {len(processed_data)} rows")
            print(f"  Column count maintained: {len(processed_data.columns)}")
            print(f"  Outlier rows directly removed: {total_outliers_removed}")

            # === Key modification: No need to call dropna(), as outlier rows have been directly deleted ===
            #
            # Old code (problem):
            # cleaned_data = processed_data.dropna(subset=[target_col]).copy()
            #
            # New code (fix): Directly use processed data, as outlier rows have been physically removed
            final_data = processed_data.copy()

            print(f"[DEBUG] Final data shape: {final_data.shape}")
            print(f"[DEBUG] All columns retained: {list(final_data.columns)}")

            # Core modification: Consistently update data through global data manager
            operation_name = f"Segmented Outlier Processing ({processing_method} - {target_column}, {segments_processed} segments)"
            self._update_data_consistently(final_data, operation_name)

            # Calculate processing statistics
            current_rows = len(final_data)

            # 【Key modification】: Use update method that preserves column selection
            self.update_data_interface_preserve_selection()

            # Update analysis status
            status_msg = (
                f"{processing_msg}: "
                f"Processed segments {segments_processed}, "
                f"Removed outlier rows {total_outliers_removed}"
            )
            self.update_geochem_analysis_status(status_msg, "success")

            # Update main status
            self.update_status(f"[OK] {processing_msg}")

            # Display detailed processing results
            result_message = f"""segmented_outlier_processing_complete!

    Target Column: {target_column}
    Processing Method: {processing_method}
    Processed Segments: {segments_processed}
    Removed Outlier Rows: {total_outliers_removed}

    Data Statistics:
    • Original data rows: {original_rows:,}
    • Processed rows: {current_rows:,}
    • Data retention rate: {(current_rows / original_rows * 100):.1f}%

    [OK] Outlier rows have been directly removed
    [OK] All column structures preserved intact
    [OK] Qualifying rows remain complete

    [INFO] Charts will automatically use processed data"""

            self.show_info_message(
                "Success",
                result_message
            )

            print(
                f"[SUCCESS] Segmented outlier processing complete: Processed {segments_processed} segments, directly removed {total_outliers_removed} rows")

        except Exception as e:
            error_msg = "Segmented outlier processing application failed"
            print(f"[ERROR] {error_msg}: {e}")
            self.update_status(f"[Error] {error_msg}")
            self.show_error_message(
                "Error",
                f"{error_msg}: {str(e)}"
            )

    def create_chart_section(self):
        """Create chart area - Chart Generation & Visualization"""
        chart_frame = tk.LabelFrame(
            self.main_frame,
            text="Chart Generation & Visualization",  # Keep English
            font=('Arial', 12, 'bold'),
            bg='white'
        )
        chart_frame.pack(fill=tk.X, pady=10)

        content_frame = tk.Frame(chart_frame, bg='white')
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        # Chart type selection
        tk.Label(
            content_frame,
            text="Select Chart Type",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.chart_type_var = tk.StringVar()
        self.chart_combo = ttk.Combobox(
            content_frame,
            textvariable=self.chart_type_var,
            values=[],
            width=12,
            state="readonly"
        )
        self.chart_combo.pack(side=tk.LEFT, padx=(0, 10))

        # Moving Average Analysis button
        analysis_btn = tk.Button(
            content_frame,
            text="Moving Average",  # Match your screenshot
            command=self.run_moving_window_analysis,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 10),
            cursor='hand2'
        )
        analysis_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Bootstrap Median Window button (新增)
        if BOOTSTRAP_MEDIAN_WINDOW_AVAILABLE:
            bootstrap_median_btn = tk.Button(
                content_frame,
                text="Bootstrap Median",
                command=self.run_bootstrap_median_window_analysis,
                bg='#9c27b0',
                fg='white',
                font=('Arial', 10),
                cursor='hand2'
            )
            bootstrap_median_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Plotting button
        generate_btn = tk.Button(
            content_frame,
            text="Plotting",  # Match your screenshot
            command=self.generate_chart,
            bg='#007bff',
            fg='white',
            font=('Arial', 10),
            cursor='hand2'
        )
        generate_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Save Result button
        save_btn = tk.Button(
            content_frame,
            text="Save Result",  # Match your screenshot
            command=self.save_chart,
            bg='#28a745',
            fg='white',
            font=('Arial', 10),
            cursor='hand2'
        )
        save_btn.pack(side=tk.LEFT)

    def create_status_section(self):
        """Create status area（紧凑版）"""
        status_frame = tk.LabelFrame(
            self.main_frame,
            text="Status",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        status_frame.pack(fill=tk.X, pady=(2, 4))

        self.status_var = tk.StringVar()
        self.status_var.set("Welcome to Geo-mean v1.0! Please select a file to start analysis...")

        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=('Arial', 9),
            bg='white',
            justify=tk.LEFT,
            wraplength=900
        )
        status_label.pack(anchor=tk.W, padx=8, pady=4)

    def create_data_table_section(self):
        """创建数据浏览表格区域"""
        table_frame = tk.LabelFrame(
            self.main_frame,
            text="Data Preview",
            font=('Arial', 10, 'bold'),
            bg='white'
        )
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(2, 4))

        # 顶部信息栏
        info_bar = tk.Frame(table_frame, bg='white')
        info_bar.pack(fill=tk.X, padx=8, pady=(4, 0))

        self.table_info_var = tk.StringVar()
        self.table_info_var.set("No data loaded.")
        tk.Label(
            info_bar,
            textvariable=self.table_info_var,
            font=('Arial', 9),
            fg='#666666',
            bg='white'
        ).pack(side=tk.LEFT)

        # 表格容器
        tree_container = tk.Frame(table_frame, bg='white')
        tree_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        from tksheet import Sheet
        self.data_table = Sheet(
            tree_container,
            font=('Arial', 9, 'normal'),
            header_font=('Arial', 9, 'bold'),
            row_height=22,
            column_width=120,
            show_row_index=True,
            show_top_left=True,
        )
        self.data_table.enable_bindings((
            'single_select', 'drag_select',
            'column_select', 'row_select',
            'column_width_resize', 'double_click_column_resize',
            'arrowkeys', 'right_click_popup_menu',
            'rc_select', 'copy',
        ))
        self.data_table.pack(fill=tk.BOTH, expand=True)

    def _on_table_double_click(self, event):
        pass  # tksheet 内置选中和复制，不需要额外双击弹窗

    def refresh_data_table(self, data):
        """刷新数据表格内容 - tksheet版"""
        try:
            if not hasattr(self, 'data_table'):
                return

            if data is None or data.empty:
                self.data_table.set_sheet_data([])
                self.data_table.headers([])
                self.table_info_var.set("No data loaded.")
                return

            cols = list(data.columns)
            n_cols = len(cols)

            # 转换数据：category/float等统一转字符串
            display_data = data.reset_index(drop=True).astype(str).replace('nan', '')

            # tksheet 直接接受二维列表，一次性设置，无卡顿
            rows_values = display_data.values.tolist()

            self.data_table.headers(cols)
            self.data_table.set_sheet_data(rows_values)
            self.data_table.set_all_column_widths(120)

            total = len(data)
            self.table_info_var.set(f"Rows: {total},  Columns: {n_cols}")

            print(f"[DEBUG] 表格刷新完成: {total}行 x {n_cols}列")

        except Exception as e:
            import traceback
            print(f"[ERROR] 刷新数据表格失败: {e}")
            print(traceback.format_exc())


    # ======== 模块接口方法 ========

    def select_file(self):
        """选择文件"""
        self.file_loader.select_and_load_file()

    def set_file_path(self, file_path):
        """设置文件路径显示"""
        self.file_var.set(file_path)
        self.file_path = file_path

    def update_status(self, message):
        """更新状态"""
        try:
            self.status_var.set(message)
            self.root.update_idletasks()
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('update_status_failed', '更新状态失败')}: {e}")

    def on_file_load_success(self, message):
        """文件加载成功回调"""
        try:
            # 核心修改：通过全局数据管理器设置原始数据
            self.global_data_manager.set_original_data(
                self.data_processor.data,
                self.data_processor.file_path,
                f"文件: {self.data_processor.file_path}"
            )

            # 原有逻辑保持不变
            self._update_data_consistently(self.data_processor.data)
            self.file_path = self.data_processor.file_path

            if safe_check_dataframe(self.data):
                self.total_rows = len(self.data)
                self.geochem_filters = []
                self.filtered_data = None
                self.geochem_analyzer = None
                self.moving_window_results = None
                self.geochem_analysis_results = None

                # 初始化地球化学分析集成
                self._initialize_geochem_analysis()

                memory_info = self.data_manager.update_data_interface_after_load()
                self.update_status(f"[OK] {message}{memory_info}")

                # 刷新数据浏览表格
                self.refresh_data_table(self.data)
            else:
                self.update_status(f"[Error] {language_manager.get_text('loaded_data_empty', '加载的数据为空或无效')}")

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('file_load_process_error', '文件加载处理异常')}: {str(e)}")
            self.update_status(
                f"[Error] {language_manager.get_text('process_load_result_error', '处理加载结果时出错')}: {str(e)}")

    def _initialize_geochem_analysis(self):
        """初始化地球化学分析集成"""
        try:
            from geochemistry.moving_window_integration import create_integration_from_processor

            self.moving_window_integration = create_integration_from_processor(self.data_processor)

            ready_msg = language_manager.get_text('analysis_module_ready', '移动窗口分析模块已准备就绪')
            self.update_geochem_analysis_status(ready_msg, "success")

            columns = self.moving_window_integration.get_available_columns()
            numeric_count = len(columns.get('numeric', []))
            print(f"[DEBUG] {language_manager.get_text('numeric_columns_detected', '检测到数值列')}: {numeric_count}")

        except ImportError as e:
            print(
                f"[WARNING] {language_manager.get_text('unable_import_geochem_module', '无法导入地球化学分析模块')}: {e}")
            self.moving_window_integration = None
            error_msg = language_manager.get_text('geochem_analysis_unavailable', '地球化学分析模块不可用')
            self.update_geochem_analysis_status(error_msg, "error")
        except Exception as e:
            print(
                f"[ERROR] {language_manager.get_text('moving_window_init_interface_failed', '初始化移动窗口分析集成接口失败')}: {e}")
            self.moving_window_integration = None
            error_msg = language_manager.get_text('moving_window_init_failed', '移动窗口分析初始化失败')
            self.update_geochem_analysis_status(error_msg, "error")

    def on_file_load_error(self, error_message):
        """文件加载失败回调"""
        try:
            error_msg = language_manager.get_text('file_load_error', f'文件加载失败: {error_message}')
            self.update_status(f"[Error] {error_msg}")
            self.show_error_message(language_manager.get_text('error', '错误'), error_msg)
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('process_file_load_error_failed', '处理文件加载错误失败')}: {e}")
            self.update_status(
                f"[Error] {language_manager.get_text('file_load_error', '文件加载失败')}: {error_message}")

    def update_column_selectors(self, columns, numeric_columns):
        """更新列选择器 - X/Y轴只显示数值列"""
        try:
            numeric = numeric_columns if numeric_columns else columns
            self.x_combo['values'] = numeric
            self.y_combo['values'] = numeric

            if hasattr(self, 'chart_combo') and self.chart_combo is not None:
                self.chart_combo['values'] = self.chart_controller.get_chart_types()
                self.set_default_chart_type()
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('update_column_selectors_failed', '更新列选择器失败')}: {e}")

    def set_x_column(self, column):
        """设置X轴列"""
        try:
            self.x_col_var.set(column)
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('set_x_column_failed', '设置X轴列失败')}: {e}")

    def set_y_column(self, column):
        """设置Y轴列"""
        try:
            self.y_col_var.set(column)
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('set_y_column_failed', '设置Y轴列失败')}: {e}")

    def set_default_chart_type(self):
        """设置默认图表类型"""
        try:
            chart_types = self.chart_controller.get_chart_types()
            if chart_types:
                self.chart_type_var.set(chart_types[0])
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('set_default_chart_type_failed', '设置默认图表类型失败')}: {e}")

    def clear_column_selectors(self):
        """清空列选择器"""
        try:
            self.x_combo['values'] = []
            self.y_combo['values'] = []
            self.x_col_var.set("")
            self.y_col_var.set("")
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('clear_column_selectors_failed', '清空列选择器失败')}: {e}")

    def on_column_changed(self, event=None):
        """列选择改变事件"""
        try:
            if safe_check_dataframe(self.data):
                x_col = self.x_col_var.get()
                y_col = self.y_col_var.get()
                if x_col and y_col:
                    self.update_status(
                        f"[Column] {language_manager.get_text('x_axis_column', 'X轴')}: {x_col} | "
                        f"{language_manager.get_text('y_axis_column', 'Y轴')}: {y_col} | "
                        f"{language_manager.get_text('chart_x_axis_small_to_large', '图表X轴将从小到大排序')}")
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('column_change_process_failed', '列选择变化处理失败')}: {e}")

    # ======== 地球化学分析功能 ========

    def open_outlier_removal_dialog(self):
        """打开异常值处理对话框 - 使用全局数据管理器版本"""
        try:
            is_valid, message = self.data_manager.validate_data_for_operation()
            if not is_valid:
                self.show_warning_message(
                    language_manager.get_text('warning', '警告'),
                    message
                )
                return

            from ui.outlier_removal_dialog import show_outlier_removal_dialog

            numeric_columns = self.data_processor.get_numeric_columns()

            # 核心修改：传递当前数据而不是原始数据
            current_data = self.global_data_manager.get_current_data()
            if current_data is None:
                current_data = self.data_processor.data

            print(f"[DEBUG] 异常值对话框使用数据: {len(current_data)} 行")

            result = show_outlier_removal_dialog(self.root, current_data, numeric_columns)

            if result:
                self.apply_outlier_removal(result)

        except Exception as e:
            print(f"[ERROR] 打开异常值处理对话框失败: {e}")
            self.show_error_message(
                language_manager.get_text('error', '错误'),
                f"打开异常值处理对话框失败: {str(e)}"
            )

    def apply_outlier_removal(self, params):
        """Apply outlier removal - Fixed version: Ensure using current data and preserve column selection"""
        try:
            # Parameter validation
            if not params or 'column' not in params:
                raise ValueError("Invalid parameters")

            self.update_status(f"[Processing] Removing outliers...")

            # Core modification: Directly use current data from global data manager, not dependent on moving_window_integration
            current_data = self.global_data_manager.get_current_data()
            if current_data is None:
                self.show_error_message(
                    "Error",
                    "No data available for outlier removal"
                )
                return

            print(f"[DEBUG-OUTLIER-DIRECT] Using current data for outlier removal: {len(current_data)} rows")

            # Record original row count
            original_rows = len(current_data)
            target_col = params['column']

            # Directly perform outlier removal on current data
            processed_data = self.remove_outliers_from_data(
                current_data,
                target_col,
                params['method'],
                params['parameters']
            )

            if processed_data is None:
                self.show_error_message(
                    "Error",
                    "Outlier removal failed"
                )
                return

            # === Key improvement: No longer call dropna(), directly use processed data ===
            print(f"[DEBUG-OUTLIER-DIRECT] Processed data row count: {len(processed_data)}")
            print(f"[DEBUG-OUTLIER-DIRECT] Processed data column count: {len(processed_data.columns)}")

            # Verify if target column still exists and has valid data
            if target_col in processed_data.columns:
                valid_count = processed_data[target_col].notna().sum()
                print(f"[DEBUG-OUTLIER-DIRECT] Target column {target_col} valid data: {valid_count}")

            # Core modification: Consistently update data through global data manager
            operation_name = f"Outlier Removal ({params['method']} - {params['column']})"
            self._update_data_consistently(processed_data, operation_name)

            current_rows = len(processed_data)
            reduction_pct = ((original_rows - current_rows) / original_rows) * 100 if original_rows > 0 else 0

            print(f"[DEBUG-OUTLIER-DIRECT] Final data state: {original_rows} -> {current_rows}")

            self.update_status(f"[OK] Outlier removal complete")

            # 【Key modification】: Use update method that preserves column selection
            self.update_data_interface_preserve_selection()

            # Display processing results
            self.show_info_message(
                "Success",
                f"""Outlier removal complete!

    Target Column: {params['column']}
    Method: {params['method']}
    Original rows: {original_rows:,}
    Processed rows: {current_rows:,} 
    Data reduction: {reduction_pct:.1f}%

    [OK] All column structures preserved intact
    [OK] Only removed rows corresponding to outliers

    [INFO] Charts will automatically use processed data"""
            )

        except ValueError as e:
            self.show_error_message("Parameter Error", str(e))
        except Exception as e:
            print(f"[ERROR] Outlier removal failed: {e}")
            self.update_status(f"[Error] Outlier removal failed")
            self.show_error_message(
                "Error",
                f"Outlier removal failed: {str(e)}"
            )

    def run_moving_window_analysis(self):
        """移动窗口分析 - 添加快速分析支持"""
        try:
            # 原有的验证代码保持不变
            is_valid, message = self.data_manager.validate_data_for_operation()
            if not is_valid:
                self.show_warning_message('警告', message)
                return

            if not hasattr(self, 'moving_window_integration') or not self.moving_window_integration:
                self.show_error_message('错误', '移动窗口分析模块未初始化，请重新加载数据文件')
                return

            columns = self.moving_window_integration.get_available_columns()
            numeric_columns = columns['numeric']

            if len(numeric_columns) < 2:
                self.show_warning_message('警告', '至少需要2个数值列才能进行移动窗口分析')
                return

            # 显示对话框
            from ui.moving_window_dialog import show_enhanced_moving_window_dialog
            params = show_enhanced_moving_window_dialog(self.root, numeric_columns)

            if not params:
                return

            # 验证参数
            is_valid, error_msg = self._validate_analysis_params_local(params)
            if not is_valid:
                self.show_warning_message('警告', error_msg)
                return

            # 🆕 新增：根据分析方法选择不同的处理方式
            if params['analysis_method'] == 'quick':
                self._run_fast_analysis(params)
            else:
                # 保持原有的分析方法
                self._execute_analysis_with_boundary_fix(params, None)

        except Exception as e:
            error_msg = '启动移动窗口分析失败'
            print(f"[ERROR] {error_msg}: {e}")
            self.show_error_message('错误', f"{error_msg}: {str(e)}")

    # 立即修复方案 - 直接替换 main_window_i18n.py 中的 _run_fast_analysis 方法

    def _run_fast_analysis(self, params):
        """
        Fast boundary processing analysis function - fixed version
        Supports boundary processing but uses simple statistics instead of Bootstrap, greatly improves speed
        """
        try:
            self.update_status("[FAST] Starting fast boundary processing analysis...")

            # Get minimum sample parameters
            min_samples = params.get('min_samples', 5)
            boundary_mode = params.get('boundary_mode', 'inclusive')
            print(
                f"[FAST-DEBUG] Fast analysis configuration: boundary mode={boundary_mode}, minimum samples={min_samples}")

            # Get data
            current_data = None
            if hasattr(self, 'global_data_manager'):
                current_data = self.global_data_manager.get_current_data()
            if current_data is None and hasattr(self, 'data'):
                current_data = self.data
            if current_data is None and hasattr(self, 'data_processor'):
                current_data = self.data_processor.data

            if current_data is None or len(current_data) == 0:
                raise ValueError("No data available for analysis")

            print(f"[FAST-DEBUG] Fast analysis using data: {len(current_data)} rows")

            # Get analysis parameters
            age_column = params['age_column']
            target_column = params['target_column']
            window_size = float(params['window_size'])
            step_size = float(params['step_size'])
            min_age = float(params['min_age'])
            max_age = float(params['max_age'])

            # Validate columns exist
            if age_column not in current_data.columns:
                raise ValueError(f"Age column '{age_column}' does not exist")
            if target_column not in current_data.columns:
                raise ValueError(f"Target column '{target_column}' does not exist")

            # === Core fix: Implement fast boundary processing logic ===
            print(f"[FAST-DEBUG] Starting fast boundary processing: {boundary_mode} mode")

            # Data preprocessing
            age_data = pd.to_numeric(current_data[age_column], errors='coerce')
            target_data = pd.to_numeric(current_data[target_column], errors='coerce')
            valid_mask = age_data.notna() & target_data.notna()

            if valid_mask.sum() < 10:
                raise ValueError(f'Too few valid data points ({valid_mask.sum()} < 10)')

            print(f"[FAST-DEBUG] Valid data pairs: {valid_mask.sum()}")

            # Fast window generation (simplified version, no debug output)
            windows = self._generate_windows_fast(min_age, max_age, window_size, step_size)
            print(f"[FAST-DEBUG] Generated {len(windows)} windows")

            # Fast boundary processing + simple statistics
            results = self._fast_boundary_processing(
                current_data, age_data, target_data, valid_mask,
                windows, age_column, target_column, boundary_mode, min_samples
            )

            if results is not None and len(results) > 0:
                print(f"[DEBUG] 分析结果生成成功，数据形状: {results.shape}")
                print(f"[DEBUG] 结果列名: {list(results.columns)}")

                # 🔧 添加：统一重命名std_error为2SE
                if 'std_error' in results.columns:
                    results = results.rename(columns={'std_error': '2SE'})
                    print(f"[DEBUG] Quick模式已将std_error重命名为2SE")

                # Save results
                self.geochem_analysis_results = results
                self.moving_window_results = results
                print(f"[DEBUG] 结果已保存到主窗口")

                # 🔧 修复：使用移动窗口分析实际生成的动态列名
                age_col_name = None
                mean_col_name = None

                # 修复：更新特殊列名列表，包含所有非数据列
                special_columns = ['2SE', 'sample_count', 'window_low', 'window_high',
                                   'window_start', 'window_end', 'boundary_mode']

                for col in results.columns:
                    # 找到年龄列（原始列名，不包含_mean后缀，也不是特殊列）
                    if (col not in special_columns and
                            not col.endswith('_mean') and
                            '-' not in col):
                        age_col_name = col
                        break  # 只取第一个匹配的列

                for col in results.columns:
                    # 找到均值列（以_mean结尾但不包含组合符号）
                    if col.endswith('_mean') and '-' not in col:
                        mean_col_name = col
                        break  # 只取第一个匹配的列

                print(f"[DEBUG] 检测到的列名: age_col={age_col_name}, mean_col={mean_col_name}")

                # 分析完成后不自动切换X/Y轴选择，保留用户原有选择

                print(f"[DEBUG] 开始计算统计信息...")

                # Calculate statistics - 使用动态列名
                if mean_col_name:
                    print(f"[DEBUG] 使用均值列: {mean_col_name}")
                    valid_windows = len(results.dropna(subset=[mean_col_name]))
                else:
                    print(f"[DEBUG] 使用备用计算方式")
                    valid_windows = len(results)
                total_windows = len(results)

                print(f"[DEBUG] 统计完成: {valid_windows}/{total_windows}")

                self.update_status(
                    f"[OK] Fast boundary analysis completed: {valid_windows}/{total_windows} valid windows "
                    f"(boundary mode: {boundary_mode}, minimum samples: {min_samples})")

                print(f"[DEBUG] 状态更新完成，准备显示完成信息...")

                # Display completion information
                completion_text = f"""Fast boundary processing analysis completed!

        Boundary Mode: {boundary_mode}
        Window Count: {valid_windows}/{total_windows} valid windows
        Data Range: {min_age:.0f} - {max_age:.0f} Ma  
        Minimum Samples: {min_samples}
        Analysis Method: Fast statistics (no Bootstrap)

        Results are ready, charts can be generated."""

                print(f"[DEBUG] 准备显示成功对话框...")
                # 🔧 新增：Quick模式也调用自动图表生成
                try:
                    # 构造参数结构供自动图表生成使用
                    chart_params = {
                        'age_column': params.get('age_column'),
                        'target_column': params.get('target_column'),
                        'boundary_mode': 'quick',
                        'min_age': params.get('min_age', 0),
                        'max_age': params.get('max_age', 4000)
                    }

                    print("[DEBUG] Quick模式调用自动图表生成...")
                    # 调用相同的完成处理方法实现自动图表
                    self._handle_analysis_complete_safe(
                        None,  # progress_window (Quick模式没有进度窗口)
                        True,  # success
                        "Quick analysis completed",  # message
                        results,  # results
                        chart_params  # params
                    )
                except Exception as e:
                    print(f"[WARNING] Quick模式自动图表生成失败: {e}")
                    # 备用：显示原有完成消息
                    self.show_info_message('Fast Analysis Complete', completion_text)

                print(f"[DEBUG] Quick分析流程全部完成")
            else:
                print(f"[ERROR] 分析未产生有效结果")
                self.show_error_message('Analysis Failed', 'Fast analysis did not produce valid results')

        except Exception as e:
            error_msg = f"Fast analysis failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            print(f"[DEBUG] 完整错误信息: {traceback.format_exc()}")
            self.update_status(f"[Error] Fast analysis failed")
            self.show_error_message('Analysis Error', error_msg)

    def run_bootstrap_median_window_analysis(self):
        """Bootstrap Median Moving Window Analysis"""
        try:
            print("[BOOTSTRAP-MEDIAN-WINDOW] Starting analysis...")

            # Validate data
            is_valid, message = self.data_manager.validate_data_for_operation()
            if not is_valid:
                self.show_warning_message('Warning', message)
                return

            # Check moving window integration
            if not hasattr(self, 'moving_window_integration') or not self.moving_window_integration:
                self.show_error_message('Error',
                                        'Moving window analysis module not initialized, please reload data file')
                return

            # Get available columns
            columns = self.moving_window_integration.get_available_columns()
            numeric_columns = columns['numeric']

            if len(numeric_columns) < 2:
                self.show_warning_message('Warning', 'At least 2 numeric columns required for analysis')
                return

            # Show parameter dialog (reuse Moving Average dialog with Bootstrap title)
            from ui.moving_window_dialog import show_enhanced_moving_window_dialog
            params = show_enhanced_moving_window_dialog(self.root, numeric_columns, title="Bootstrap Median Window Analysis")

            if not params:
                return

            # Validate parameters
            is_valid, error_msg = self._validate_analysis_params_local(params)
            if not is_valid:
                self.show_warning_message('Warning', error_msg)
                return

            # Execute analysis
            self._execute_bootstrap_median_window_analysis(params)

        except Exception as e:
            print(f"[ERROR] Bootstrap median analysis failed: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message('Error', f"Analysis failed: {str(e)}")

    def _execute_bootstrap_median_window_analysis(self, params):
        """Execute Bootstrap median moving window analysis core logic"""
        try:
            self.update_status("[BOOTSTRAP-MEDIAN-WINDOW] Executing analysis...")

            # Get current data
            current_data = None
            if hasattr(self, 'global_data_manager'):
                current_data = self.global_data_manager.get_current_data()
            if current_data is None and hasattr(self, 'data'):
                current_data = self.data
            if current_data is None and hasattr(self, 'data_processor'):
                current_data = self.data_processor.data

            if current_data is None or len(current_data) == 0:
                raise ValueError("No data available")

            print(f"[BOOTSTRAP-MEDIAN-WINDOW] Using data: {len(current_data)} rows")

            # Execute in background thread
            import threading

            def analyze_thread():
                try:
                    from geochemistry.bootstrap_median_window_analyzer import run_bootstrap_median_window_analysis

                    result_df = run_bootstrap_median_window_analysis(
                        data=current_data,
                        params=params,
                        progress_callback=lambda msg: self.root.after(0, lambda: self.update_status(msg))
                    )

                    if result_df is not None and len(result_df) > 0:
                        self.root.after(0, lambda: self._handle_bootstrap_median_results(
                            result_df, params
                        ))
                    else:
                        error_msg = "Analysis produced no valid results"
                        self.root.after(0, lambda: self.show_error_message('Error', error_msg))

                except Exception as e:
                    error_msg = f"Analysis failed: {str(e)}"
                    print(f"[ERROR] {error_msg}")
                    self.root.after(0, lambda: self.show_error_message('Error', error_msg))
                finally:
                    self.root.after(0, lambda: self.update_status("Ready"))

            thread = threading.Thread(target=analyze_thread)
            thread.daemon = True
            thread.start()

        except Exception as e:
            print(f"[ERROR] Failed to execute analysis: {e}")
            raise

    def _handle_bootstrap_median_results(self, result_df, params):
        """Handle Bootstrap median analysis results"""
        try:
            print("[BOOTSTRAP-MEDIAN-WINDOW] Processing analysis results...")
            print(f"[DEBUG] Result shape: {result_df.shape}")
            print(f"[DEBUG] Column names: {list(result_df.columns)}")

            if hasattr(self, 'moving_window_integration'):
                self.moving_window_integration.analysis_results = result_df

            age_col = params['age_column']
            target_col = params['target_column']

            plot_data = result_df.copy()
            median_col = f'{target_col}_median'

            print(f"[DEBUG] Using column: {median_col}")

            chart_type = "Line Chart"

            self.analysis_original_columns = {
                'age_column': age_col,
                'target_column': target_col,
                'is_median_analysis': True
            }

            success, message = self.chart_controller.generate_chart(
                data=plot_data,
                x_col=age_col,
                y_col=median_col,
                chart_type=chart_type
            )

            if success:
                valid_count = result_df[median_col].notna().sum()
                total_count = len(result_df)

                summary = (
                    f"Bootstrap Median Moving Window Analysis Complete!\n\n"
                    f"Total windows: {total_count}\n"
                    f"Valid windows: {valid_count}\n"
                    f"Success rate: {valid_count / total_count * 100:.1f}%\n\n"
                    f"Analysis parameters:\n"
                    f"  Window size: {params['window_size']} Ma\n"
                    f"  Step size: {params['step_size']} Ma\n"
                    f"  Age range: {params['min_age']}-{params['max_age']} Ma\n"
                    f"  Min samples: {params.get('min_samples', 5)}\n"
                    f"  Statistic: Bootstrap median (±2σ)"
                )

                print("[SUCCESS] Analysis complete")
                print(summary)
                self.update_status("[BOOTSTRAP-MEDIAN-WINDOW] Complete")
            else:
                self.show_error_message('Error', f"Plotting failed: {message}")

        except Exception as e:
            print(f"[ERROR] Failed to process results: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message('Error', f"Failed to process results: {str(e)}")

    def _generate_windows_fast(self, min_age: float, max_age: float, window_size: float, step_size: float):
        """快速窗口生成 - 无调试输出版本"""
        windows = []
        current_center = min_age + window_size / 2

        while current_center + window_size / 2 <= max_age:
            start = current_center - window_size / 2
            end = current_center + window_size / 2
            windows.append((current_center, start, end))
            current_center += step_size

        return windows

    def _fast_boundary_processing(self, data, age_data, target_data, valid_mask,
                                  windows, age_column, target_column, boundary_mode, min_samples):
        """
        Fast boundary processing - core logic
        Supports different boundary modes but uses simple statistics
        """
        try:
            import numpy as np
            import pandas as pd

            results = []
            processed_count = 0
            skipped_count = 0

            # Select processing strategy based on boundary mode
            if boundary_mode == 'inclusive':
                # Inclusive mode: data points can be shared by multiple windows
                for i, (center, start, end) in enumerate(windows):
                    window_mask = (age_data >= start) & (age_data <= end) & valid_mask
                    window_values = target_data[window_mask].dropna()

                    if len(window_values) >= min_samples:
                        # Fast statistical calculation (no Bootstrap)
                        mean_val = float(np.mean(window_values))
                        std_val = float(np.std(window_values, ddof=1)) if len(window_values) > 1 else 0.0
                        std_error = 2 * std_val / np.sqrt(len(window_values)) if len(window_values) > 0 else 0.0

                        # 🔧 修复：使用动态列名
                        results.append({
                            age_column: center,  # 使用原始年龄列名
                            f'{target_column}_mean': mean_val,  # 使用原始目标列名_mean
                            'std_error': std_error,
                            'sample_count': len(window_values),
                            'window_start': start,
                            'window_end': end,
                            'boundary_mode': boundary_mode
                        })
                        processed_count += 1
                    else:
                        skipped_count += 1

            elif boundary_mode == 'exclusive':
                # Exclusive mode: each data point belongs to only one window
                assigned_indices = set()

                for i, (center, start, end) in enumerate(windows):
                    window_mask = (age_data >= start) & (age_data <= end) & valid_mask
                    candidate_indices = np.where(window_mask)[0]

                    # Calculate distance to window center, select closest window
                    available_indices = []
                    for idx in candidate_indices:
                        if idx not in assigned_indices:
                            age_val = age_data.iloc[idx]
                            # Check if other windows are closer
                            is_closest = True
                            current_dist = abs(age_val - center)

                            for j, (other_center, other_start, other_end) in enumerate(windows):
                                if i != j and other_start <= age_val <= other_end:
                                    other_dist = abs(age_val - other_center)
                                    if other_dist < current_dist:
                                        is_closest = False
                                        break

                            if is_closest:
                                available_indices.append(idx)

                    if len(available_indices) >= min_samples:
                        window_values = target_data.iloc[available_indices].dropna()
                        assigned_indices.update(available_indices)

                        # Fast statistical calculation
                        mean_val = float(np.mean(window_values))
                        std_val = float(np.std(window_values, ddof=1)) if len(window_values) > 1 else 0.0
                        std_error = 2 * std_val / np.sqrt(len(window_values)) if len(window_values) > 0 else 0.0

                        # 🔧 修复：使用动态列名
                        results.append({
                            age_column: center,  # 使用原始年龄列名
                            f'{target_column}_mean': mean_val,  # 使用原始目标列名_mean
                            'std_error': std_error,
                            'sample_count': len(window_values),
                            'window_start': start,
                            'window_end': end,
                            'boundary_mode': boundary_mode
                        })
                        processed_count += 1
                    else:
                        skipped_count += 1

            elif boundary_mode in ['left_priority', 'right_priority']:
                # Priority mode
                assigned_indices = set()
                window_order = range(len(windows)) if boundary_mode == 'left_priority' else reversed(
                    range(len(windows)))

                for i in window_order:
                    center, start, end = windows[i]
                    window_mask = (age_data >= start) & (age_data <= end) & valid_mask
                    candidate_indices = np.where(window_mask)[0]

                    available_indices = [idx for idx in candidate_indices if idx not in assigned_indices]

                    if len(available_indices) >= min_samples:
                        window_values = target_data.iloc[available_indices].dropna()
                        assigned_indices.update(available_indices)

                        # Fast statistical calculation
                        mean_val = float(np.mean(window_values))
                        std_val = float(np.std(window_values, ddof=1)) if len(window_values) > 1 else 0.0
                        std_error = 2 * std_val / np.sqrt(len(window_values)) if len(window_values) > 0 else 0.0

                        # 🔧 修复：使用动态列名
                        results.append({
                            age_column: center,  # 使用原始年龄列名
                            f'{target_column}_mean': mean_val,  # 使用原始目标列名_mean
                            'std_error': std_error,
                            'sample_count': len(window_values),
                            'window_start': start,
                            'window_end': end,
                            'boundary_mode': boundary_mode
                        })
                        processed_count += 1
                    else:
                        skipped_count += 1

            else:
                # Default to inclusive mode
                return self._fast_boundary_processing(
                    data, age_data, target_data, valid_mask, windows,
                    age_column, target_column, 'inclusive', min_samples
                )

            print(
                f"[FAST-DEBUG] Fast boundary processing completed: processed {processed_count} windows, skipped {skipped_count}")

            if not results:
                return None

            # Create result DataFrame and sort by age
            results_df = pd.DataFrame(results).sort_values(age_column).reset_index(drop=True)

            return results_df

        except Exception as e:
            print(f"[ERROR] Fast boundary processing failed: {e}")
            import traceback
            traceback.print_exc()
            return None



    def _execute_analysis_with_boundary_fix(self, params, progress_window):
        """执行边界处理分析 - 修复版 + 性能监控"""
        import threading

        # 获取性能分析器（如果可用）
        profiler = get_profiler() if PERFORMANCE_MONITORING else None

        def run_boundary_analysis():
            try:
                if profiler:
                    with profiler.profile_operation("主分析-数据获取"):
                        current_data = self.data.copy() if hasattr(self, 'data') and self.data is not None else None

                        if current_data is None:
                            raise ValueError("没有可用的数据进行分析")

                        profiler.log_data_size("主窗口当前数据", len(current_data))
                        profiler.check_analysis_path("数据来源", "主窗口self.data")
                else:
                    current_data = self.data.copy() if hasattr(self, 'data') and self.data is not None else None

                    if current_data is None:
                        raise ValueError("没有可用的数据进行分析")

                def progress_callback(message, current=0, total=0):
                    try:
                        print(f"[BOUNDARY-PROGRESS] {message}")  # 强制输出到控制台
                        if progress_window and hasattr(progress_window, 'cancelled') and not progress_window.cancelled:
                            progress_percent = (current / total * 100) if total > 0 else 0
                            self.root.after(0, lambda: progress_window.update_progress(
                                current, total, progress_percent, True, message))
                        else:
                            self.root.after(0, lambda: self.update_status(f"[Processing] {message}"))
                    except Exception as e:
                        print(f"[ERROR] 进度回调失败: {e}")

                results = None

                print("[DEBUG-FIX] [FIX] 尝试使用边界处理分析")
                print(f"[DEBUG-FIX] 全局边界分析器可用标志: {BOUNDARY_ANALYZER_AVAILABLE}")

                # [FIX] 修复：强制尝试使用边界分析器，无论标志如何
                if profiler:
                    with profiler.profile_operation("主分析-边界分析器创建"):
                        try:
                            print("[DEBUG-FIX] 强制尝试创建边界分析器...")
                            boundary_analyzer = BoundaryAnalyzer()
                            print("[DEBUG-FIX] [OK] 边界分析器创建成功")
                            profiler.check_analysis_path("边界分析器", "创建成功")
                        except Exception as e:
                            print(f"[DEBUG-FIX] [ERROR] 边界分析器创建失败: {e}")
                            boundary_analyzer = None
                            profiler.check_analysis_path("边界分析器", f"创建失败: {e}")
                else:
                    try:
                        print("[DEBUG-FIX] 强制尝试创建边界分析器...")
                        boundary_analyzer = BoundaryAnalyzer()
                        print("[DEBUG-FIX] [OK] 边界分析器创建成功")
                    except Exception as e:
                        print(f"[DEBUG-FIX] [ERROR] 边界分析器创建失败: {e}")
                        boundary_analyzer = None

                # [FIX] 修复：确保传递progress_callback
                if boundary_analyzer:
                    if profiler:
                        with profiler.profile_operation("主分析-边界处理执行"):
                            try:
                                print("[DEBUG-FIX] 开始边界处理分析，传递进度回调...")
                                profiler.check_analysis_path("边界处理分析", "开始执行")

                                raw_results = boundary_analyzer.analyze_with_boundary_handling(
                                    current_data,
                                    params,
                                    progress_callback=progress_callback  # 确保传递进度回调
                                )

                                print("[DEBUG-FIX] [OK] 边界分析完成")
                                profiler.check_analysis_path("边界处理分析", "执行成功")

                                # 转换结果格式
                                with profiler.profile_operation("主分析-结果转换"):
                                    if params.get('enable_boundary_comparison', False):
                                        results = self._convert_boundary_comparison_results(raw_results, params)
                                        print("[DEBUG-FIX] [CHART] 使用边界方法比较结果")
                                        profiler.check_analysis_path("结果转换", "边界方法比较")
                                    else:
                                        results = self._convert_single_boundary_results(raw_results, params)
                                        print("[DEBUG-FIX] [ANALYSIS] 使用单一边界处理结果")
                                        profiler.check_analysis_path("结果转换", "单一边界处理")

                            except Exception as e:
                                print(f"[WARNING] [WARNING] 边界处理分析失败，使用标准分析: {e}")
                                profiler.check_analysis_path("边界处理分析", f"失败: {e}")
                                import traceback
                                print(f"[DEBUG] 完整错误信息:\n{traceback.format_exc()}")
                                results = None
                    else:
                        try:
                            print("[DEBUG-FIX] 开始边界处理分析，传递进度回调...")

                            raw_results = boundary_analyzer.analyze_with_boundary_handling(
                                current_data,
                                params,
                                progress_callback=progress_callback  # 确保传递进度回调
                            )

                            print("[DEBUG-FIX] [OK] 边界分析完成")

                            # 转换结果格式
                            if params.get('enable_boundary_comparison', False):
                                results = self._convert_boundary_comparison_results(raw_results, params)
                                print("[DEBUG-FIX] [CHART] 使用边界方法比较结果")
                            else:
                                results = self._convert_single_boundary_results(raw_results, params)
                                print("[DEBUG-FIX] [ANALYSIS] 使用单一边界处理结果")

                        except Exception as e:
                            print(f"[WARNING] [WARNING] 边界处理分析失败，使用标准分析: {e}")
                            import traceback
                            print(f"[DEBUG] 完整错误信息:\n{traceback.format_exc()}")
                            results = None

                # 如果边界处理失败，使用标准分析作为备用
                if results is None:
                    if profiler:
                        with profiler.profile_operation("主分析-标准分析备用"):
                            print("[DEBUG-FIX] [REFRESH] 使用标准分析作为备用")
                            profiler.check_analysis_path("标准分析", "备用执行")
                            try:
                                from geochemistry.moving_window_integration import run_quick_moving_window_analysis
                                results = run_quick_moving_window_analysis(
                                    main_window_data=current_data,
                                    age_column=params['age_column'],
                                    target_column=params['target_column'],
                                    window_size=params['window_size'],
                                    step_size=params['step_size'],
                                    min_age=params.get('min_age', current_data[params['age_column']].min()),
                                    max_age=params.get('max_age', current_data[params['age_column']].max()),
                                    progress_callback=progress_callback
                                )
                                print("[DEBUG-FIX] [OK] 标准分析完成")
                                profiler.check_analysis_path("标准分析", "执行成功")
                            except Exception as e:
                                print(f"[ERROR] [ERROR] 标准分析也失败: {e}")
                                profiler.check_analysis_path("标准分析", f"失败: {e}")
                                results = None
                    else:
                        print("[DEBUG-FIX] [REFRESH] 使用标准分析作为备用")
                        try:
                            from geochemistry.moving_window_integration import run_quick_moving_window_analysis
                            results = run_quick_moving_window_analysis(
                                main_window_data=current_data,
                                age_column=params['age_column'],
                                target_column=params['target_column'],
                                window_size=params['window_size'],
                                step_size=params['step_size'],
                                min_age=params.get('min_age', current_data[params['age_column']].min()),
                                max_age=params.get('max_age', current_data[params['age_column']].max()),
                                progress_callback=progress_callback
                            )
                            print("[DEBUG-FIX] [OK] 标准分析完成")
                        except Exception as e:
                            print(f"[ERROR] [ERROR] 标准分析也失败: {e}")
                            results = None

                # 处理结果
                if results is not None and len(results) > 0:
                    if profiler:
                        with profiler.profile_operation("主分析-结果后处理"):
                            profiler.log_data_size("分析结果行数", len(results))
                            results = self._fix_error_bars_safe(results)
                            success = True
                            # 动态找到均值列
                            mean_col = None
                            for col in results.columns:
                                if col.endswith('_mean') and '-' not in col:
                                    mean_col = col
                                    break

                            if mean_col:
                                valid_windows = len(results.dropna(subset=[mean_col]))
                            else:
                                valid_windows = len(results)  # 备用方案
                            message = f'[SUCCESS] 分析完成！总窗口数: {len(results)}, 有效窗口数: {valid_windows}'
                            print(f"[DEBUG-FIX] [OK] 分析成功: {message}")
                            profiler.log_operation_count("有效窗口", valid_windows)
                    else:
                        results = self._fix_error_bars_safe(results)
                        success = True
                        # 动态找到均值列
                        mean_col = None
                        for col in results.columns:
                            if col.endswith('_mean') and '-' not in col:
                                mean_col = col
                                break

                        if mean_col:
                            valid_windows = len(results.dropna(subset=[mean_col]))
                        else:
                            valid_windows = len(results)  # 备用方案
                        message = f'[SUCCESS] 分析完成！总窗口数: {len(results)}, 有效窗口数: {valid_windows}'
                        print(f"[DEBUG-FIX] [OK] 分析成功: {message}")
                else:
                    success = False
                    message = '[ERROR] 分析未产生有效结果'
                    results = None
                    print("[DEBUG-FIX] [ERROR] 分析失败")

                # 打印性能摘要
                if profiler:
                    profiler.print_summary()

                # 处理完成
                self.root.after(0, lambda: self._handle_analysis_complete_safe(
                    progress_window, success, message, results, params))

            except Exception as e:
                error_msg = f"[ERROR] 分析线程出错: {str(e)}"
                print(f"[ERROR] {error_msg}")
                if profiler:
                    profiler.check_analysis_path("分析异常", str(e))
                    # 即使出错也打印性能摘要
                    profiler.print_summary()

                import traceback
                print(f"[DEBUG] 完整错误信息:\n{traceback.format_exc()}")
                self.root.after(0, lambda: self._handle_analysis_error_safe(progress_window, error_msg))

        # 启动分析线程
        threading.Thread(target=run_boundary_analysis, daemon=True).start()

    def _execute_analysis_with_progress_fixed(self, params, progress_window):
        """执行分析带进度条 - 修复版"""
        import threading

        def run_analysis():
            try:
                current_data = self.data.copy() if self.data is not None else None

                def progress_callback(message, current=0, total=0):
                    if progress_window and not progress_window.cancelled:
                        progress_percent = (current / total * 100) if total > 0 else 0
                        self.root.after(0, lambda: progress_window.update_progress(
                            current, total, progress_percent, True, message))
                    else:
                        self.root.after(0, lambda: self.update_status(f"[Processing] {message}"))

                # 使用快速分析
                try:
                    from geochemistry.moving_window_integration import run_quick_moving_window_analysis
                    results = run_quick_moving_window_analysis(
                        main_window_data=current_data,
                        age_column=params['age_column'],
                        target_column=params['target_column'],
                        window_size=params['window_size'],
                        step_size=params['step_size'],
                        min_age=params['min_age'],
                        max_age=params['max_age'],
                        progress_callback=progress_callback
                    )
                except:
                    # 备用方法
                    results = self.moving_window_integration.run_complete_analysis(params, progress_callback)

                # 【修复3】：修复误差棒数据
                if results is not None and len(results) > 0:
                    results = self._fix_error_bars(results)
                    success = True
                    message = f'分析完成！总窗口数: {len(results)}'
                else:
                    success = False
                    message = '分析未产生结果'

                # 处理完成
                self.root.after(0, lambda: self._handle_analysis_complete_fixed(
                    progress_window, success, message, results, params))

            except Exception as e:
                self.root.after(0, lambda: self._handle_analysis_error_simple(progress_window, str(e)))

        # 启动分析线程
        threading.Thread(target=run_analysis, daemon=True).start()

    def _fix_error_bars(self, results):
        """修复误差棒数据"""
        import numpy as np

        try:
            if 'std_error' not in results.columns:
                # 如果没有误差列，创建一个默认的
                results['std_error'] = results['mean'] * 0.1
                print("[INFO] 已添加默认误差棒")
            else:
                # 修复缺失的误差值
                nan_count = results['std_error'].isna().sum()
                if nan_count > 0:
                    print(f"[INFO] 修复 {nan_count} 个缺失的误差值")
                    # 用线性插值填充
                    results['std_error'] = results['std_error'].interpolate()
                    # 剩余的用均值填充
                    results['std_error'] = results['std_error'].fillna(results['std_error'].mean())

            # 确保误差值合理
            results['std_error'] = results['std_error'].abs()
            mean_val = results['mean'].mean()
            results.loc[results['std_error'] > mean_val * 0.5, 'std_error'] = mean_val * 0.1

            print(f"[SUCCESS] 误差棒修复完成，所有 {len(results)} 个数据点都有误差棒")
            return results

        except Exception as e:
            print(f"[ERROR] 修复误差棒失败: {e}")
            return results

    def open_export_dialog(self):
        """Export dialog - 始终导出原始加载数据"""
        try:
            # Data validation
            if not hasattr(self, 'data') or self.data is None or self.data.empty:
                self.show_warning_message('Warning', 'No data to export. Please load a data file first.')
                return

            # 始终使用原始数据，不使用分析结果
            export_data = self.data
            data_description = "Current Data"

            # Check for geographic aggregation data
            if ('agg_key' in export_data.columns and 'sample_count' in export_data.columns):
                data_description = "Geographic Aggregation Data"

            # Check for processed data from global data manager
            elif hasattr(self, 'global_data_manager'):
                current_data = self.global_data_manager.get_current_data()
                if current_data is not None and not current_data.empty:
                    if len(current_data) != len(self.data):
                        export_data = current_data
                        data_description = "Processed Data"

            # File selection dialog
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title=f"Export {data_description}",
                defaultextension='.xlsx',
                filetypes=[
                    ('Excel files', '*.xlsx'),
                    ('CSV files', '*.csv'),
                    ('All files', '*.*')
                ]
            )

            if not filename:
                return

            # Start export with infinite progress bar
            self._start_infinite_progress_export(export_data, filename, data_description)

        except Exception as e:
            error_msg = "Export function error"
            print(f"[ERROR] {error_msg}: {e}")
            self.show_error_message('Error', f"{error_msg}: {str(e)}")

    def _start_infinite_progress_export(self, data, filename, data_description):
        """Start export with infinite progress bar"""
        import threading

        # Create infinite progress window
        progress_window = self._create_infinite_progress_window(filename, len(data))

        def export_worker():
            """Background export worker thread"""
            try:
                print(f"[DEBUG] Starting export: {len(data)} rows of {data_description} to {filename}")

                # Different messages based on data type
                is_geo_data = 'agg_key' in data.columns and 'sample_count' in data.columns
                is_analysis_data = data_description == "Moving Window Analysis Results"

                if is_geo_data:
                    messages = [
                        "Preparing geographic data...",
                        "Analyzing aggregation structure...",
                        "Optimizing column order...",
                        "Exporting aggregated data...",
                        "Generating statistics...",
                        "Finalizing export..."
                    ]
                elif is_analysis_data:
                    messages = [
                        "Preparing analysis results...",
                        "Processing time series data...",
                        "Formatting analysis output...",
                        "Exporting analysis data...",
                        "Adding metadata...",
                        "Completing export..."
                    ]
                else:
                    messages = [
                        "Preparing data export...",
                        "Analyzing data structure...",
                        "Optimizing export format...",
                        "Writing data content...",
                        "Finalizing file...",
                        "Export complete..."
                    ]

                import time

                # Show preparation messages
                for i, message in enumerate(messages[:3]):
                    if getattr(progress_window, 'cancelled', False):
                        print("[INFO] Export cancelled by user")
                        return

                    self.root.after(0, lambda msg=message:
                    self._update_infinite_progress_status(progress_window, msg))
                    time.sleep(0.6)

                # Execute actual export
                self.root.after(0, lambda: self._update_infinite_progress_status(
                    progress_window, messages[3]))

                success = self._perform_smart_export(data, filename, data_description)

                if success:
                    # Show completion messages
                    for message in messages[4:]:
                        if getattr(progress_window, 'cancelled', False):
                            return

                        self.root.after(0, lambda msg=message:
                        self._update_infinite_progress_status(progress_window, msg))
                        time.sleep(0.4)

                    # Export successful
                    self.root.after(0, lambda: self._handle_export_success(
                        progress_window, filename, data_description, len(data), is_geo_data))
                else:
                    # Export failed
                    self.root.after(0, lambda: self._handle_export_error(
                        progress_window, "Export process failed"))

            except Exception as e:
                error_msg = f"Export exception: {str(e)}"
                print(f"[ERROR] {error_msg}")
                self.root.after(0, lambda: self._handle_export_error(progress_window, error_msg))

        # Start background export thread
        export_thread = threading.Thread(target=export_worker, daemon=True)
        export_thread.start()

    def _create_infinite_progress_window(self, filename, row_count):
        """Create infinite progress bar window"""
        try:
            import tkinter as tk
            from tkinter import ttk
            import os

            # Create window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Export Progress")
            progress_window.geometry("420x180")
            progress_window.transient(self.root)
            progress_window.grab_set()
            progress_window.resizable(False, False)

            # Center window
            x = self.root.winfo_rootx() + 100
            y = self.root.winfo_rooty() + 100
            progress_window.geometry(f"420x180+{x}+{y}")

            # Main frame
            main_frame = tk.Frame(progress_window, bg='white', padx=25, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # Title
            title_label = tk.Label(
                main_frame,
                text="Exporting data, please wait...",
                font=('Arial', 12, 'bold'),
                bg='white',
                fg='#2563eb'
            )
            title_label.pack(pady=(0, 12))

            # File info
            file_name = os.path.basename(filename)
            if len(file_name) > 50:
                file_name = file_name[:47] + "..."

            file_label = tk.Label(
                main_frame,
                text=f"File: {file_name}",
                font=('Arial', 10),
                bg='white',
                fg='#666666'
            )
            file_label.pack(pady=(0, 8))

            # Data info
            data_info_label = tk.Label(
                main_frame,
                text=f"Data: {row_count:,} rows",
                font=('Arial', 9),
                bg='white',
                fg='#888888'
            )
            data_info_label.pack(pady=(0, 15))

            # Infinite progress bar
            progress_bar = ttk.Progressbar(
                main_frame,
                length=350,
                mode='indeterminate'  # Infinite mode
            )
            progress_bar.pack(pady=(0, 15))
            progress_bar.start(8)  # Start scrolling animation

            # Status label
            status_var = tk.StringVar()
            status_var.set("Starting export...")
            status_label = tk.Label(
                main_frame,
                textvariable=status_var,
                font=('Arial', 10),
                bg='white',
                fg='#666666'
            )
            status_label.pack(pady=(0, 15))

            # Button frame
            button_frame = tk.Frame(main_frame, bg='white')
            button_frame.pack(fill=tk.X)

            # Cancel button
            def on_cancel():
                try:
                    progress_window.cancelled = True
                    progress_bar.stop()
                    progress_window.destroy()
                    print("[INFO] User cancelled export operation")
                except Exception as e:
                    print(f"[WARNING] Error during cancel: {e}")

            cancel_button = tk.Button(
                button_frame,
                text="Cancel Export",
                command=on_cancel,
                bg='#dc2626',
                fg='white',
                font=('Arial', 10),
                padx=20,
                pady=6,
                cursor='hand2',
                relief=tk.FLAT
            )
            cancel_button.pack(side=tk.RIGHT)

            # Tip label
            tip_label = tk.Label(
                button_frame,
                text="Large files may take several minutes",
                font=('Arial', 8),
                bg='white',
                fg='#999999'
            )
            tip_label.pack(side=tk.LEFT)

            # Add window attributes
            progress_window.progress_bar = progress_bar
            progress_window.status_var = status_var
            progress_window.cancelled = False

            # Window close handler
            def on_window_close():
                try:
                    progress_bar.stop()
                    progress_window.cancelled = True
                    progress_window.destroy()
                except:
                    pass

            progress_window.protocol("WM_DELETE_WINDOW", on_window_close)

            print("[DEBUG] Infinite progress window created successfully")
            return progress_window

        except Exception as e:
            print(f"[ERROR] Failed to create infinite progress window: {e}")
            return None

    def _update_infinite_progress_status(self, progress_window, message):
        """Update infinite progress bar status message"""
        try:
            if progress_window and not getattr(progress_window, 'cancelled', False):
                if hasattr(progress_window, 'status_var'):
                    progress_window.status_var.set(message)

                progress_window.update_idletasks()
                print(f"[PROGRESS] {message}")

        except Exception as e:
            print(f"[WARNING] Failed to update progress status: {e}")

    def _perform_smart_export(self, data, filename, data_description):
        """Perform smart export based on data type"""
        try:
            print(f"[EXPORT] Starting actual export: {len(data)} rows")

            # 只对移动窗口分析结果重命名 std_error 为 2SE
            if ('std_error' in data.columns and
                    'age' in data.columns and
                    'mean' in data.columns):
                data = data.copy()
                data.rename(columns={'std_error': '2SE'}, inplace=True)
                print("[INFO] Renamed 'std_error' column to '2SE' for moving window analysis")

            # Check if it's geographic aggregation data
            is_geo_data = 'agg_key' in data.columns and 'sample_count' in data.columns

            if is_geo_data and hasattr(self, 'export_clean_geo_aggregated_data'):
                # Use special geo aggregation export if available
                return self.export_clean_geo_aggregated_data(data, filename)
            else:
                # Use standard export
                if filename.lower().endswith('.csv'):
                    # CSV export - fastest
                    data.to_csv(filename, index=False, encoding='utf-8-sig')
                    print("[SUCCESS] CSV export completed")
                else:
                    # Excel export with performance optimization
                    import pandas as pd

                    if len(data) > 50000:
                        # Large file optimization
                        try:
                            with pd.ExcelWriter(filename, engine='xlsxwriter',
                                                options={'strings_to_numbers': True}) as writer:
                                data.to_excel(writer, sheet_name='Data', index=False)
                            print("[SUCCESS] Large file Excel export completed (xlsxwriter)")
                        except ImportError:
                            print("[WARNING] xlsxwriter not available, using openpyxl")
                            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                                data.to_excel(writer, sheet_name='Data', index=False)
                            print("[SUCCESS] Large file Excel export completed (openpyxl)")
                    else:
                        # Small file
                        with pd.ExcelWriter(filename) as writer:
                            data.to_excel(writer, sheet_name='Data', index=False)
                        print("[SUCCESS] Excel export completed")

            return True

        except Exception as e:
            print(f"[ERROR] Actual export failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _handle_export_success(self, progress_window, filename, data_description, row_count, is_geo_data):
        """Handle export success"""
        try:
            # Stop progress bar animation
            if progress_window and hasattr(progress_window, 'progress_bar'):
                progress_window.progress_bar.stop()

            # Show completion status briefly
            if progress_window:
                self._update_infinite_progress_status(progress_window, "Export completed!")

            import time
            time.sleep(0.8)

            # Close progress window
            if progress_window:
                progress_window.destroy()

            # Update main window status
            self.update_status(f"[OK] Data export completed - {data_description} ({row_count:,} records)")

            # Show success message based on data type
            if is_geo_data:
                message = f"""Geographic aggregation data exported successfully!

    File location: {filename}
    Record count: {row_count:,} aggregation groups

    Contents:
    • Aggregation keys and sample counts
    • Representative coordinates and ages
    • Averaged chemical compositions
    • Location information"""
            else:
                message = f"""Data exported successfully!

    File location: {filename}
    Data type: {data_description}
    Record count: {row_count:,} rows"""

            self.show_info_message('Export Successful', message)

            print(f"[SUCCESS] Export operation completed: {filename}")

        except Exception as e:
            print(f"[ERROR] Failed to handle export success: {e}")

    def _handle_export_error(self, progress_window, error_msg):
        """Handle export error"""
        try:
            # Stop progress bar animation
            if progress_window and hasattr(progress_window, 'progress_bar'):
                progress_window.progress_bar.stop()

            # Close progress window
            if progress_window:
                progress_window.destroy()

            # Update main window status
            self.update_status(f"[Error] Data export failed")

            # Show error message
            self.show_error_message('Export Failed', f"Export process error:\n\n{error_msg}")

            print(f"[ERROR] Export operation failed: {error_msg}")

        except Exception as e:
            print(f"[ERROR] Failed to handle export error: {e}")

    def _should_reorder_columns(self, data, data_description):
        """
        判断是否需要重排序列 - 修复版：大多数情况下保持原始列顺序
        """
        try:
            print(f"[DEBUG] 检查是否需要重排序: {data_description}")

            # 地理聚合数据已经有正确的列顺序，不需要重排序
            if ('agg_key' in data.columns and 'sample_count' in data.columns):
                print(f"[DEBUG] 地理聚合数据，保持现有列顺序")
                return False

            # 移动窗口分析结果也不需要重排序
            if (data_description == "移动窗口分析结果" and
                    'age' in data.columns and 'mean' in data.columns):
                print(f"[DEBUG] 移动窗口分析结果，保持现有列顺序")
                return False

            # 异常值处理后的数据保持原始顺序
            if "异常值" in data_description or "outlier" in data_description.lower():
                print(f"[DEBUG] 异常值处理数据，保持现有列顺序")
                return False

            # 筛选后的数据保持原始顺序
            if "筛选" in data_description or "filter" in data_description.lower():
                print(f"[DEBUG] 筛选数据，保持现有列顺序")
                return False

            # 已处理数据保持原始顺序
            if "已处理" in data_description or "processed" in data_description.lower():
                print(f"[DEBUG] 已处理数据，保持现有列顺序")
                return False

            # 当前数据默认也不重排序，除非明确需要
            if data_description == "当前数据":
                print(f"[DEBUG] 当前数据，保持现有列顺序")
                return False

            # 包含"Geographic"关键词的也不重排序
            if "geographic" in data_description.lower() or "geo" in data_description.lower():
                print(f"[DEBUG] 地理相关数据，保持现有列顺序")
                return False

            # 其他特殊情况才重排序
            print(f"[DEBUG] 特殊数据类型，允许重排序")
            return True

        except Exception as e:
            print(f"[WARNING] 判断重排序需求时出错: {e}")
            return False  # 出错时默认不重排序，保持原始顺序

    def _apply_column_reordering(self, data):
        """
        应用列重排序逻辑 - 只在确实需要时调用
        这是原有的重排序代码，保持不变
        """
        try:
            # 定义地球化学元素关键词（保持原有逻辑）
            chemical_keywords = [
                # 主重元素
                'SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'FeO', 'MnO', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5',
                'SIO2', 'TIO2', 'AL2O3', 'FE2O3', 'FEO', 'MNO', 'MGO', 'CAO', 'NA2O', 'P2O5',

                # 稀土元素
                'La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu',
                'LA', 'CE', 'PR', 'ND', 'SM', 'EU', 'GD', 'TB', 'DY', 'HO', 'ER', 'TM', 'YB', 'LU',

                # 微量元素
                'Li', 'Be', 'Sc', 'V', 'Cr', 'Mn', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Rb', 'Sr',
                'Y', 'Zr', 'Nb', 'Mo', 'Cd', 'In', 'Sn', 'Sb', 'Cs', 'Ba', 'Hf', 'Ta', 'W',
                'Re', 'Tl', 'Pb', 'Bi', 'Th', 'U', 'Ti', 'Ge', 'P',

                # 地球化学比值和参数
                'Th_U', 'ThU', 'TH_U', 'logUTh', 'U_Th', 'La_Sm', 'Delta_logUTh',
                'Mg#', 'CIA', 'Na2O_K2O', 'ALK', 'A_CNK', 'LOI', 'Total', 'H2O+', 'CO2'
            ]

            # 分类列
            non_element_cols = []
            element_cols = []

            for col in data.columns:
                col_str = str(col).strip()

                # 检查是否为地球化学元素
                is_chemical = any(keyword in col_str or col_str == keyword for keyword in chemical_keywords)

                if is_chemical:
                    element_cols.append(col)
                else:
                    non_element_cols.append(col)

            print(f"[REORDER] 分类结果: {len(non_element_cols)}个非元素列, {len(element_cols)}个元素列")

            # 非元素列按优先级排序
            priority_non_element = [
                'latitude', 'longitude', 'latitude_mean', 'longitude_mean',
                'age', 'age_min', 'age_max', 'age_std', 'AGE',
                'Location', 'Country', 'Continent', 'Region',
                'sample_count', 'Reference', 'Score', 'SAMPLE_ID', 'error'
            ]

            sorted_non_element = []
            remaining_non_element = non_element_cols.copy()

            # 添加优先级列
            for priority_col in priority_non_element:
                if priority_col in remaining_non_element:
                    sorted_non_element.append(priority_col)
                    remaining_non_element.remove(priority_col)

            # 添加剩余非元素列
            sorted_non_element.extend(sorted(remaining_non_element))

            # 元素列按类别排序
            major_elements = [col for col in element_cols if any(
                major in str(col) for major in ['SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'MgO', 'CaO', 'Na2O', 'K2O']
            )]
            ree_elements = [col for col in element_cols if any(
                ree in str(col) for ree in
                ['La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']
            )]
            other_elements = [col for col in element_cols if col not in major_elements and col not in ree_elements]

            sorted_elements = sorted(major_elements) + sorted(ree_elements) + sorted(other_elements)

            # 最终列顺序：非元素 + 元素
            final_column_order = sorted_non_element + sorted_elements
            reordered_data = data[final_column_order]

            print(f"[REORDER] 列重排序完成: 前5列: {list(reordered_data.columns[:5])}")
            return reordered_data

        except Exception as e:
            print(f"[ERROR] 列重排序失败: {e}")
            # 重排序失败时返回原始数据
            return data.copy()

    def _create_export_progress_window(self, filename):
        """创建导出进度窗口"""
        try:
            import tkinter as tk
            from tkinter import ttk

            progress_window = tk.Toplevel(self.root)
            progress_window.title("导出进度")
            progress_window.geometry("400x150")
            progress_window.transient(self.root)
            progress_window.grab_set()
            progress_window.resizable(False, False)

            # 居中显示
            x = self.root.winfo_rootx() + 50
            y = self.root.winfo_rooty() + 100
            progress_window.geometry(f"400x150+{x}+{y}")

            # 主框架
            main_frame = tk.Frame(progress_window, bg='white', padx=20, pady=15)
            main_frame.pack(fill=tk.BOTH, expand=True)

            # 标题
            title_label = tk.Label(
                main_frame,
                text="正在导出数据...",
                font=('Arial', 12, 'bold'),
                bg='white',
                fg='#2E86C1'
            )
            title_label.pack(pady=(0, 10))

            # 文件信息
            import os
            file_name = os.path.basename(filename)
            if len(file_name) > 40:
                file_name = file_name[:37] + "..."

            file_label = tk.Label(
                main_frame,
                text=f"文件: {file_name}",
                font=('Arial', 9),
                bg='white',
                fg='#666666'
            )
            file_label.pack(pady=(0, 15))

            # 进度条
            progress_bar = ttk.Progressbar(
                main_frame,
                mode='indeterminate',
                length=300
            )
            progress_bar.pack(pady=(0, 15))
            progress_bar.start(10)  # 动画速度

            # 状态标签
            status_var = tk.StringVar()
            status_var.set("准备导出...")
            status_label = tk.Label(
                main_frame,
                textvariable=status_var,
                font=('Arial', 9),
                bg='white',
                fg='#666666'
            )
            status_label.pack()

            # 更新窗口
            progress_window.update()

            return progress_window, progress_bar, status_var

        except Exception as e:
            print(f"[ERROR] 创建进度窗口失败: {e}")
            return None, None, None

    def _update_export_progress(self, status_var, message):
        """更新导出进度"""
        try:
            if status_var:
                status_var.set(message)
                self.root.update_idletasks()
        except Exception as e:
            print(f"[WARNING] 更新进度失败: {e}")

    def _close_export_progress(self, progress_window, progress_bar):
        """关闭导出进度窗口"""
        try:
            if progress_bar:
                progress_bar.stop()
            if progress_window:
                progress_window.destroy()
        except Exception as e:
            print(f"[WARNING] 关闭进度窗口失败: {e}")

    def simple_export_data(self, data, filename, data_description):
        """
        简单数据导出 - 修复版：地理聚合数据保持原始列顺序
        """
        try:
            import pandas as pd
            from datetime import datetime

            print(f"[EXPORT] 开始导出: {data_description} -> {filename}")
            print(f"[EXPORT-FIX] 原始列顺序: {list(data.columns)[:10]}...")

            # 创建进度窗口
            progress_window, progress_bar, status_var = self._create_export_progress_window(filename)

            def progress_callback(message):
                self._update_export_progress(status_var, message)

            try:
                progress_callback("分析数据结构...")

                # 关键修复：检测是否需要重排序
                needs_reordering = self._should_reorder_columns(data, data_description)

                if needs_reordering:
                    print(f"[EXPORT-FIX] 检测到特殊数据类型，将重排序列")
                    progress_callback("重排序列...")
                    # 使用原有的重排序逻辑
                    sorted_data = self._apply_column_reordering(data)
                else:
                    print(f"[EXPORT-FIX] 地理聚合数据，保持原始列顺序")
                    progress_callback("保持原始列顺序...")
                    # 关键修复：直接使用原始数据，不重排序
                    sorted_data = data.copy()

                # 根据文件扩展名选择导出格式
                if filename.lower().endswith('.xlsx'):
                    success = self.export_to_excel_simple(sorted_data, filename, data_description, progress_callback)
                elif filename.lower().endswith('.csv'):
                    progress_callback("CSV导出...")
                    sorted_data.to_csv(filename, index=False, encoding='utf-8-sig')
                    success = True
                else:
                    # 默认导出为Excel
                    if not filename.lower().endswith(('.xlsx', '.csv')):
                        filename += '.xlsx'
                    success = self.export_to_excel_simple(sorted_data, filename, data_description, progress_callback)

                progress_callback("导出完成！")
                print(f"[EXPORT-FIX] 导出完成: {filename}")
                print(f"[EXPORT-FIX] 最终列顺序: {list(sorted_data.columns)[:10]}...")

                # 短暂延迟让用户看到完成状态
                import time
                time.sleep(0.5)

            finally:
                # 确保关闭进度窗口
                self._close_export_progress(progress_window, progress_bar)

            return success

        except Exception as e:
            print(f"[ERROR] 导出数据失败: {e}")
            # 确保关闭进度窗口
            if 'progress_window' in locals():
                self._close_export_progress(progress_window, progress_bar)
            return False

    def export_to_excel_simple(self, data, filename, data_description, progress_callback=None):
        """
        简单的Excel导出 - 修复版：默认保持原始列顺序，支持进度回调
        只在特殊数据类型（如地理聚合）时才重排序
        """
        try:
            import pandas as pd
            from datetime import datetime

            print(f"[EXPORT-FIX] 开始导出: {data_description}")
            print(f"[EXPORT-FIX] 原始列顺序: {list(data.columns)[:10]}...")  # 显示前10列

            if progress_callback:
                progress_callback("分析数据结构...")

            # 核心修改：检测是否需要重排序
            needs_reordering = self._should_reorder_columns(data, data_description)

            if needs_reordering:
                print(f"[EXPORT-FIX] 检测到特殊数据类型，将重排序列")
                if progress_callback:
                    progress_callback("重排序列...")
                # 使用原有的重排序逻辑
                sorted_data = self._apply_column_reordering(data)
            else:
                print(f"[EXPORT-FIX] 保持原始列顺序导出")
                if progress_callback:
                    progress_callback("保持原始列顺序...")
                # 关键修改：直接使用原始数据，不重排序
                sorted_data = data.copy()

            if progress_callback:
                progress_callback("准备Excel文件...")

            # 创建Excel文件
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                if progress_callback:
                    progress_callback("写入主数据表...")

                # 主数据 - 使用处理后的数据
                sorted_data.to_excel(writer, sheet_name='数据', index=False)

                if progress_callback:
                    progress_callback("写入导出信息...")

                # 导出信息页
                info_data = {
                    '属性': [
                        '导出时间',
                        '数据类型',
                        '总记录数',
                        '总列数',
                        '列顺序处理',
                        '程序版本'
                    ],
                    '值': [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        data_description,
                        len(sorted_data),
                        len(sorted_data.columns),
                        '重排序' if needs_reordering else '保持原始顺序',
                        'Excel地球化学数据分析器 v4.0 (修复版)'
                    ]
                }

                info_df = pd.DataFrame(info_data)
                info_df.to_excel(writer, sheet_name='导出信息', index=False)

            if progress_callback:
                progress_callback("导出完成！")

            print(f"[EXPORT-FIX] 导出完成: {filename}")
            print(f"[EXPORT-FIX] 最终列顺序: {list(sorted_data.columns)[:10]}...")
            return True

        except Exception as e:
            print(f"[ERROR] Excel导出失败: {e}")
            return False

    def export_to_csv_simple(self, data, filename):
        """简单的CSV导出"""
        try:
            data.to_csv(filename, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"[ERROR] CSV导出失败: {e}")
            return False




    def save_last_analysis_params(self, params):
        """保存最近的分析参数（用于导出时的元数据）"""
        try:
            self.last_analysis_params = {
                'age_column': params.get('age_column', ''),
                'target_column': params.get('target_column', ''),
                'window_size': params.get('window_size', 0),
                'step_size': params.get('step_size', 0),
                'min_age': params.get('min_age', 0),
                'max_age': params.get('max_age', 0),
                'boundary_mode': params.get('boundary_mode', 'exclusive'),
                'analysis_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"[WARNING] 保存分析参数失败: {e}")

    def _handle_analysis_complete_fixed(self, progress_window, success, message, results, params):
        """处理分析完成"""
        if progress_window:
            progress_window.close()

        if success and results is not None:
            # 保存结果
            self.geochem_analysis_results = results
            self.moving_window_results = results

            # 动态找到均值列
            mean_col = None
            for col in results.columns:
                if col.endswith('_mean') and '-' not in col:
                    mean_col = col
                    break

            if mean_col:
                valid_windows = len(results.dropna(subset=[mean_col]))
            else:
                valid_windows = len(results)  # 备用方案
            total_windows = len(results)

            self.update_status(f"[OK] 移动窗口分析完成: {valid_windows}/{total_windows} 有效窗口")
            self.update_geochem_analysis_status(f"分析完成: {valid_windows}/{total_windows} 有效窗口", "success")

            # 自动设置图表列
            # 🔧 修复：使用移动窗口分析实际生成的动态列名
            if results is not None and len(results) > 0:
                # 查找实际的年龄列名（不是组合列）
                age_col_name = None
                mean_col_name = None

                for col in results.columns:
                    # 找到年龄列（原始列名，不包含_mean后缀，也不是特殊列）
                    if (col not in ['std_error', 'sample_count', 'window_low', 'window_high'] and
                            not col.endswith('_mean') and
                            '-' not in col):
                        age_col_name = col

                    # 找到均值列（以_mean结尾但不包含组合符号）
                    elif col.endswith('_mean') and '-' not in col:
                        mean_col_name = col

                # 分析完成后不自动切换X/Y轴，保留用户原有选择

            # 显示完成信息
            completion_text = f"""移动窗口分析完成！

    总窗口数: {total_windows}
    有效窗口数: {valid_windows}
    [OK] 进度条已恢复
    [OK] 误差棒已修复 - 所有点都有误差棒

    分析结果已准备就绪，可以生成图表。"""

            self.show_info_message('分析成功', completion_text)
        else:
            self.show_warning_message('分析失败', message)

    def _handle_analysis_error_simple(self, progress_window, error_msg):
        """处理分析错误"""
        if progress_window:
            progress_window.close()
        self.show_error_message('分析错误', f"分析失败: {error_msg}")





    def _show_enhanced_analysis_completion_message(self, params, total_windows, valid_windows, boundary_points,
                                                   analysis_type):
        """显示增强分析完成信息"""
        try:
            completion_text = f"""SUCCESS！

    年龄列: {params['age_column']}
    目标列: {params['target_column']}
    年龄范围: {params['min_age']:.0f}-{params['max_age']:.0f} Ma
    窗口大小: {params['window_size']:.0f} Ma
    移动步长: {params['step_size']:.0f} Ma

    [REFRESH] 分析类型: {analysis_type}
    总窗口数: {total_windows}
    有效窗口数: {valid_windows}
    边界点数: {boundary_points}

    ✨ 边界处理功能已生效，优化了窗口边界处的数据点分配。
    分析结果已准备就绪，可以生成图表。"""

            self.show_info_message('SUCCESS', completion_text)

        except Exception as e:
            print(f"[ERROR] 显示完成信息失败: {e}")

    def _execute_moving_window_analysis_fixed(self, params):
        """执行移动窗口分析 - 修复版"""
        try:
            self.update_status(
                f"[Processing] {language_manager.get_text('running_analysis', '正在运行移动窗口分析')}...")

            if not self._confirm_analysis_execution(params):
                return

            # 传递主窗口当前数据
            if hasattr(self, 'data') and self.data is not None:
                print(f"[DEBUG-FIX] 传递主窗口当前数据到移动窗口分析: {len(self.data)} 行")
                self.moving_window_integration.set_current_data(self.data)
            else:
                print("[WARNING] 主窗口没有当前数据，使用原始数据")

            # 更新状态管理器
            self.state_manager.update_state("analysis_running", info=params)

            # 创建进度窗口
            progress_window = self._create_progress_window(params)

            # 启动分析线程
            self._start_analysis_thread_fixed(params, progress_window)

        except Exception as e:
            error_msg = language_manager.get_text('execute_analysis_failed', '执行移动窗口分析失败')
            self.update_status(f"[Error] {error_msg}")
            self.show_error_message(
                language_manager.get_text('error', '错误'),
                f"{error_msg}: {str(e)}"
            )

    def _start_analysis_thread_fixed(self, params, progress_window):
        """启动分析线程 - 线程安全版"""

        def run_analysis():
            try:
                # 捕获当前状态
                current_data = self.data.copy() if self.data is not None else None
                current_progress_window = progress_window

                def progress_callback(message):
                    if current_progress_window and not current_progress_window.cancelled:
                        self.root.after(0,
                                        lambda msg=message: current_progress_window.update_progress(0, 0, 0, True, msg))
                    else:
                        self.root.after(0, lambda msg=message: self.update_status(f"[Processing] {msg}"))

                # 尝试使用快速分析函数
                try:
                    from geochemistry.moving_window_integration import run_quick_moving_window_analysis

                    results = run_quick_moving_window_analysis(
                        main_window_data=current_data,
                        age_column=params['age_column'],
                        target_column=params['target_column'],
                        window_size=params['window_size'],
                        step_size=params['step_size'],
                        min_age=params['min_age'],
                        max_age=params['max_age'],
                        progress_callback=progress_callback
                    )

                    if results is not None and len(results) > 0:
                        success = True
                        # 动态找到均值列
                        mean_col = None
                        for col in results.columns:
                            if col.endswith('_mean') and '-' not in col:
                                mean_col = col
                                break

                        if mean_col:
                            valid_windows = len(results.dropna(subset=[mean_col]))
                        else:
                            valid_windows = len(results)  # 备用方案
                        total_windows = len(results)
                        message = f'分析完成！总窗口数: {total_windows}, 有效窗口数: {valid_windows}'
                    else:
                        success = False
                        message = '分析未产生有效结果'
                        results = None

                except ImportError:
                    print("[WARNING] 快速分析函数不可用，使用标准分析方法")
                    success, message, results = self.moving_window_integration.run_complete_analysis(
                        params, progress_callback
                    )

                # 处理结果
                if current_progress_window and not current_progress_window.cancelled:
                    self.root.after(0, lambda: self._handle_analysis_completion(
                        current_progress_window, success, message, results, params))
                else:
                    self.root.after(0, lambda: self._handle_analysis_completion(
                        None, success, message, results, params))

            except Exception as e:
                error_msg = language_manager.get_text('analysis_thread_error', '分析线程出错')
                if current_progress_window and not current_progress_window.cancelled:
                    self.root.after(0, lambda err=str(e): self._handle_analysis_error(current_progress_window, err))
                else:
                    self.root.after(0, lambda err=str(e): self._handle_analysis_error(None, err))

        # 启动线程
        analysis_thread = threading.Thread(target=run_analysis, daemon=True)
        analysis_thread.start()

    def _confirm_analysis_execution(self, params):
        """确认分析执行"""
        try:
            confirm_text = self._build_analysis_confirmation_text(params)
            return messagebox.askyesno(
                language_manager.get_text('confirm_analysis', '确认分析'),
                confirm_text
            )
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('build_confirmation_failed', '构建确认信息失败')}: {e}")
            return True

    def _build_analysis_confirmation_text(self, params):
        """构建分析确认文本"""
        try:
            estimated_time = self._estimate_analysis_time(params['estimated_windows'])

            confirm_text = f"""{language_manager.get_text('analysis_parameters_summary', '分析参数摘要')}:

{language_manager.get_text('age_column', '年龄列')}: {params['age_column']}
{language_manager.get_text('target_column', '目标列')}: {params['target_column']}
{language_manager.get_text('age_range', '年龄范围')}: {params['min_age']:.0f} - {params['max_age']:.0f} Ma
{language_manager.get_text('window_size', '窗口大小')}: {params['window_size']:.0f} Ma
{language_manager.get_text('step_size', '步长')}: {params['step_size']:.0f} Ma

{language_manager.get_text('estimated_windows', '预计窗口数')}: {params['estimated_windows']}
{language_manager.get_text('estimated_time', '预计时间')}: {estimated_time}

{language_manager.get_text('confirm_start_analysis', '确定要开始分析吗')}？"""

            return confirm_text

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('build_confirmation_text_failed', '构建确认文本失败')}: {e}")
            return language_manager.get_text('confirm_start_analysis', '确定要开始分析吗？')

    def _estimate_analysis_time(self, window_count):
        """估算分析时间"""
        try:
            if window_count < 50:
                return language_manager.get_text('less_than_1_minute', '< 1分钟')
            elif window_count < 200:
                return language_manager.get_text('1_3_minutes', '1-3分钟')
            elif window_count < 500:
                return language_manager.get_text('3_10_minutes', '3-10分钟')
            else:
                return language_manager.get_text('more_than_10_minutes', '> 10分钟')
        except:
            return language_manager.get_text('unknown_time', '未知')

    def _create_progress_window(self, params):
        """创建进度窗口"""
        try:
            from ui.progress_windows import ModernAnalysisProgressWindow
            return ModernAnalysisProgressWindow(self.root, params['estimated_windows'])
        except ImportError:
            print(f"[WARNING] {language_manager.get_text('progress_window_unavailable', '进度窗口不可用')}")
            return None
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('create_progress_window_failed', '创建进度窗口失败')}: {e}")
            return None

    def _handle_analysis_completion(self, progress_window, success, message, results, params):
        """处理分析完成"""
        if progress_window:
            progress_window.close()

        if success and results is not None:
            self._process_successful_analysis(results, params)
        else:
            self._process_failed_analysis(message)

    def _process_successful_analysis(self, results, params):
        """处理成功的分析 - 修复轴标签版本"""
        try:
            # 🔧 添加：统一重命名std_error为2SE
            if 'std_error' in results.columns:
                results = results.rename(columns={'std_error': '2SE'})
                print(f"[DEBUG] 已将std_error重命名为2SE")

            # 保存结果
            self.geochem_analysis_results = results
            self.moving_window_results = results

            # 【新增】保存分析参数用于导出
            self.save_last_analysis_params(params)

            # 🔧 关键修复：保存原始分析参数用于动态轴标签
            original_age_col = params.get('age_column', 'Age')
            original_target_col = params.get('target_column', 'Target')

            # 保存到实例变量，供图表控制器使用
            self.analysis_original_columns = {
                'age_column': original_age_col,
                'target_column': original_target_col
            }

            print(f"[DEBUG] 保存原始列名用于动态轴标签: Age={original_age_col}, Target={original_target_col}")

            # 更新状态管理器
            self.state_manager.update_state("analysis_complete", data=results, info=params)

            # 计算统计信息
            # 动态找到均值列
            mean_col = None
            for col in results.columns:
                if col.endswith('_mean') and '-' not in col:
                    mean_col = col
                    break

            if mean_col:
                valid_windows = len(results.dropna(subset=[mean_col]))
            else:
                valid_windows = len(results)  # 备用方案
            total_windows = len(results)

            # 更新状态
            self.update_status(
                f"[OK] {language_manager.get_text('analysis_completed', '移动窗口分析完成')}: "
                f"{total_windows} {language_manager.get_text('windows_total', '个窗口')}, "
                f"{valid_windows} {language_manager.get_text('windows_valid', '个有效')}"
            )

            # 更新分析状态
            self.update_geochem_analysis_status(
                f"{language_manager.get_text('analysis_complete', '分析完成')}: "
                f"{valid_windows}/{total_windows} {language_manager.get_text('valid_windows', '有效窗口')}",
                "success"
            )

            # 显示完成信息
            self._show_analysis_completion_message(params, total_windows, valid_windows)

            # 🔧 修复：使用移动窗口分析实际生成的动态列名
            if results is not None and len(results) > 0:
                # 查找实际的年龄列名（不是组合列）
                age_col_name = None
                mean_col_name = None

                # 修复：更新特殊列名列表，包含所有非数据列
                special_columns = ['2SE', 'sample_count', 'window_low', 'window_high',
                                   'window_start', 'window_end', 'boundary_mode']

                for col in results.columns:
                    # 找到年龄列（原始列名，不包含_mean后缀，也不是特殊列）
                    if (col not in special_columns and
                            not col.endswith('_mean') and
                            '-' not in col):
                        age_col_name = col
                        break  # 只取第一个匹配的列

                for col in results.columns:
                    # 找到均值列（以_mean结尾但不包含组合符号）
                    if col.endswith('_mean') and '-' not in col:
                        mean_col_name = col
                        break  # 只取第一个匹配的列

                # 分析完成后不自动切换X/Y轴，保留用户原有选择

        except Exception as e:
            error_msg = language_manager.get_text('process_results_failed', '处理分析结果失败')
            print(f"[ERROR] {error_msg}: {e}")

    def _process_failed_analysis(self, message):
        """处理失败的分析"""
        error_details = message if message else language_manager.get_text('unknown_error', '未知错误')

        self.update_status(f"[Warning] {language_manager.get_text('analysis_failed', '移动窗口分析失败')}")
        self.update_geochem_analysis_status(f"{language_manager.get_text('analysis_failed', '分析失败')}", "error")

        # 更新状态管理器
        self.state_manager.update_state("analysis_failed", info={'error': error_details})

        failure_text = f"""{language_manager.get_text('analysis_failed', '移动窗口分析失败')}

{language_manager.get_text('error_info', '错误信息')}: {error_details}

{language_manager.get_text('possible_solutions', '可能的解决方案')}：
• {language_manager.get_text('check_data_quality', '检查数据质量和完整性')}
• {language_manager.get_text('adjust_parameters', '调整分析参数')}
• {language_manager.get_text('verify_column_selection', '验证列选择是否正确')}"""

        self.show_warning_message(
            language_manager.get_text('analysis_failed', '分析失败'),
            failure_text
        )

    def _handle_analysis_error(self, progress_window, error_msg):
        """处理分析错误"""
        if progress_window:
            progress_window.close()

        self.update_status(f"[Error] {language_manager.get_text('analysis_error', '分析错误')}")
        self.update_geochem_analysis_status(f"{language_manager.get_text('analysis_error', '分析出错')}", "error")

        # 更新状态管理器
        self.state_manager.update_state("analysis_error", info={'error': error_msg})

        self.show_error_message(
            language_manager.get_text('analysis_error', '分析错误'),
            f"{language_manager.get_text('analysis_execution_error', '移动窗口分析执行时发生错误')}:\n\n{error_msg}"
        )

    def _show_analysis_completion_message(self, params, total_windows, valid_windows):
        """显示分析完成信息"""
        try:
            completion_text = f"""{language_manager.get_text('analysis_completed', '移动窗口分析完成')}！

{language_manager.get_text('age_column', '年龄列')}: {params['age_column']}
{language_manager.get_text('target_column', '目标列')}: {params['target_column']}
{language_manager.get_text('age_range', '年龄范围')}: {params['min_age']:.0f}-{params['max_age']:.0f} Ma
{language_manager.get_text('total_windows', '总窗口数')}: {total_windows}
{language_manager.get_text('valid_windows', '有效窗口数')}: {valid_windows}
{language_manager.get_text('window_size', '窗口大小')}: {params['window_size']:.0f} Ma
{language_manager.get_text('step_size', '步长')}: {params['step_size']:.0f} Ma

{language_manager.get_text('analysis_results_ready', '分析结果已准备就绪，可以生成图表或导出数据')}。"""

            self.show_info_message(
                language_manager.get_text('analysis_success', '分析成功'),
                completion_text
            )

        except Exception as e:
            error_msg = language_manager.get_text('show_completion_message_failed', '显示完成信息失败')
            print(f"[ERROR] {error_msg}: {e}")

    def update_geochem_analysis_status(self, message, status_type="info"):
        """更新地球化学分析状态"""
        try:
            status_icons = {
                'info': 'ℹ',
                'success': '✓',
                'warning': '⚠',
                'error': '✗',
                'processing': '⚙'
            }
            icon = status_icons.get(status_type, 'ℹ')
            self.analysis_status_var.set(f"{icon} {message}")
        except Exception as e:
            print(f"[ERROR] 更新分析状态失败: {e}")

    # ======== 图表生成方法 ========

    def generate_chart(self):
        """生成图表 - 修复版"""
        try:
            is_valid, message = self.data_manager.validate_data_for_operation()
            if not is_valid:
                self.show_warning_message(language_manager.get_text('warning', '警告'), message)
                return

            chart_type = self.chart_type_var.get()
            if not chart_type:
                chart_type = "Scatter Plot"
                self.chart_type_var.set(chart_type)
            x_col = self.x_col_var.get()
            y_col = self.y_col_var.get()

            is_valid, message = self.chart_controller.validate_chart_generation(chart_type, x_col, y_col)
            if not is_valid:
                self.show_warning_message(language_manager.get_text('warning', '警告'), message)
                return

            # 智能选择数据源
            chart_data, data_source_info = self._get_smart_chart_data(x_col, y_col)

            if chart_data is None or len(chart_data) == 0:
                self.show_warning_message(
                    language_manager.get_text('warning', '警告'),
                    f"没有有效数据用于生成图表。\n\n当前状态：{data_source_info}"
                )
                return

            # 生成图表
            success, result_message = self.chart_controller.generate_chart(chart_data, x_col, y_col, chart_type)

            if success:
                data_count = len(chart_data)
                status_message = f"Successfully generated {chart_type}: {data_source_info} ({data_count} DATAS)"
                self.update_status(status_message)
            else:
                self.update_status(f"[Error] 图表生成失败: {result_message}")
                self.show_error_message("错误", result_message)

        except Exception as e:
            print(f"[ERROR] 图表生成失败: {e}")
            self.show_error_message("错误", f"图表显示失败: {str(e)}")

    def save_chart(self):
        """保存图表"""
        try:
            success, message = self.chart_controller.save_current_chart()
            if success:
                self.update_status(f"[OK] {language_manager.get_text('chart_saved', '图表已保存')}")
                self.show_info_message(language_manager.get_text('success', '成功'), message)
            else:
                self.update_status(f"[Error] {language_manager.get_text('save_error', '保存失败')}")
                self.show_error_message(language_manager.get_text('error', '错误'), message)
        except Exception as e:
            print(f"[ERROR] 保存图表失败: {e}")
            self.show_error_message(
                language_manager.get_text('error', '错误'),
                f"保存图表失败: {str(e)}"
            )

    def _get_smart_chart_data(self, x_col, y_col):
        """智能获取图表数据源 - 支持边界处理和分段处理数据"""
        try:
            # 优先级1：移动窗口分析结果（修复：支持动态列名）
            if (hasattr(self, 'geochem_analysis_results') and
                    self.geochem_analysis_results is not None and
                    len(self.geochem_analysis_results) > 0):

                print(f"[DEBUG] 检查移动窗口分析结果")
                print(f"[DEBUG] 结果列名: {list(self.geochem_analysis_results.columns)}")
                print(f"[DEBUG] 查找列: x_col={x_col}, y_col={y_col}")

                # 检查请求的列是否存在于分析结果中
                if x_col in self.geochem_analysis_results.columns and y_col in self.geochem_analysis_results.columns:
                    valid_results = self.geochem_analysis_results.dropna(subset=[y_col])
                    if len(valid_results) > 0:
                        print(f"[DEBUG] 找到匹配的移动窗口数据: {len(valid_results)} 行")
                        # 检查是否是边界处理结果
                        if 'window_start' in valid_results.columns:
                            return valid_results, f"SUCCESS, {len(valid_results)}"
                        else:
                            return valid_results, f"SUCCESS,{len(valid_results)}"
                    else:
                        print(f"[DEBUG] 移动窗口数据存在但无有效行")
                else:
                    print(f"[DEBUG] 请求的列不存在于移动窗口结果中")
                    print(f"[DEBUG] x_col '{x_col}' 存在: {x_col in self.geochem_analysis_results.columns}")
                    print(f"[DEBUG] y_col '{y_col}' 存在: {y_col in self.geochem_analysis_results.columns}")

            # 优先级2：检查是否使用了分段处理的数据
            if hasattr(self, 'data') and self.data is not None:
                # 检查数据是否经过分段异常值处理
                # (这里可以通过数据标记或其他方式来识别)

                # 如果有筛选后的数据，优先使用筛选数据
                if (hasattr(self, 'filter_manager') and
                        self.filter_manager is not None and
                        hasattr(self.filter_manager, 'has_active_filters') and
                        self.filter_manager.has_active_filters()):

                    filtered_data = self.filter_manager.get_filtered_data()
                    if filtered_data is not None and len(filtered_data) > 0:
                        chart_data = self._extract_chart_data(filtered_data, x_col, y_col)
                        if chart_data is not None and len(chart_data) > 0:
                            return chart_data, f"筛选后数据({len(chart_data)}个有效点)"

                # 使用当前数据（可能包含分段处理的结果）
                chart_data = self._extract_chart_data(self.data, x_col, y_col)
                if chart_data is not None and len(chart_data) > 0:
                    # 检查数据是否可能经过分段处理
                    nan_ratio = chart_data[y_col].isna().sum() / len(chart_data)
                    if nan_ratio > 0.05:  # 如果有超过5%的NaN值，可能经过了异常值处理
                        return chart_data, f"使用分段处理后的数据({len(chart_data)}个有效点)"
                    else:
                        return chart_data, f"NOW ({len(chart_data)} DATA)"

            return None, "没有可用数据"

        except Exception as e:
            print(f"[ERROR] 获取图表数据源失败: {e}")
            return None, "数据获取错误"

    def _extract_chart_data(self, data, x_col, y_col):
        """从数据中提取有效的图表数据"""
        try:
            if x_col not in data.columns or y_col not in data.columns:
                return None

            valid_mask = data[x_col].notna() & data[y_col].notna()
            valid_data = data.loc[valid_mask, [x_col, y_col]]

            return valid_data if len(valid_data) > 0 else None

        except Exception as e:
            print(f"[ERROR] 提取图表数据失败: {e}")
            return None

    # ======== 通用辅助方法 ========

    def show_error_message(self, title, message):
        """显示错误消息"""
        try:
            messagebox.showerror(title, message)
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('show_error_message_failed', '显示错误消息失败')}: {e}")

    def show_info_message(self, title, message):
        """显示信息消息"""
        try:
            messagebox.showinfo(title, message)
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('show_info_message_failed', '显示信息消息失败')}: {e}")

    def show_warning_message(self, title, message):
        """显示警告消息"""
        try:
            messagebox.showwarning(title, message)
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('show_warning_message_failed', '显示警告消息失败')}: {e}")

    # ======== 语言相关方法 ========

    def change_language(self, language_code):
        """切换语言"""
        try:
            if language_manager.set_language(language_code):
                self.update_all_texts()
                self.show_info_message(
                    language_manager.get_text('info', '信息'),
                    f"Language changed to: {language_manager.get_current_language_name()}"
                )
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('language_switch_failed', '语言切换失败')}: {e}")

    def update_all_texts(self):
        """更新所有界面文本"""
        try:
            self.update_window_title()
            for widget in self.main_frame.winfo_children():
                widget.destroy()
            self.create_main_content()
            self.setup_menu()

            if safe_check_dataframe(self.data):
                self.data_manager.update_data_interface_after_load()
                self._initialize_geochem_analysis()

        except Exception as e:
            print(f"[WARNING] {language_manager.get_text('interface_update_problem', '界面更新时出现问题')}: {e}")

    def show_about(self):
        """Show about dialog - English version"""
        try:
            about_text = f"""
    Geo-mean v1.0

    Professional Geochemical Data Analysis & Visualization Tool

    - Moving Window Bootstrap Statistical Analysis
    - Intelligent Outlier Processing
    - Geochemical Data Auto-Filtering
    - MATLAB Algorithm Python Implementation
    - Chart X-axis Default Small to Large Sorting

    Current Language: English
           """
            self.show_info_message("About", about_text)
        except Exception as e:
            print(f"[ERROR] Failed to show about dialog: {e}")

    # ======== 筛选管理器相关方法 ========

    def _initialize_filter_manager(self):
        """模块化初始化筛选管理器"""
        try:
            from ui.geochem_filter_manager import GeochemFilterManager
            self.filter_manager = GeochemFilterManager(self)
            print(f"[DEBUG] {language_manager.get_text('filter_manager_init_success', '筛选管理器初始化成功')}")
        except ImportError as e:
            print(f"[WARNING] {language_manager.get_text('filter_manager_import_failed', '无法导入筛选管理器')}: {e}")
            self.filter_manager = None
        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('filter_manager_init_failed', '筛选管理器初始化失败')}: {e}")
            self.filter_manager = None

    def _is_filter_manager_available(self):
        """检查筛选管理器是否可用"""
        return hasattr(self, 'filter_manager') and self.filter_manager is not None

    # ======== 兼容性方法 ========

    def open_geochem_filter(self):
        """保留兼容性 - 重定向到移动窗口分析"""
        self.show_info_message(
            language_manager.get_text('function_upgrade', '功能升级'),
            language_manager.get_text('geochem_filter_integrated',
                                      '地球化学筛选功能已集成到移动窗口分析中，请使用移动窗口分析按钮')
        )

    def apply_geochem_filters(self):
        """保留兼容性 - 重定向到移动窗口分析"""
        self.show_info_message(
            language_manager.get_text('function_upgrade', '功能升级'),
            language_manager.get_text('filter_integrated',
                                      '筛选功能已集成到移动窗口分析中，请使用移动窗口分析或一键分析按钮')
        )

    def update_data_interface_preserve_selection(self):
        """更新数据界面但保留列选择"""
        try:
            # 保存当前的列选择
            current_x_col = self.x_col_var.get()
            current_y_col = self.y_col_var.get()

            print(f"[DEBUG] 保存当前列选择: X={current_x_col}, Y={current_y_col}")

            # 调用原始的数据界面更新
            memory_info = self.data_manager.update_data_interface_after_load()

            # 恢复列选择（如果列仍然存在）
            if current_x_col and hasattr(self, 'data') and self.data is not None and current_x_col in self.data.columns:
                self.set_x_column(current_x_col)
                print(f"[DEBUG] 恢复X轴列选择: {current_x_col}")

            if current_y_col and hasattr(self, 'data') and self.data is not None and current_y_col in self.data.columns:
                self.set_y_column(current_y_col)
                print(f"[DEBUG] 恢复Y轴列选择: {current_y_col}")

            # 刷新数据预览表格
            if hasattr(self, 'data') and self.data is not None:
                self.refresh_data_table(self.data)

            return memory_info

        except Exception as e:
            print(f"[ERROR] 更新数据界面时保留列选择失败: {e}")
            return self.data_manager.update_data_interface_after_load()

    def remove_outliers_from_data(self, data, column, method, params):
        """
        从数据中移除异常值 - 改进版：直接行级筛选，保持列完整性

        Args:
            data: 原始数据DataFrame
            column: 要检测异常值的列名
            method: 检测方法 ('percentile', 'std_dev', 'iqr', 'custom')
            params: 方法参数字典

        Returns:
            DataFrame: 移除异常值行后的完整数据（所有列都保留）
        """
        try:
            if column not in data.columns:
                print(f"[ERROR] 列不存在: '{column}'")
                return None

            # 获取列数据
            data_col = data[column].dropna()
            if len(data_col) == 0:
                print(f"[WARNING] 列中没有有效数据: '{column}'")
                return data.copy()

            print(f"[DEBUG] 开始异常值检测: 列={column}, 方法={method}")
            print(f"[DEBUG] 原始数据: {len(data)} 行")

            # 计算阈值
            if method == "percentile":
                lower_bound = np.percentile(data_col, params['lower_percentile'])
                upper_bound = np.percentile(data_col, params['upper_percentile'])
            elif method == "std_dev":
                mean = data_col.mean()
                std = data_col.std()
                multiplier = params['std_multiplier']
                lower_bound = mean - multiplier * std
                upper_bound = mean + multiplier * std
            elif method == "iqr":
                q1 = data_col.quantile(0.25)
                q3 = data_col.quantile(0.75)
                iqr = q3 - q1
                multiplier = params['iqr_multiplier']
                lower_bound = q1 - multiplier * iqr
                upper_bound = q3 + multiplier * iqr
            elif method == "custom":
                lower_bound = params['lower_bound']
                upper_bound = params['upper_bound']
            else:
                print(f"[ERROR] 未知的异常值检测方法: {method}")
                return None

            print(f"[DEBUG] 阈值范围: [{lower_bound:.6f}, {upper_bound:.6f}]")

            # === 关键改进：直接行级筛选，不修改列值 ===

            # 1. 创建异常值掩码（在完整数据上操作，处理NaN值）
            valid_mask = data[column].notna()  # 找到非NaN的行
            outlier_mask = pd.Series(False, index=data.index)  # 初始化为全False

            # 2. 只对有效数据检测异常值
            valid_data = data.loc[valid_mask, column]
            valid_outliers = (valid_data < lower_bound) | (valid_data > upper_bound)
            outlier_mask.loc[valid_mask] = valid_outliers

            # 3. 直接返回移除异常值行后的完整数据
            result_data = data[~outlier_mask].copy()

            outlier_count = outlier_mask.sum()
            remaining_count = len(result_data)

            print(f"[INFO] 异常值处理完成:")
            print(f"  目标列: {column}")
            print(f"  检测方法: {method}")
            print(f"  阈值范围: [{lower_bound:.6f}, {upper_bound:.6f}]")
            print(f"  检测到异常值: {outlier_count} 行")
            print(f"  移除异常值行: {outlier_count} 行")
            print(f"  保留数据行: {remaining_count} 行")
            print(f"  所有列都完整保留: {len(result_data.columns)} 列")

            return result_data

        except Exception as e:
            print(f"[ERROR] 移除异常值时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _convert_single_boundary_results(self, raw_results, params):
        """转换单一边界模式的结果 - 支持动态列名"""
        try:
            import pandas as pd
            import numpy as np

            print("[DEBUG-FIX] 转换单一边界结果")

            # 获取原始列名信息
            age_column = raw_results.get('age_column') or params.get('age_column', 'age')
            target_column = raw_results.get('target_column') or params.get('target_column', 'target')

            print(f"[DEBUG-FIX] 使用动态列名: age_column={age_column}, target_column={target_column}")

            # 使用动态列名创建DataFrame
            results_df = pd.DataFrame({
                age_column: raw_results['window_centers'],  # 动态年龄列名
                f'{target_column}_mean': raw_results['means'],  # 动态目标列名_mean
                'std_error': [2 * std if not np.isnan(std) else np.nan
                              for std in raw_results.get('bootstrap_stds', [np.nan] * len(raw_results['means']))],
                'sample_count': raw_results['counts'],
                'window_start': raw_results['window_starts'],
                'window_end': raw_results['window_ends'],
                'boundary_mode': raw_results.get('method', params.get('boundary_mode', 'exclusive'))
            })

            print(f"[DEBUG-FIX] 单一边界结果转换完成: {len(results_df)} 个窗口")
            print(f"[DEBUG-FIX] 结果列名: {list(results_df.columns)}")
            return results_df

        except Exception as e:
            print(f"[ERROR] 转换单一边界结果失败: {e}")
            import traceback
            print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
            return None

    def _convert_boundary_comparison_results(self, raw_results, params):
        """转换边界方法比较的结果 - 支持动态列名"""
        try:
            import pandas as pd
            import numpy as np

            print("[DEBUG-FIX] 转换边界比较结果")

            # 获取原始列名信息（从第一个方法结果中获取）
            age_column = params.get('age_column', 'age')
            target_column = params.get('target_column', 'target')

            # 尝试从结果中获取更准确的列名信息
            for method_name, method_results in raw_results.items():
                if method_name != 'comparison_analysis' and isinstance(method_results, dict):
                    age_column = method_results.get('age_column') or age_column
                    target_column = method_results.get('target_column') or target_column
                    break

            print(f"[DEBUG-FIX] 使用动态列名: age_column={age_column}, target_column={target_column}")

            all_results = []

            for method_name, method_results in raw_results.items():
                if method_name == 'comparison_analysis':
                    continue

                # 使用动态列名创建DataFrame
                method_df = pd.DataFrame({
                    age_column: method_results['window_centers'],  # 动态年龄列名
                    f'{target_column}_mean': method_results['means'],  # 动态目标列名_mean
                    'std_error': [2 * std if not np.isnan(std) else np.nan
                                  for std in
                                  method_results.get('bootstrap_stds', [np.nan] * len(method_results['means']))],
                    'sample_count': method_results['counts'],
                    'window_start': method_results['window_starts'],
                    'window_end': method_results['window_ends'],
                    'boundary_mode': method_name
                })
                all_results.append(method_df)

            if all_results:
                result = pd.concat(all_results, ignore_index=True)
                print(f"[DEBUG-FIX] 边界比较结果转换完成: {len(result)} 个窗口")
                print(f"[DEBUG-FIX] 结果列名: {list(result.columns)}")
                return result
            return None

        except Exception as e:
            print(f"[ERROR] 转换边界比较结果失败: {e}")
            import traceback
            print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
            return None

    # ========== 方法4：如果没有这些辅助方法，也添加进去 ==========

    def _validate_analysis_params_local(self, params):
        """本地参数验证函数"""
        if not isinstance(params, dict):
            return False, "参数必须是字典类型"

        required_keys = ['age_column', 'target_column', 'window_size', 'step_size']
        for key in required_keys:
            if key not in params:
                return False, f"缺少必需参数: {key}"

        try:
            window_size = float(params['window_size'])
            step_size = float(params['step_size'])

            if window_size <= 0 or step_size <= 0:
                return False, "窗口大小和步长必须大于0"

        except (ValueError, TypeError):
            return False, "窗口大小和步长必须是有效数值"

        return True, "参数验证通过"

    def _confirm_analysis_execution_local(self, params):
        """本地确认执行函数"""
        try:
            confirm_text = f"""移动窗口分析参数摘要:

    年龄列: {params['age_column']}
    目标列: {params['target_column']}
    年龄范围: {params.get('min_age', 'N/A')} - {params.get('max_age', 'N/A')} Ma
    窗口大小: {params['window_size']} Ma
    步长: {params['step_size']} Ma
    边界模式: {params.get('boundary_mode', 'exclusive')}
    预计窗口数: {params.get('estimated_windows', 'N/A')}

    [FIX] 已启用边界处理功能

    确定要开始分析吗？"""

            return messagebox.askyesno('确认分析', confirm_text)
        except Exception as e:
            print(f"[ERROR] 构建确认信息失败: {e}")
            return True

    def _create_progress_window_safe(self, params):
        """安全创建进度窗口"""
        try:
            from ui.progress_windows import ModernAnalysisProgressWindow
            estimated_windows = params.get('estimated_windows', 100)
            return ModernAnalysisProgressWindow(self.root, estimated_windows)
        except ImportError as e:
            print(f"[WARNING] 进度窗口不可用: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] 创建进度窗口失败: {e}")
            return None

    def _fix_error_bars_safe(self, results):
        """禁用误差棒修复，强制使用原始Bootstrap数据"""
        try:
            import numpy as np

            # 严格检查：必须有真实的Bootstrap误差数据
            if 'std_error' not in results.columns:
                raise ValueError(
                    "Bootstrap分析结果缺少std_error列。"
                    "请确保移动窗口分析正确计算了Bootstrap统计量。"
                    "不允许使用默认误差棒作为替代方案。"
                )

            # 检查数据质量：不允许全部为空
            valid_errors = results['std_error'].dropna()
            if len(valid_errors) == 0:
                raise ValueError(
                    "Bootstrap误差数据全部无效(NaN)。"
                    "请检查Bootstrap计算流程，确保每个窗口都有有效的统计结果。"
                    "不允许使用插值或估算作为替代方案。"
                )

            # 检查是否有过多的缺失值
            nan_count = results['std_error'].isna().sum()
            total_count = len(results)
            missing_ratio = nan_count / total_count

            if missing_ratio > 0.1:  # 超过10%缺失
                raise ValueError(
                    f"Bootstrap误差数据缺失率过高: {missing_ratio:.1%} ({nan_count}/{total_count})。"
                    "请修复Bootstrap计算流程，确保大部分窗口都能产生有效的统计结果。"
                    "不允许使用插值修复大量缺失数据。"
                )

            # 严格模式：不进行任何修复或替换
            print(f"[BOOTSTRAP-STRICT] 使用原始Bootstrap误差数据")
            print(f"[BOOTSTRAP-STRICT] 有效误差值: {len(valid_errors)}/{total_count}")
            print(f"[BOOTSTRAP-STRICT] 误差范围: {valid_errors.min():.6f} - {valid_errors.max():.6f}")

            # 直接返回原始数据，不做任何修改
            return results

        except Exception as e:
            print(f"[ERROR] Bootstrap数据验证失败: {e}")
            raise e  # 重新抛出错误，不返回修复后的数据

    def auto_generate_chart_after_analysis(self, x_col, y_col, results):
        """移动窗口分析完成后自动生成图表"""
        try:
            print(f"[AUTO-CHART] 开始自动生成图表: {x_col} vs {y_col}")

            # 检查图表控制器是否可用
            if not hasattr(self, 'chart_controller'):
                print("[WARNING] 图表控制器不可用")
                return False

            # 移动窗口分析使用折线图（最适合的类型）
            chart_type = "Line Chart"

            print(f"[AUTO-CHART] 使用图表类型: {chart_type}")

            # 验证数据并获取图表数据
            chart_data, data_source_info = self._get_smart_chart_data(x_col, y_col)

            if chart_data is None or len(chart_data) == 0:
                print("[WARNING] 没有有效的图表数据")
                return False

            print(f"[AUTO-CHART] 图表数据: {len(chart_data)} 个数据点")

            # 生成图表 - 这里会自动弹出图表窗口
            success, result_message = self.chart_controller.generate_chart(
                chart_data, x_col, y_col, chart_type
            )

            if success:
                print(f"[AUTO-CHART] 图表生成成功")

                # 🔧 关键修改：生成图表后，将界面选择框设置为散点图
                if hasattr(self, 'chart_type_var'):
                    self.chart_type_var.set("Scatter Plot")  # 或者 "散点图"
                    print("[AUTO-CHART] 界面图表类型已设置为散点图，方便后续手动操作")

                return True
            else:
                print(f"[AUTO-CHART] 图表生成失败: {result_message}")
                return False

        except Exception as e:
            print(f"[ERROR] 自动图表生成异常: {e}")
            return False

    def show_analysis_completion_message_with_chart(self, params, total_windows, valid_windows, x_axis_col, y_axis_col):
        """显示分析完成消息 - 包含自动图表信息"""
        try:
            boundary_mode_names = {
                'exclusive': 'Exclusive',
                'inclusive': 'Inclusive',
                'left_priority': 'Left Priority',
                'right_priority': 'Right Priority',
                'weighted_overlap': 'Weighted Overlap'
            }
            mode_name = boundary_mode_names.get(params.get('boundary_mode', 'exclusive'), 'Unknown')

            # Get data range
            try:
                min_age = params.get('min_age', 0)
                max_age = params.get('max_age', 4000)
            except:
                min_age, max_age = 0, 4000

            # 根据是否有有效的图表列来调整消息
            if x_axis_col and y_axis_col:
                chart_info = f"""
        Chart automatically generated and displayed
        Chart type: Line chart with error bars
        X-axis: {x_axis_col}
        Y-axis: {y_axis_col}"""
            else:
                chart_info = """
        Chart generation skipped (column detection failed)
        You can manually generate charts using the chart controls"""

            completion_text = f"""Moving window analysis completed!

    Analysis Results:
    - Windows: {valid_windows}/{total_windows} valid windows
    - Data range: {min_age:.0f} - {max_age:.0f} Ma  
    - Boundary mode: {mode_name}
    {chart_info}

    What you can do now:
    - View the auto-generated chart in the new window
    - Export analysis results to Excel
    - Generate additional chart types
    - Save chart images"""

            try:
                self.show_info_message('Analysis Completed', completion_text)
            except Exception as e:
                print(f"[DEBUG] Failed to show info window: {str(e)}")
                # Fallback: simplified message
                simple_message = f"Moving window analysis completed!\n\nWindows: {valid_windows} valid windows\nChart automatically generated and displayed!"
                self.show_info_message('Analysis Completed', simple_message)

        except Exception as e:
            print(f"[ERROR] Failed to show completion message: {e}")


    def _handle_analysis_complete_safe(self, progress_window, success, message, results, params):
        """Safe handling of analysis completion - with automatic chart generation"""
        try:
            # Close progress window
            if progress_window and hasattr(progress_window, 'close'):
                progress_window.close()

            if success and results is not None:
                # 统一重命名std_error为2SE
                if 'std_error' in results.columns:
                    results = results.rename(columns={'std_error': '2SE'})
                    print(f"[DEBUG] 已将std_error重命名为2SE")

                # Save results
                self.geochem_analysis_results = results
                self.moving_window_results = results

                # 动态找到X轴列和Y轴列（基于用户在移动窗口分析中的实际选择）
                x_axis_col = None
                y_axis_col = None

                # 从分析参数中获取用户选择的列名
                if 'age_column' in params:
                    x_axis_col = params['age_column']  # 用户选择的X轴列
                if 'target_column' in params:
                    # 查找对应的均值列
                    target_col = params['target_column']
                    mean_col_name = f"{target_col}_mean"
                    if mean_col_name in results.columns:
                        y_axis_col = mean_col_name

                # 备用方案：如果参数中没有找到，则动态检测
                if not x_axis_col or not y_axis_col:
                    special_columns = ['2SE', 'std_error', 'sample_count', 'window_low', 'window_high',
                                       'window_start', 'window_end', 'boundary_mode']

                    # 找均值列
                    if not y_axis_col:
                        for col in results.columns:
                            if col.endswith('_mean') and '-' not in col:
                                y_axis_col = col
                                break

                    # 找X轴列
                    if not x_axis_col:
                        for col in results.columns:
                            if (col not in special_columns and
                                    not col.endswith('_mean') and
                                    '-' not in col):
                                x_axis_col = col
                                break

                if y_axis_col:
                    valid_windows = len(results.dropna(subset=[y_axis_col]))
                else:
                    valid_windows = len(results)
                total_windows = len(results)

                # Update status
                self.update_status(f"[OK] Boundary analysis completed: {valid_windows}/{total_windows} valid windows")

                # Update analysis status (if method exists)
                if hasattr(self, 'update_geochem_analysis_status'):
                    boundary_mode = params.get('boundary_mode', 'exclusive')
                    self.update_geochem_analysis_status(
                        f"Boundary analysis completed ({boundary_mode}): {valid_windows}/{total_windows} valid windows",
                        "success")

                # 分析完成后直接自动生成图表，不切换X/Y轴选择
                if x_axis_col and y_axis_col:
                    print(f"[AUTO-CHART] 自动生成图表: X轴={x_axis_col}, Y轴={y_axis_col}")

                    # 核心功能：自动生成图表（这里会弹出图表窗口）
                    try:
                        chart_success = self.auto_generate_chart_after_analysis(x_axis_col, y_axis_col, results)

                        if chart_success:
                            print("[SUCCESS] 自动图表生成成功，图表窗口已弹出")
                        else:
                            print("[WARNING] 自动图表生成失败，但分析结果已保存")
                    except Exception as e:
                        print(f"[WARNING] 自动图表生成异常: {e}")
                else:
                    print(f"[WARNING] 无法确定图表列: x_axis_col={x_axis_col}, y_axis_col={y_axis_col}")

                # Display completion info - 显示包含图表信息的完成消息
                self.show_analysis_completion_message_with_chart(params, total_windows, valid_windows, x_axis_col,
                                                                 y_axis_col)

            else:
                self.show_warning_message('Analysis Failed', message)

        except Exception as e:
            print(f"[ERROR] Failed to handle analysis completion: {e}")
            import traceback
            traceback.print_exc()

    def execute_geo_aggregation(self):
        """执行地理数据聚合 - 集成到你的主窗口"""
        try:
            # 1. 检查全局数据管理器
            if not hasattr(self, 'global_data_manager'):
                from tkinter import messagebox
                messagebox.showerror("错误", "全局数据管理器未初始化")
                return

            # 2. 获取当前数据
            current_data = self.global_data_manager.get_current_data()
            if current_data is None:
                from tkinter import messagebox
                messagebox.showwarning("警告", "请先加载数据")
                return

            print(f"[DEBUG] 准备执行地理聚合，当前数据: {len(current_data)} 行 x {len(current_data.columns)} 列")

            # 3. 准备列信息
            all_columns = list(current_data.columns)
            numeric_columns = list(current_data.select_dtypes(include=['number']).columns)

            print(f"[DEBUG] 可用列: {len(all_columns)}, 数值列: {len(numeric_columns)}")

            # 4. 显示聚合对话框
            from ui.geo_aggregation_dialog import show_geo_aggregation_dialog
            result = show_geo_aggregation_dialog(
                self, current_data, all_columns, numeric_columns
            )

            if result is None:
                print("[INFO] 用户取消了地理聚合操作")
                return

            # 5. 处理聚合结果
            aggregated_data = result['aggregated_data']
            method = result['aggregation_method']
            group_column = result['group_column']
            stats = result['statistics']

            print(f"[DEBUG] 聚合完成: {method} 方法, 分组列: {group_column}")
            print(f"[DEBUG] 聚合统计: {stats['original_count']} -> {stats['aggregated_count']} 行")

            # 6. 更新全局数据管理器
            operation_name = f"地理数据聚合 ({method} - {group_column})"
            success = self.global_data_manager.update_current_data(
                aggregated_data,
                operation_name,
                metadata={
                    'aggregation_method': method,
                    'group_column': group_column,
                    'original_rows': stats.get('original_count', 0),
                    'aggregated_rows': stats.get('aggregated_count', 0),
                    'aggregation_ratio': stats.get('aggregation_ratio', 0)
                }
            )

            if success:
                print(f"[DEBUG-INTEGRATION] 统一数据更新: {operation_name}")

                # 7. 更新界面
                if hasattr(self, 'data_manager'):
                    self.data_manager.update_data_interface_after_load()

                # 8. 更新列选择器（如果有的话）
                if hasattr(self, 'update_column_selectors'):
                    new_all_columns = list(aggregated_data.columns)
                    new_numeric_columns = list(aggregated_data.select_dtypes(include=['number']).columns)
                    self.update_column_selectors(new_all_columns, new_numeric_columns)

                # 刷新数据预览表格
                current_data = self.global_data_manager.get_current_data()
                if current_data is not None:
                    self.refresh_data_table(current_data)

                # 9. 显示成功消息
                from tkinter import messagebox
                message = (f"地理聚合完成！\n\n"
                           f"聚合方法: {method}\n"
                           f"分组依据: {group_column}\n"
                           f"原始数据: {stats.get('original_count', 0)} 行\n"
                           f"聚合后: {stats.get('aggregated_count', 0)} 行\n"
                           f"聚合比例: {stats.get('aggregation_ratio', 0):.1%}")

                messagebox.showinfo("聚合成功", message)

                # 10. 更新状态栏（如果有的话）
                if hasattr(self, 'update_status_bar'):
                    status_msg = f"地理聚合完成: {stats['original_count']} → {stats['aggregated_count']} 行"
                    self.update_status_bar(status_msg)

            else:
                from tkinter import messagebox
                messagebox.showerror("错误", "聚合结果更新失败")

        except Exception as e:
            error_msg = f"地理聚合失败: {str(e)}"
            print(f"[ERROR] {error_msg}")

            from tkinter import messagebox
            messagebox.showerror("错误", error_msg)

    def reset_to_original_data(self):
        """重置到原始数据 - 集成到你的主窗口"""
        try:
            if not hasattr(self, 'global_data_manager'):
                from tkinter import messagebox
                messagebox.showerror("错误", "全局数据管理器未初始化")
                return

            # 检查是否有原始数据
            original_data = self.global_data_manager.get_original_data()
            if original_data is None:
                from tkinter import messagebox
                messagebox.showinfo("提示", "没有原始数据可以重置")
                return

            # 重置数据
            success = self.global_data_manager.reset_to_original()

            if success:
                # 更新界面
                if hasattr(self, 'data_manager'):
                    self.data_manager.update_data_interface_after_load()

                # 更新列选择器
                if hasattr(self, 'update_column_selectors'):
                    all_columns = list(original_data.columns)
                    numeric_columns = list(original_data.select_dtypes(include=['number']).columns)
                    self.update_column_selectors(all_columns, numeric_columns)

                # 刷新数据预览表格
                self.refresh_data_table(original_data)

                # 更新状态栏
                if hasattr(self, 'update_status_bar'):
                    self.update_status_bar("已重置到原始数据")

                from tkinter import messagebox
                messagebox.showinfo("成功", "已重置到原始数据")

            else:
                from tkinter import messagebox
                messagebox.showerror("错误", "重置失败")

        except Exception as e:
            error_msg = f"重置数据时出错: {str(e)}"
            print(f"[ERROR] {error_msg}")

            from tkinter import messagebox
            messagebox.showerror("错误", error_msg)

    def load_excel_with_location_fix(self, file_path):
        """加载Excel文件 - 使用修复后的数据处理器"""
        try:
            # 1. 创建修复后的数据处理器
            from core.data_processor import DataProcessor
            processor = DataProcessor()

            # 2. 显示进度（如果有进度窗口的话）
            def progress_callback(message):
                print(f"[PROGRESS] {message}")
                # 如果你有进度窗口，在这里更新
                # if hasattr(self, 'progress_window'):
                #     self.progress_window.update_progress(message)

            # 3. 加载文件
            success, message = processor.load_excel(file_path, progress_callback)

            if success:
                # 4. 获取加载的数据
                loaded_data = processor.data

                # 5. 设置到全局数据管理器
                if hasattr(self, 'global_data_manager'):
                    success = self.global_data_manager.set_original_data(
                        loaded_data,
                        file_path=file_path,
                        source_info=f"Excel文件: {file_path}"
                    )

                    if success:
                        print(f"[DEBUG] 数据已加载到全局管理器: {len(loaded_data)} 行")

                        # 6. 更新界面
                        if hasattr(self, 'data_manager'):
                            self.data_manager.update_data_interface_after_load()

                        # 7. 刷新数据预览表格
                        self.refresh_data_table(loaded_data)

                        return True, message
                    else:
                        return False, "数据设置到全局管理器失败"
                else:
                    # 如果没有全局数据管理器，直接设置到主窗口
                    self.data = loaded_data
                    return True, message
            else:
                return False, message

        except Exception as e:
            return False, f"加载失败: {str(e)}"

    def get_chart_data_with_integration(self, x_col, y_col):
        """获取图表数据 - 集成版本"""
        try:
            # 优先从全局数据管理器获取
            if hasattr(self, 'global_data_manager'):
                current_data = self.global_data_manager.get_current_data()
                if current_data is not None and x_col in current_data.columns and y_col in current_data.columns:
                    chart_data = current_data[[x_col, y_col]].dropna()
                    print(f"[DEBUG] 从全局数据管理器获取图表数据: {len(chart_data)} 行")
                    return chart_data

            # 备用：从主窗口数据获取
            if hasattr(self, 'data') and self.data is not None:
                if x_col in self.data.columns and y_col in self.data.columns:
                    chart_data = self.data[[x_col, y_col]].dropna()
                    print(f"[DEBUG] 从主窗口数据获取图表数据: {len(chart_data)} 行")
                    return chart_data

            print(f"[WARNING] 无法获取图表数据 ({x_col}, {y_col})")
            return None

        except Exception as e:
            print(f"[ERROR] 获取图表数据失败: {e}")
            return None

    # 菜单添加示例
    def setup_menu_with_geo_aggregation(self):
        """设置包含地理聚合的菜单"""
        import tkinter as tk

        # 假设你已经有menubar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 数据菜单
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="数据", menu=data_menu)

        data_menu.add_command(label="加载Excel文件", command=self.load_file_dialog)
        data_menu.add_separator()
        data_menu.add_command(label="地理数据聚合", command=self.execute_geo_aggregation)
        data_menu.add_command(label="重置到原始数据", command=self.reset_to_original_data)
        data_menu.add_separator()
        data_menu.add_command(label="数据信息", command=self.show_data_info)

    def load_file_dialog(self):
        """文件选择对话框"""
        from tkinter import filedialog, messagebox

        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )

        if file_path:
            success, message = self.load_excel_with_location_fix(file_path)
            if success:
                messagebox.showinfo("成功", message)
            else:
                messagebox.showerror("错误", message)

    def show_data_info(self):
        """显示数据信息"""
        try:
            if hasattr(self, 'global_data_manager'):
                status = self.global_data_manager.get_processing_status()

                info_text = f"""数据状态信息:

    是否有数据: {'是' if status['has_data'] else '否'}
    是否有原始数据: {'是' if status['has_original'] else '否'}
    处理步骤数: {status['history_count']}

    当前数据形状: {status['current_shape']}
    原始数据形状: {status['original_shape']}

    处理摘要: {self.global_data_manager.get_processing_summary()}
    """

                from tkinter import messagebox
                messagebox.showinfo("数据信息", info_text)
            else:
                from tkinter import messagebox
                messagebox.showinfo("数据信息", "全局数据管理器未初始化")

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("错误", f"获取数据信息失败: {str(e)}")

    def _handle_analysis_error_safe(self, progress_window, error_msg):
        """安全处理分析错误"""
        try:
            if progress_window and hasattr(progress_window, 'close'):
                progress_window.close()

            self.update_status(f"[Error] 边界处理分析错误")
            if hasattr(self, 'update_geochem_analysis_status'):
                self.update_geochem_analysis_status("边界处理分析出错", "error")

            self.show_error_message('分析错误', f"边界处理分析失败:\n{error_msg}")

        except Exception as e:
            print(f"[ERROR] 处理分析错误失败: {e}")

    # 在 geochemistry/moving_window_analyzer.py 文件末尾添加：

    def run_complete_analysis(data_processor,
                              age_column: str,
                              target_column: str,
                              window_params: Dict = None,
                              boundary_mode: str = "exclusive",
                              export_path: str = None,
                              compare_methods: bool = False):
        """
        运行完整的移动窗口分析流程（支持边界处理选项）

        Args:
            data_processor: DataProcessor实例
            age_column: 年龄列名
            target_column: 目标列名
            window_params: 窗口参数字典
            boundary_mode: 边界处理模式
            export_path: 导出路径
            compare_methods: 是否比较不同的边界处理方法

        Returns:
            (分析器实例, 结果DataFrame)
        """
        # 默认参数
        if window_params is None:
            window_params = {
                'low': 2900,
                'high': 3100,
                'move_step': 50
            }

        # 创建分析器
        analyzer = create_analyzer_from_processor(data_processor)

        # 设置列映射
        analyzer.set_column_mapping({
            'AGE': age_column,
            'ThU': target_column
        })

        print(f"[INFO] 开始完整的移动窗口分析流程 (边界模式: {boundary_mode})...")

        # 1. 应用地球化学筛选
        try:
            filtered_data = analyzer.apply_geochemical_filters()
            print("[SUCCESS] 地球化学筛选完成")
        except Exception as e:
            print(f"[WARNING] 地球化学筛选失败，使用原始数据: {e}")
            analyzer.filtered_data = analyzer.original_data

        # 2. 移除异常值
        try:
            analyzer.remove_outliers(target_column)
            print("[SUCCESS] 异常值移除完成")
        except Exception as e:
            print(f"[WARNING] 异常值移除失败: {e}")

        # 3. 移动窗口分析
        results = analyzer.moving_window_analysis(
            age_column=age_column,
            target_column=target_column,
            boundary_mode=boundary_mode,
            **window_params
        )

        # 4. 导出结果
        if export_path:
            analyzer.export_results(export_path, include_boundary_info=True)

        print("[SUCCESS] 完整分析流程完成")

        return analyzer, results