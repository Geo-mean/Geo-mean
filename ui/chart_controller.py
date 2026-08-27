"""
完全国际化的图表控制器 - ui/chart_controller.py
"""

import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from config.languages import language_manager


# [PALETTE] 科学期刊风格美化函数
def apply_scientific_journal_style(fig, ax):
    """应用科学期刊风格 - 专业、严谨、适合发表"""
    try:
        # [TARGET] 科学期刊标准：纯白背景，最小干扰
        fig.patch.set_facecolor('#ffffff')
        ax.set_facecolor('#ffffff')  # 纯白背景

        # [TARGET] 科学期刊网格：细致、低调的网格
        ax.grid(True, alpha=0.25, linestyle='-', linewidth=0.6, color='#cccccc')
        ax.minorticks_on()  # 启用小刻度
        ax.grid(True, which='minor', alpha=0.12, linestyle=':', linewidth=0.4, color='#dddddd')
        ax.set_axisbelow(True)

        # [TARGET] 科学期刊坐标轴：黑色，简洁
        for spine in ax.spines.values():
            spine.set_linewidth(1.2)
            spine.set_color('#000000')  # 纯黑色边框

        # [TARGET] 科学期刊刻度：清晰易读
        ax.tick_params(
            colors='#000000',  # 黑色刻度
            labelsize=11,
            direction='out',
            length=5,
            width=1.0,
            which='major'
        )

        # 小刻度样式
        ax.tick_params(
            colors='#000000',
            length=3,
            width=0.8,
            which='minor'
        )

        # [TARGET] 科学期刊标签：黑色，专业字体
        ax.xaxis.label.set_color('#000000')
        ax.yaxis.label.set_color('#000000')
        ax.title.set_color('#000000')
        ax.xaxis.label.set_fontsize(12)
        ax.yaxis.label.set_fontsize(12)
        ax.title.set_fontsize(14)
        ax.title.set_fontweight('bold')

        print("[SUCCESS] 科学期刊风格已应用")
        return True
    except Exception as e:
        print(f"[WARNING] 科学期刊样式应用失败: {e}")
        return False


def beautify_scientific_line_chart(ax, x_data, y_data, error_data=None, show_error_bars=False):
    """科学期刊风格折线图 - 使用真实误差数据"""
    try:
        # 数据排序
        if hasattr(x_data, 'argsort'):
            sorted_indices = x_data.argsort()
            x_sorted = x_data.iloc[sorted_indices] if hasattr(x_data, 'iloc') else x_data[sorted_indices]
            y_sorted = y_data.iloc[sorted_indices] if hasattr(y_data, 'iloc') else y_data[sorted_indices]

            # [OK] 关键修复：如果有真实误差数据，也要排序
            if error_data is not None:
                error_sorted = error_data.iloc[sorted_indices] if hasattr(error_data, 'iloc') else error_data[sorted_indices]
            else:
                error_sorted = None
        else:
            sorted_indices = np.argsort(x_data)
            x_sorted = np.array(x_data)[sorted_indices]
            y_sorted = np.array(y_data)[sorted_indices]
            error_sorted = np.array(error_data)[sorted_indices] if error_data is not None else None

        # [TARGET] 科学期刊配色：深蓝色主线，专业可靠
        main_color = '#1f4e79'  # 深蓝色
        marker_color = '#2563eb'  # 稍亮的蓝色

        # 绘制主折线 - 科学期刊标准样式
        line = ax.plot(x_sorted, y_sorted,
                      color=main_color,
                      linewidth=2.0,  # 期刊标准线宽
                      marker='o',
                      markersize=5,  # 适中的点大小
                      markerfacecolor=marker_color,
                      markeredgecolor='white',
                      markeredgewidth=1.0,
                      alpha=0.95,
                      zorder=5,
                      label='观测数据')

        # [OK] 修复：使用真实的误差数据
        if show_error_bars and error_sorted is not None:
            print(f"[DEBUG] 使用真实误差数据")
            print(f"[DEBUG] 误差范围: {np.min(error_sorted):.6f} - {np.max(error_sorted):.6f}")
            print(f"[DEBUG] 误差平均值: {np.mean(error_sorted):.6f}")
            print(f"[DEBUG] 误差变异性: {np.std(error_sorted):.6f}")

            # [TARGET] 科学期刊误差棒：深红色，使用真实Bootstrap误差
            ax.errorbar(x_sorted, y_sorted,
                       yerr=error_sorted,  # [OK] 使用真实的不同误差值
                       fmt='none',
                       ecolor='#dc2626',  # 深红色
                       capsize=4,  # 期刊标准帽子大小
                       capthick=1.5,
                       elinewidth=1.5,
                       alpha=0.8,
                       zorder=4,
                       label='2σ 不确定性')

            print("[SUCCESS] 真实Bootstrap误差棒已添加")


        elif show_error_bars:

            # 强制要求真实Bootstrap误差数据，禁用所有备用方案

            print("[ERROR] 缺少真实Bootstrap误差数据，拒绝使用估算备用方案")

            print("[STRICT] 要求提供真实的Bootstrap std_error数据")

            # 抛出错误，强制修复数据源问题

            raise ValueError(

                "Bootstrap误差棒显示失败: 缺少真实的Bootstrap误差数据。"

                "请确保移动窗口分析正确计算了Bootstrap统计量，"

                "并且结果数据包含有效的'std_error'列。"

                "不允许使用估算误差作为替代方案。"

            )
        else:
            print("[INFO] ")

        print("[SUCCESS] 科学期刊风格折线图完成")
        return True
    except Exception as e:
        print(f"[WARNING] 科学期刊折线图美化失败: {e}")
        return False


