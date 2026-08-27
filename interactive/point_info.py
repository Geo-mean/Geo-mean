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
        info_frame = tk.LabelFrame(self.parent, text="[Info] 选中数据点信息", bg='white',
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
            text="[Refresh] 刷新信息",
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
            text="[Clear] 清除选择",
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
            self.info_text.insert(tk.END, "[Help] 使用说明:\n\n")
            self.info_text.insert(tk.END, "• 鼠标悬停在数据点上查看详细信息\n")
            self.info_text.insert(tk.END, "• 点击数据点进行选择/取消选择\n")
            self.info_text.insert(tk.END, "• 选中的数据点会以红色高亮显示\n")
            self.info_text.insert(tk.END, "• 可同时选择多个数据点进行对比\n\n")
            self.info_text.insert(tk.END, "[Status] 当前未选择任何数据点")
        else:
            self.info_text.insert(tk.END, f"[Selected] 已选择 {len(self.tooltip.selected_points)} 个数据点:\n\n")

            for i, point_idx in enumerate(self.tooltip.selected_points):
                row = self.tooltip.chart_data.iloc[point_idx]
                self.info_text.insert(tk.END, f"数据点 #{point_idx + 1}:\n")
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
        messagebox.showinfo("清除完成", "已清除所有选中的数据点")