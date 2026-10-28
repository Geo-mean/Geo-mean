"""
数据点信息面板模块
显示选中数据点的详细信息
"""

import tkinter as tk
from tkinter import messagebox


class DataPointInfo:
    """数据点信息面板"""

    def __init__(self, parent, tooltip_instance):
        self.parent = parent
        self.tooltip = tooltip_instance
        self.setup_info_panel()

    def setup_info_panel(self):
        """设置信息面板"""
        info_frame = tk.LabelFrame(self.parent, text="[Info] Selected Points", bg='white',
                                   font=('Segoe UI', 10, 'bold'))
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        info_content = tk.Frame(info_frame, bg='white', padx=15, pady=15)
        info_content.pack(fill=tk.BOTH, expand=True)

        # 信息显示区域
        self.info_text = tk.Text(
            info_content,
            height=8,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#f8f9fa',
            relief='flat'
        )
        self.info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 控制按钮
        button_frame = tk.Frame(info_content, bg='white')
        button_frame.pack(fill=tk.X)

        tk.Button(
            button_frame,
            text="[Refresh] Refresh",
            command=self.refresh_info,
            bg='#059669',
            fg='white',
            relief='flat',
            padx=15,
            pady=6,
            font=('Segoe UI', 9),
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            button_frame,
            text="[Clear] Clear Selection",
            command=self.clear_selection,
            bg='#dc2626',
            fg='white',
            relief='flat',
            padx=15,
            pady=6,
            font=('Segoe UI', 9),
            cursor='hand2'
        ).pack(side=tk.LEFT)

        # 初始显示
        self.refresh_info()

    def refresh_info(self):
        """刷新选中点信息"""
        self.info_text.delete(1.0, tk.END)

        if not self.tooltip.selected_points:
            self.info_text.insert(tk.END, "[Help] How to use:\n\n")
            self.info_text.insert(tk.END, "• Hover over a data point to see its details\n")
            self.info_text.insert(tk.END, "• Click a data point to select or deselect it\n")
            self.info_text.insert(tk.END, "• Selected points are highlighted in red\n")
            self.info_text.insert(tk.END, "• You can select several points to compare them\n\n")
            self.info_text.insert(tk.END, "[Status] No data points selected")
        else:
            self.info_text.insert(tk.END, f"[Selected] {len(self.tooltip.selected_points)} data points:\n\n")

            for i, point_idx in enumerate(self.tooltip.selected_points):
                row = self.tooltip.chart_data.iloc[point_idx]
                self.info_text.insert(tk.END, f"Data point #{point_idx + 1}:\n")
                self.info_text.insert(tk.END, f"  {self.tooltip.x_col}: {row[self.tooltip.x_col]}\n")
                self.info_text.insert(tk.END, f"  {self.tooltip.y_col}: {row[self.tooltip.y_col]:.6f}\n")

                if i < len(self.tooltip.selected_points) - 1:
                    self.info_text.insert(tk.END, "\n")

    def clear_selection(self):
        """清除所有选择"""
        # 移除所有高亮
        for artist in self.tooltip.highlight_artists:
            artist.remove()

        self.tooltip.highlight_artists.clear()
        self.tooltip.selected_points.clear()
        self.tooltip.canvas.draw_idle()

        self.refresh_info()
        messagebox.showinfo("Cleared", "All selected data points have been cleared.")