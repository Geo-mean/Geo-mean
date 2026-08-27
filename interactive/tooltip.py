import tkinter as tk
from config.styles import ModernStyle


class InteractiveTooltip:
    """交互式提示工具类"""

    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Motion>", self.on_motion)

    def on_enter(self, event=None):
        """鼠标进入时显示提示"""
        if self.text:
            self.show_tooltip(event)

    def on_leave(self, event=None):
        """鼠标离开时隐藏提示"""
        self.hide_tooltip()

    def on_motion(self, event=None):
        """鼠标移动时更新提示位置"""
        if self.tooltip:
            self.update_tooltip_position(event)

    def show_tooltip(self, event):
        """显示提示框"""
        if self.tooltip:
            return

        x, y = event.x_root + 10, event.y_root + 10

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        self.tooltip.configure(bg='#333333')

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background='#333333',
            foreground='white',
            font=ModernStyle.FONTS['small'],
            relief='solid',
            borderwidth=1,
            padx=8,
            pady=4
        )
        label.pack()

    def hide_tooltip(self):
        """隐藏提示框"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def update_tooltip_position(self, event):
        """更新提示框位置"""
        if self.tooltip:
            x, y = event.x_root + 10, event.y_root + 10
            self.tooltip.wm_geometry(f"+{x}+{y}")

    def update_text(self, new_text):
        """更新提示文本"""
        self.text = new_text