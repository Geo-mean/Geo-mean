"""
增强的坐标轴控制模块
提供快速缩放和精确范围控制功能
"""

import tkinter as tk
from tkinter import messagebox


class EnhancedAxisControl:
    """增强的坐标轴控制类"""

    def __init__(self, parent, ax, canvas, chart_data, x_col, y_col):
        self.parent = parent
        self.ax = ax
        self.canvas = canvas
        self.chart_data = chart_data
        self.x_col = x_col
        self.y_col = y_col

        # 存储原始范围
        self.original_xlim = ax.get_xlim()
        self.original_ylim = ax.get_ylim()

        # 创建控制面板
        self.setup_control_panel()

    def setup_control_panel(self):
        """设置增强的控制面板"""
        # 主控制框架
        main_frame = tk.Frame(self.parent, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="[Enhanced] 增强坐标轴控制",
            font=('Segoe UI', 16, 'bold'),
            fg='#2563eb',
            bg='white'
        )
        title_label.pack(pady=(0, 20))

        # 快速缩放按钮区域
        zoom_frame = tk.LabelFrame(main_frame, text="[Quick] 快速缩放", bg='white',
                                  font=('Segoe UI', 10, 'bold'))
        zoom_frame.pack(fill=tk.X, pady=(0, 15))

        zoom_content = tk.Frame(zoom_frame, bg='white', padx=15, pady=10)
        zoom_content.pack(fill=tk.X)

        # 快速缩放按钮
        zoom_buttons = [
            ("全览", self.zoom_to_all, '#3b82f6'),
            ("缩放至数据", self.zoom_to_data, '#059669'),
            ("放大 2x", lambda: self.zoom_factor(0.5), '#d97706'),
            ("缩小 2x", lambda: self.zoom_factor(2.0), '#dc2626'),
            ("重置", self.reset_zoom, '#6b7280')
        ]

        for text, command, color in zoom_buttons:
            btn = tk.Button(
                zoom_content,
                text=text,
                command=command,
                bg=color,
                fg='white',
                relief='flat',
                padx=12,
                pady=6,
                font=('Segoe UI', 9),
                cursor='hand2'
            )
            btn.pack(side=tk.LEFT, padx=(0, 8))

        # 精确范围控制
        range_frame = tk.LabelFrame(main_frame, text="[Precise] 精确范围控制", bg='white',
                                   font=('Segoe UI', 10, 'bold'))
        range_frame.pack(fill=tk.X, pady=(0, 15))

        range_content = tk.Frame(range_frame, bg='white', padx=15, pady=15)
        range_content.pack(fill=tk.X)

        # X轴控制
        x_frame = tk.Frame(range_content, bg='white')
        x_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(x_frame, text=f"X轴 ({self.x_col})", font=('Segoe UI', 9, 'bold'),
                fg='#1e293b', bg='white').pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(x_frame, text="最小值:", bg='white').pack(side=tk.LEFT, padx=(0, 5))
        self.x_min_var = tk.DoubleVar(value=round(self.original_xlim[0], 2))
        x_min_entry = tk.Entry(x_frame, textvariable=self.x_min_var, width=12)
        x_min_entry.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(x_frame, text="最大值:", bg='white').pack(side=tk.LEFT, padx=(0, 5))
        self.x_max_var = tk.DoubleVar(value=round(self.original_xlim[1], 2))
        x_max_entry = tk.Entry(x_frame, textvariable=self.x_max_var, width=12)
        x_max_entry.pack(side=tk.LEFT, padx=(0, 15))

        # Y轴控制
        y_frame = tk.Frame(range_content, bg='white')
        y_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(y_frame, text=f"Y轴 ({self.y_col})", font=('Segoe UI', 9, 'bold'),
                fg='#1e293b', bg='white').pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(y_frame, text="最小值:", bg='white').pack(side=tk.LEFT, padx=(0, 5))
        self.y_min_var = tk.DoubleVar(value=round(self.original_ylim[0], 4))
        y_min_entry = tk.Entry(y_frame, textvariable=self.y_min_var, width=12)
        y_min_entry.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(y_frame, text="最大值:", bg='white').pack(side=tk.LEFT, padx=(0, 5))
        self.y_max_var = tk.DoubleVar(value=round(self.original_ylim[1], 4))
        y_max_entry = tk.Entry(y_frame, textvariable=self.y_max_var, width=12)
        y_max_entry.pack(side=tk.LEFT, padx=(0, 15))

        # 应用按钮
        apply_btn = tk.Button(
            range_content,
            text="[Apply] 应用范围",
            command=self.apply_range,
            bg='#2563eb',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            font=('Segoe UI', 10),
            cursor='hand2'
        )
        apply_btn.pack()

        # 智能建议区域
        suggestion_frame = tk.LabelFrame(main_frame, text="[Smart] 智能建议", bg='white',
                                        font=('Segoe UI', 10, 'bold'))
        suggestion_frame.pack(fill=tk.X, pady=(0, 15))

        suggestion_content = tk.Frame(suggestion_frame, bg='white', padx=15, pady=10)
        suggestion_content.pack(fill=tk.X)

        # 数据统计信息
        self.update_statistics(suggestion_content)

        # 实时更新绑定
        self.x_min_var.trace('w', self.on_range_change)
        self.x_max_var.trace('w', self.on_range_change)
        self.y_min_var.trace('w', self.on_range_change)
        self.y_max_var.trace('w', self.on_range_change)

    def update_statistics(self, parent):
        """更新数据统计信息"""
        try:
            x_data = self.chart_data[self.x_col].dropna()
            y_data = self.chart_data[self.y_col].dropna()

            stats_text = tk.Text(parent, height=6, width=50, bg='#f8f9fa',
                               font=('Consolas', 9), relief='flat')
            stats_text.pack(fill=tk.X)

            stats_info = f"""[Statistics] 数据统计信息
X轴 ({self.x_col}): 范围 {x_data.min():.2f} - {x_data.max():.2f}, 均值 {x_data.mean():.2f}
Y轴 ({self.y_col}): 范围 {y_data.min():.6f} - {y_data.max():.6f}, 均值 {y_data.mean():.6f}
有效数据点: {len(x_data)} 个
建议: 使用"缩放至数据"可自动调整到最佳显示范围"""

            stats_text.insert(tk.END, stats_info)
            stats_text.config(state='disabled')

        except Exception as e:
            print(f"更新统计信息时出错: {e}")

    def zoom_to_all(self):
        """缩放到全部数据"""
        self.ax.autoscale()
        self.canvas.draw()
        self.update_range_vars()

    def zoom_to_data(self):
        """缩放到有效数据范围"""
        try:
            x_data = self.chart_data[self.x_col].dropna()
            y_data = self.chart_data[self.y_col].dropna()

            x_margin = (x_data.max() - x_data.min()) * 0.05
            y_margin = (y_data.max() - y_data.min()) * 0.05

            self.ax.set_xlim(x_data.min() - x_margin, x_data.max() + x_margin)
            self.ax.set_ylim(y_data.min() - y_margin, y_data.max() + y_margin)

            self.canvas.draw()
            self.update_range_vars()

        except Exception as e:
            messagebox.showerror("错误", f"缩放到数据范围失败: {e}")

    def zoom_factor(self, factor):
        """按倍数缩放"""
        try:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2

            x_range = (xlim[1] - xlim[0]) * factor / 2
            y_range = (ylim[1] - ylim[0]) * factor / 2

            self.ax.set_xlim(x_center - x_range, x_center + x_range)
            self.ax.set_ylim(y_center - y_range, y_center + y_range)

            self.canvas.draw()
            self.update_range_vars()

        except Exception as e:
            messagebox.showerror("错误", f"缩放失败: {e}")

    def reset_zoom(self):
        """重置到原始范围"""
        self.ax.set_xlim(self.original_xlim)
        self.ax.set_ylim(self.original_ylim)
        self.canvas.draw()
        self.update_range_vars()

    def apply_range(self):
        """应用用户设置的范围"""
        try:
            self.ax.set_xlim(self.x_min_var.get(), self.x_max_var.get())
            self.ax.set_ylim(self.y_min_var.get(), self.y_max_var.get())
            self.canvas.draw()
            messagebox.showinfo("成功", "坐标轴范围已更新")
        except Exception as e:
            messagebox.showerror("错误", f"应用范围失败: {e}")

    def update_range_vars(self):
        """更新范围变量"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        self.x_min_var.set(round(xlim[0], 2))
        self.x_max_var.set(round(xlim[1], 2))
        self.y_min_var.set(round(ylim[0], 6))
        self.y_max_var.set(round(ylim[1], 6))

    def on_range_change(self, *args):
        """范围变化时的回调"""
        # 可以添加实时预览功能
        pass