def beautify_scientific_scatter_chart(ax, x_data, y_data, show_colorbar=False, is_analysis_result=False):
    """科学期刊风格散点图 - 修复版：智能控制颜色条显示"""
    try:
        if show_colorbar and is_analysis_result:

            print("[DEBUG] ")

            # 根据Y值创建科学的颜色映射
            if len(y_data) > 1:
                y_min, y_max = np.min(y_data), np.max(y_data)
                if y_max != y_min:
                    c_values = (y_data - y_min) / (y_max - y_min)
                else:
                    c_values = [0.5] * len(y_data)
            else:
                c_values = [0.5] * len(y_data)

            # 科学期刊专用配色：plasma色谱
            scatter = ax.scatter(x_data, y_data,
                               c=c_values,
                               cmap='plasma',  # 科学可视化标准色谱
                               s=60,  # 期刊标准点大小
                               alpha=0.85,
                               edgecolors='black',  # 黑色边框
                               linewidth=0.8,
                               zorder=5)

            # 添加科学期刊标准颜色条
            try:
                if hasattr(ax, 'figure') and ax.figure:
                    cbar = ax.figure.colorbar(scatter, ax=ax, shrink=0.8, aspect=25, pad=0.02)
                    cbar.set_label('相对数值', fontsize=11, fontweight='normal', rotation=270, labelpad=18)
                    cbar.ax.tick_params(labelsize=10, colors='#000000')

                    # 颜色条边框
                    cbar.outline.set_linewidth(1.0)
                    cbar.outline.set_edgecolor('#000000')

                    print("[SUCCESS] 科学期刊标准颜色条已添加")
            except Exception as e:
                print(f"[WARNING] 添加颜色条失败: {e}")

        else:
            # [TARGET] 原始数据散点图：简洁单色，无颜色条
            print("[DEBUG] 绘制原始数据散点图 - 使用简洁单色")

            scatter = ax.scatter(x_data, y_data,
                               color='#1f4e79',  # 统一的深蓝色
                               s=50,  # 适中的点大小
                               alpha=0.75,
                               edgecolors='black',  # 黑色边框
                               linewidth=0.6,
                               zorder=5)

            print("[SUCCESS] 原始数据散点图完成 - 无颜色条")

        print("[SUCCESS] 科学期刊风格散点图完成")
        return True
    except Exception as e:
        print(f"[WARNING] 科学期刊散点图美化失败: {e}")
        return False


class ChartController:
    """图表控制器类 - 科学期刊风格版本"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.current_data = None
        self.chart_windows = []  # 存储图表窗口引用

    def get_chart_types(self):
        """获取图表类型列表 - 多语言"""
        chart_types = [
            # language_manager.get_text('line_chart', '折线图'),
            language_manager.get_text('scatter_chart', '散点图'),
            # language_manager.get_text('bar_chart', '柱状图'),
            # language_manager.get_text('histogram', '直方图')
        ]
        return chart_types

    def validate_chart_generation(self, chart_type, x_col, y_col):
        """验证图表生成参数 - 多语言"""
        if not chart_type:
            return False, language_manager.get_text('select_chart_type', '请选择图表类型')

        if not x_col or not y_col:
            return False, language_manager.get_text('select_columns', '请选择X轴和Y轴列')

        if x_col == y_col:
            return False, language_manager.get_text('same_columns_error', 'X轴和Y轴不能是同一列')

        return True, language_manager.get_text('data_validation_passed', '验证通过')

    def generate_chart(self, data, x_col, y_col, chart_type):
        """生成图表 - 使用tkinter内嵌matplotlib"""
        try:
            if data is None or len(data) == 0:
                return False, language_manager.get_text('no_data', '没有数据可以生成图表')

            # 🔧 调试输出：检查接收到的数据结构
            print(f"[DEBUG] 图表生成收到的数据列名: {list(data.columns)}")
            print(f"[DEBUG] x_col参数: {x_col}, y_col参数: {y_col}")
            print(f"[DEBUG] 数据预览:")
            print(data.head(3))
            print(f"[DEBUG] 数据形状: {data.shape}")

            print(
                f"[DEBUG] {language_manager.get_text('chart_testing', '开始生成图表')}: {chart_type}, {language_manager.get_text('data_preview', '数据行数')}: {len(data)}")

            # 获取图表类型的英文key
            chart_type_key = self._get_chart_type_key(chart_type)
            if not chart_type_key:
                return False, language_manager.get_text('invalid_chart_type', f'不支持的图表类型: {chart_type}')

            # 保存当前数据
            self.current_data = data.copy()

            # 使用tkinter创建图表窗口（避免matplotlib后端问题）
            success = self._create_tkinter_chart_window(data, x_col, y_col, chart_type, chart_type_key)

            if success:
                return True, language_manager.get_text('chart_saved', f'成功生成{chart_type}')
            else:
                return False, language_manager.get_text('chart_error', '图表生成失败')

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('chart_generation_failed', '生成图表失败')}: {e}")
            import traceback
            print(f"[DEBUG] {language_manager.get_text('error_info', '错误详情')}:\n{traceback.format_exc()}")
            return False, language_manager.get_text('chart_error', f'图表生成失败: {str(e)}')

    def _create_tkinter_chart_window(self, data, x_col, y_col, chart_type, chart_type_key):
        """创建tkinter图表窗口"""
        try:
            # 创建新窗口
            chart_window = tk.Toplevel(self.main_window.root)
            chart_window.title(f"[Scientific] {chart_type} - {x_col} vs {y_col}")
            chart_window.geometry("1350x700")
            chart_window.configure(bg='white')

            # 确保窗口在前台
            chart_window.lift()
            chart_window.attributes('-topmost', True)
            chart_window.after(100, lambda: chart_window.attributes('-topmost', False))

            # 存储窗口引用
            self.chart_windows.append(chart_window)

            # 创建主框架
            main_frame = tk.Frame(chart_window, bg='white')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 工具栏
            toolbar_frame = tk.Frame(main_frame, bg='white', height=50)
            toolbar_frame.pack(fill=tk.X, pady=(0, 10))
            toolbar_frame.pack_propagate(False)

            # 工具栏内容
            toolbar_content = tk.Frame(toolbar_frame, bg='white')
            toolbar_content.pack(fill=tk.X, pady=(0, 5))

            # 统计信息
            data_type = "" if self._is_moving_window_result(data, x_col, y_col) else ""
            info_label = tk.Label(
                toolbar_content,
                text=f"[Scientific] {language_manager.get_text('data_preview', '数据点')}: {len(data)} | {language_manager.get_text('chart_type', '类型')}: {chart_type} | {data_type}",
                bg='white',
                fg='#666666',
                font=('Arial', 9)
            )
            info_label.pack(side=tk.RIGHT)

            # 图表区域
            chart_frame = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=1)
            chart_frame.pack(fill=tk.BOTH, expand=True)

            # 尝试使用matplotlib
            try:
                success = self._embed_matplotlib_chart_with_axis_control(
                    chart_frame, data, x_col, y_col, chart_type_key
                )
                if success:
                    print(f"[SUCCESS] {language_manager.get_text('chart_saved', '科学期刊风格图表嵌入成功')}")
                    return True
            except Exception as e:
                print(f"[WARNING] {language_manager.get_text('chart_error', 'matplotlib嵌入失败')}: {e}")

            # 备用方案：使用tkinter原生绘图
            print(f"[INFO] {language_manager.get_text('chart_testing', '使用tkinter原生绘图作为备用方案')}")
            self._create_native_tkinter_chart(
                chart_frame, data, x_col, y_col, chart_type_key
            )

            return True

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('chart_error', '创建tkinter图表窗口失败')}: {e}")
            return False

    def _embed_matplotlib_chart_with_axis_control(self, parent_frame, data, x_col, y_col, chart_type_key):
        """嵌入matplotlib图表并添加轴长度控制功能 - 修复轴标签版本"""
        try:
            # 动态导入matplotlib避免后端冲突
            import matplotlib
            matplotlib.use('TkAgg', force=True)
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

            # 设置matplotlib支持中文
            plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 创建水平分割的容器
            main_container = tk.Frame(parent_frame, bg='white')
            main_container.pack(fill=tk.BOTH, expand=True)

            # 左侧：图表区域
            chart_container = tk.Frame(main_container, bg='white')
            chart_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

            # 右侧：轴控制面板
            control_container = tk.Frame(main_container, bg='#f8f9fa', width=350)
            control_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
            control_container.pack_propagate(False)

            # 创建图形
            fig, ax = plt.subplots(figsize=(8, 6))

            # [PALETTE] 应用科学期刊样式
            apply_scientific_journal_style(fig, ax)

            # 🔧 修复：检查并使用真实误差数据（支持新的2SE列名）
            error_data = None
            if '2SE' in data.columns:
                error_data = data['2SE']
                print(f"[DEBUG] 发现真实误差列: 2SE")
            elif 'std_error' in data.columns:
                error_data = data['std_error']
                print(f"[DEBUG] 发现真实误差列: std_error")
            elif 'error' in data.columns:
                error_data = data['error']
                print(f"[DEBUG] 发现误差列: error")
            else:
                print(f"[DEBUG] 未发现误差列，可用列: {list(data.columns)}")

            # 智能判断是否需要误差棒和颜色条
            is_analysis_result = self._is_moving_window_result(data, x_col, y_col)

            # 根据类型绘制图表
            if chart_type_key == 'line':
                success = beautify_scientific_line_chart(
                    ax, data[x_col], data[y_col],
                    error_data=error_data,
                    show_error_bars=is_analysis_result
                )
                if not success:
                    raise ValueError("Bootstrap误差棒计算失败，请检查数据源和统计计算")
            elif chart_type_key == 'scatter':
                # [OK] 修复：根据数据类型决定是否显示颜色条
                success = beautify_scientific_scatter_chart(
                    ax, data[x_col], data[y_col],
                    show_colorbar=is_analysis_result,  # 只有分析结果才显示颜色条
                    is_analysis_result=is_analysis_result
                )
                if not success:
                    self._plot_scatter_chart_mpl(ax, data, x_col, y_col)  # 备用方案
            elif chart_type_key == 'bar':
                self._plot_bar_chart_mpl(ax, data, x_col, y_col)
            elif chart_type_key == 'histogram':
                self._plot_histogram_chart_mpl(ax, data, x_col, y_col)

            # 🔧 关键修复：使用动态轴标签
            x_label = self._get_axis_label(x_col)
            y_label = self._get_axis_label(y_col)

            ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
            ax.set_ylabel(y_label, fontsize=12, fontweight='bold')

            # 🔧 修复标题也使用原始列名
            if hasattr(self.main_window, 'analysis_original_columns'):
                original_cols = self.main_window.analysis_original_columns
                if x_col == 'age' and y_col == 'mean':
                    chart_title = f"{original_cols.get('age_column', x_col)} vs {original_cols.get('target_column', y_col)} (Moving Window Analysis)"
                else:
                    chart_title = f"{x_col} vs {y_col}"
            else:
                chart_title = f"{x_col} vs {y_col}"
                if is_analysis_result:
                    chart_title += " (Analysis Result)"

            ax.set_title(chart_title, fontweight='bold', fontsize=14, pad=20)

            plt.tight_layout()

            # 嵌入到tkinter
            canvas = FigureCanvasTkAgg(fig, chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # 添加工具栏
            toolbar_frame = tk.Frame(chart_container)
            toolbar_frame.pack(fill=tk.X)
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()

            # 创建轴长度控制器
            try:
                from interactive.axis_length_control import AxisLengthController

                # 控制面板标题
                control_header = tk.Frame(control_container, bg='#f8f9fa', height=40)
                control_header.pack(fill=tk.X, padx=5, pady=5)
                control_header.pack_propagate(False)

                control_content = tk.Frame(control_container, bg='#f8f9fa')
                control_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

                # 控制面板可见性
                control_visible = tk.BooleanVar(value=True)

                def toggle_control_panel():
                    """切换控制面板显示/隐藏"""
                    if control_visible.get():
                        control_content.pack_forget()
                        toggle_btn.config(text=f"< {language_manager.get_text('show_control', '显示控制')}")
                        control_container.config(width=100)
                        control_visible.set(False)
                    else:
                        control_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
                        toggle_btn.config(text=f"> {language_manager.get_text('hide_control', '隐藏控制')}")
                        control_container.config(width=350)
                        control_visible.set(True)

                toggle_btn = tk.Button(
                    control_header,
                    text=f"> {language_manager.get_text('hide_control', '隐藏控制')}",
                    command=toggle_control_panel,
                    bg='#3b82f6',
                    fg='white',
                    relief='flat',
                    font=('Arial', 9),
                    cursor='hand2'
                )
                toggle_btn.pack(side=tk.RIGHT, padx=(0, 5), pady=5)

                tk.Label(
                    control_header,
                    text=f"[Control] {language_manager.get_text('axis_length_control', '轴长度控制')}",
                    bg='#f8f9fa',
                    font=('Arial', 12, 'bold'),
                    fg='#1e40af'
                ).pack(side=tk.LEFT, padx=5, pady=5)

                # 创建轴长度控制器
                axis_controller = AxisLengthController(
                    control_content, ax, canvas, data, x_col, y_col
                )

                # 存储控制器引用
                setattr(canvas, 'axis_controller', axis_controller)

                print(f"[SUCCESS] {language_manager.get_text('chart_saved', '科学期刊风格图表和轴控制器创建成功')}")

            except ImportError as e:
                print(f"[WARNING] {language_manager.get_text('axis_control_import_failed', '轴控制器导入失败')}: {e}")
                # 在控制面板显示错误信息
                error_label = tk.Label(
                    control_container,
                    text=language_manager.get_text('axis_control_unavailable_check_file',
                                                   '轴控制功能不可用\n请检查 axis_length_control.py'),
                    bg='#fee2e2',
                    fg='#dc2626',
                    font=('Arial', 10),
                    justify=tk.CENTER,
                    padx=20,
                    pady=20
                )
                error_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            return True

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('chart_error', 'matplotlib嵌入失败')}: {e}")
            plt.close('all')  # 清理
            return False

    def _is_moving_window_result(self, data, x_col, y_col):
        """智能判断是否为移动窗口分析结果"""
        try:
            # 方法1：检查列名
            if x_col == 'age' and y_col == 'mean':
                return True

            # 方法2：检查数据是否包含移动窗口分析的特征列
            moving_window_columns = ['std_error', 'sample_count', 'window_low', 'window_high']
            has_analysis_columns = any(col in data.columns for col in moving_window_columns)
            if has_analysis_columns:
                print(f"[DEBUG] 检测到移动窗口分析特征列: {[col for col in moving_window_columns if col in data.columns]}")
                return True

            # 方法3：检查数据点数量（移动窗口结果通常点数较少且规律）
            if len(data) < 200 and x_col.lower() in ['age', 'time'] and 'mean' in y_col.lower():
                return True

            return False
        except Exception as e:
            print(f"[WARNING] 判断数据类型失败: {e}")
            return False

    def _create_native_tkinter_chart(self, parent_frame, data, x_col, y_col, chart_type_key):
        """创建原生tkinter图表（备用方案）"""
        try:
            # 创建Canvas
            chart_canvas = tk.Canvas(parent_frame, bg='white', width=800, height=500)
            chart_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # 获取数据
            x_data = data[x_col].dropna()
            y_data = data[y_col].dropna()

            if len(x_data) == 0 or len(y_data) == 0:
                chart_canvas.create_text(400, 250, text=language_manager.get_text('no_valid_data', '没有有效数据'),
                                 font=('Arial', 16), fill='red')
                return

            # 计算绘图区域
            margin = 60
            plot_width = 800 - 2 * margin
            plot_height = 500 - 2 * margin

            # 数据范围
            x_min, x_max = x_data.min(), x_data.max()
            y_min, y_max = y_data.min(), y_data.max()

            # 添加一些边距
            x_range = x_max - x_min
            y_range = y_max - y_min
            if y_range > 0:
                y_min -= y_range * 0.05
                y_max += y_range * 0.05

            # 绘制坐标轴
            chart_canvas.create_line(margin, 500-margin, 800-margin, 500-margin, width=2, fill='black')
            chart_canvas.create_line(margin, margin, margin, 500-margin, width=2, fill='black')

            # 绘制数据点
            if chart_type_key in ['line', 'scatter'] and x_range > 0 and y_range > 0:
                points = []
                for i in range(min(len(x_data), len(y_data), 1000)):
                    x_val = x_data.iloc[i] if i < len(x_data) else 0
                    y_val = y_data.iloc[i] if i < len(y_data) else 0

                    canvas_x = margin + (x_val - x_min) / x_range * plot_width
                    canvas_y = (500 - margin) - (y_val - y_min) / y_range * plot_height

                    points.extend([canvas_x, canvas_y])

                    # 绘制散点
                    if chart_type_key == 'scatter':
                        chart_canvas.create_oval(canvas_x-3, canvas_y-3, canvas_x+3, canvas_y+3,
                                         fill='#1f4e79', outline='white', width=2)

                # 绘制折线
                if chart_type_key == 'line' and len(points) > 3:
                    # 按X坐标排序
                    point_pairs = [(points[i], points[i+1]) for i in range(0, len(points), 2)]
                    point_pairs.sort(key=lambda p: p[0])
                    sorted_points = []
                    for x, y in point_pairs:
                        sorted_points.extend([x, y])

                    if len(sorted_points) > 3:
                        chart_canvas.create_line(sorted_points, fill='#1f4e79', width=3, smooth=True)

            # 添加标签
            chart_canvas.create_text(400, 480, text=x_col, font=('Arial', 12, 'bold'), fill='#000000')
            chart_canvas.create_text(20, 250, text=y_col, font=('Arial', 12, 'bold'), fill='#000000', angle=90)

            # 标题
            chart_canvas.create_text(400, 30, text=f"[Scientific] {x_col} vs {y_col} ",
                             font=('Arial', 14, 'bold'), fill='#000000')

            print(f"[SUCCESS] 科学期刊风格原生图表创建成功")

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('chart_error', '创建原生tkinter图表失败')}: {e}")

    def _plot_line_chart_mpl(self, ax, data, x_col, y_col):
        """matplotlib折线图 - X轴从小到大排序"""
        data_sorted = data.sort_values(x_col, ascending=True)
        ax.plot(data_sorted[x_col], data_sorted[y_col], 'o-',
                color='#1f4e79', linewidth=2, markersize=4, alpha=0.8)

    def _plot_scatter_chart_mpl(self, ax, data, x_col, y_col):
        """matplotlib散点图 - 简洁单色版本"""
        ax.scatter(data[x_col], data[y_col],
                  color='#1f4e79', alpha=0.75, s=50, edgecolors='black', linewidth=0.6)

    def _plot_bar_chart_mpl(self, ax, data, x_col, y_col):
        """matplotlib柱状图"""
        if len(data) > 20:
            data = data.head(20)
        ax.bar(range(len(data)), data[y_col], alpha=0.8, color='#1f4e79', edgecolor='black')
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(data[x_col], rotation=45, ha='right')

    def _plot_histogram_chart_mpl(self, ax, data, x_col, y_col):
        """matplotlib直方图"""
        y_data = data[y_col].dropna()
        ax.hist(y_data, bins=30, alpha=0.7, color='#1f4e79', edgecolor='black')

    def _get_chart_type_key(self, chart_type_display):
        """根据显示名称获取图表类型key"""
        type_mapping = {
            language_manager.get_text('line_chart', '折线图'): 'line',
            language_manager.get_text('scatter_chart', '散点图'): 'scatter',
            language_manager.get_text('bar_chart', '柱状图'): 'bar',
            language_manager.get_text('histogram', '直方图'): 'histogram'
        }
        return type_mapping.get(chart_type_display, None)

    def _get_axis_label(self, column_name):
        """获取坐标轴标签 - 修复版：支持动态标签和智能单位"""

        # 🔧 关键修复：检查是否是移动窗口分析结果，并使用原始列名
        if hasattr(self.main_window, 'analysis_original_columns'):
            original_cols = self.main_window.analysis_original_columns

            # 如果是age列，使用原始的年龄列名
            if column_name == 'age' and 'age_column' in original_cols:
                original_age_col = original_cols['age_column']
                return f"{original_age_col} (Ma)"

            # 🔧 新增：如果是动态的年龄列名，智能判断是否需要Ma单位
            elif 'age_column' in original_cols and column_name == original_cols['age_column']:
                # 智能判断：只有明确是年龄的列才加Ma单位
                age_keywords = ['AGE', 'TIME', 'YEAR', 'MA', 'DATE']
                col_upper = column_name.upper()
                is_age_column = any(keyword in col_upper for keyword in age_keywords)

                if is_age_column:
                    return f"{column_name} (Ma)"
                else:
                    # 对于Ni、Cu等元素，不加Ma单位
                    return f"{column_name}"

            # 如果是mean列，使用原始的目标列名
            if column_name == 'mean' and 'target_column' in original_cols:
                original_target_col = original_cols['target_column']
                return f"{original_target_col} (mean)"

            # 🔧 新增：如果是动态的目标列名_mean
            elif 'target_column' in original_cols and column_name == f"{original_cols['target_column']}_mean":
                original_target_col = original_cols['target_column']
                return f"{original_target_col} (mean)"

            # 处理median列（新增）
            elif 'target_column' in original_cols and column_name == f"{original_cols['target_column']}_median":
                original_target_col = original_cols['target_column']
                if original_cols.get('is_median_analysis', False):
                    return f"{original_target_col} (median)"
                else:
                    return f"{original_target_col}"

        # 默认的标签映射（保持原有逻辑）
        label_mapping = {
            'AGE': f"{language_manager.get_text('age_column', '年龄')} (Ma)",
            'Age': f"{language_manager.get_text('age_column', '年龄')} (Ma)",
            'age': f"{language_manager.get_text('age_column', '年龄')} (Ma)",
            'mean': language_manager.get_text('calculated_mean', '计算平均值'),
            'SIO2': 'SiO2 (%)',
            'TIO2': 'TiO2 (%)',
            'AL2O3': 'Al2O3 (%)',
            'ThU': 'Th/U',
            'calculated_mean': '计算平均值'
        }
        return label_mapping.get(column_name, column_name)

    def _save_chart_data(self, data, x_col, y_col, chart_type):
        """保存图表数据"""
        try:
            file_path = filedialog.asksaveasfilename(
                title=language_manager.get_text('save_chart', '保存数据'),
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("All files", "*.*")
                ]
            )

            if file_path:
                if file_path.endswith('.csv'):
                    data.to_csv(file_path, index=False, encoding='utf-8-sig')
                elif file_path.endswith('.xlsx'):
                    data.to_excel(file_path, index=False)
                else:
                    data.to_csv(file_path + '.csv', index=False, encoding='utf-8-sig')

                messagebox.showinfo(
                    language_manager.get_text('success', '保存成功'),
                    language_manager.get_text('data_exported', f'数据已保存到: {file_path}')
                )
                print(f"[SUCCESS] {language_manager.get_text('chart_saved', '图表数据已保存到')}: {file_path}")

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('save_error', '保存图表数据失败')}: {e}")
            messagebox.showerror(
                language_manager.get_text('error', '保存失败'),
                language_manager.get_text('save_error', f'保存失败: {str(e)}')
            )

    def _show_chart_data_table(self, data, x_col, y_col):
        """弹出窗口浏览当前图表的数据"""
        try:
            from tksheet import Sheet

            popup = tk.Toplevel()
            popup.title(f"Data View  —  {x_col} vs {y_col}  ({len(data)} rows)")
            popup.geometry("800x500")
            popup.configure(bg='white')

            # 顶部信息
            info_frame = tk.Frame(popup, bg='white')
            info_frame.pack(fill=tk.X, padx=10, pady=(8, 2))
            tk.Label(
                info_frame,
                text=f"Rows: {len(data)}    Columns: {len(data.columns)}",
                font=('Arial', 9),
                fg='#666666',
                bg='white'
            ).pack(side=tk.LEFT)

            # 表格
            sheet_frame = tk.Frame(popup, bg='white')
            sheet_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

            sheet = Sheet(
                sheet_frame,
                font=('Arial', 9, 'normal'),
                header_font=('Arial', 9, 'bold'),
                row_height=22,
                column_width=120,
            )
            sheet.enable_bindings(('single_select', 'drag_select', 'column_width_resize',
                                   'double_click_column_resize', 'arrowkeys', 'copy'))
            sheet.pack(fill=tk.BOTH, expand=True)

            # 填充数据
            display = data.reset_index(drop=True).astype(str).replace('nan', '')
            sheet.headers(list(display.columns))
            sheet.set_sheet_data(display.values.tolist())
            sheet.set_all_column_widths(120)

        except Exception as e:
            print(f"[ERROR] 数据浏览失败: {e}")
            messagebox.showerror("Error", f"Failed to show data: {str(e)}")

    def _export_chart_data(self, data):
        """导出图表数据"""
        self._save_chart_data(data, "", "", "")

    def close_all_charts(self):
        """关闭所有图表窗口"""
        for window in self.chart_windows:
            try:
                window.destroy()
            except:
                pass
        self.chart_windows.clear()

    # 保持兼容性的方法
    def save_chart(self, fig, file_path):
        """保存图表"""
        return True, language_manager.get_text('chart_save_upgraded', '图表保存功能已整合到图表窗口中')

    def export_chart_data(self, data, file_path):
        """导出图表数据"""
        return True, language_manager.get_text('chart_save_upgraded', '数据导出功能已整合到图表窗口中')

    def close_current_chart(self):
        """关闭当前图表"""
        pass

    def get_chart_info(self):
        """获取当前图表信息"""
        return {
            'has_chart': len(self.chart_windows) > 0,
            'data_points': len(self.current_data) if self.current_data is not None else 0,
            'columns': list(self.current_data.columns) if self.current_data is not None else [],
            'chart_windows': len(self.chart_windows)
        }

    def save_current_chart(self):
        """保存当前图表 - 兼容性方法"""
        if self.current_data is not None:
            try:
                self._save_chart_data(self.current_data, "", "", "当前图表")
                return True, language_manager.get_text('chart_saved', '图表数据已保存')
            except Exception as e:
                return False, language_manager.get_text('save_error', f'保存失败: {str(e)}')
        else:
            return False, language_manager.get_text('no_data', '没有图表数据可以保存')


# [PALETTE] 科学期刊配色参考
SCIENTIFIC_JOURNAL_COLORS = {
    # 主要数据系列
    'primary_data': '#1f4e79',      # 深蓝色 - 主要数据
    'secondary_data': '#7c2d12',    # 深棕色 - 次要数据
    'tertiary_data': '#166534',     # 深绿色 - 第三数据系列

    # 误差和不确定性
    'error_bars': '#dc2626',        # 深红色 - 误差棒
    'confidence_band': '#fef3c7',   # 浅黄色 - 置信区间

    # 背景和网格
    'background': '#ffffff',        # 纯白背景
    'grid_major': '#cccccc',        # 主网格线
    'grid_minor': '#dddddd',        # 次网格线
    'axes': '#000000',              # 坐标轴黑色

    # 文字
    'text_primary': '#000000',      # 主要文字
    'text_secondary': '#333333',    # 次要文字
}