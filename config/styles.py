import tkinter as tk
from tkinter import ttk


# 延迟导入matplotlib，避免在模块检查时就设置后端
def configure_matplotlib():
    """配置matplotlib设置"""
    try:
        import matplotlib
        matplotlib.use('TkAgg', force=True)
        import matplotlib.pyplot as plt

        # 设置中文字体支持和美化样式
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams['axes.facecolor'] = '#f8f9fa'
        plt.rcParams['grid.alpha'] = 0.3
        plt.rcParams['grid.linewidth'] = 0.8
        plt.rcParams['axes.linewidth'] = 1.2
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14

        print("[INFO] matplotlib配置完成")

    except Exception as e:
        print(f"[WARNING] matplotlib配置失败: {e}")


class ModernStyle:
    """现代化样式配置"""

    # 配色方案
    COLORS = {
        'primary': '#2563eb',  # 蓝色主色调
        'secondary': '#7c3aed',  # 紫色次要色
        'success': '#059669',  # 绿色成功色
        'warning': '#d97706',  # 橙色警告色
        'danger': '#dc2626',  # 红色危险色
        'info': '#0891b2',  # 青色信息色
        'light': '#f8fafc',  # 浅灰背景
        'dark': '#1e293b',  # 深色文字
        'muted': '#64748b',  # 灰色文字
        'border': '#e2e8f0',  # 边框色
        'gradient_start': '#3b82f6',
        'gradient_end': '#8b5cf6'
    }

    # 字体配置
    FONTS = {
        'title': ('Segoe UI', 16, 'bold'),
        'heading': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 10),
        'small': ('Segoe UI', 9),
        'mono': ('Consolas', 10)
    }

    @staticmethod
    def configure_ttk_styles():
        """配置ttk样式"""
        style = ttk.Style()

        # 配置按钮样式
        style.configure('Modern.TButton',
                        background=ModernStyle.COLORS['primary'],
                        foreground='white',
                        borderwidth=0,
                        focuscolor='none',
                        padding=(15, 8))

        style.map('Modern.TButton',
                  background=[('active', '#1d4ed8'),
                              ('pressed', '#1e40af')])

        # 成功按钮
        style.configure('Success.TButton',
                        background=ModernStyle.COLORS['success'],
                        foreground='white',
                        borderwidth=0,
                        focuscolor='none',
                        padding=(15, 8))

        # 警告按钮
        style.configure('Warning.TButton',
                        background=ModernStyle.COLORS['warning'],
                        foreground='white',
                        borderwidth=0,
                        focuscolor='none',
                        padding=(10, 6))

        # 现代化LabelFrame
        style.configure('Modern.TLabelframe',
                        background='white',
                        borderwidth=1,
                        relief='solid')

        style.configure('Modern.TLabelframe.Label',
                        background='white',
                        foreground=ModernStyle.COLORS['dark'],
                        font=ModernStyle.FONTS['heading'])

        # 现代化Entry
        style.configure('Modern.TEntry',
                        fieldbackground='white',
                        borderwidth=1,
                        relief='solid',
                        padding=8)

        # 现代化Combobox
        style.configure('Modern.TCombobox',
                        fieldbackground='white',
                        borderwidth=1,
                        relief='solid',
                        padding=8)

    @staticmethod
    def initialize_all():
        """初始化所有样式配置"""
        try:
            ModernStyle.configure_ttk_styles()
            configure_matplotlib()
            print("[SUCCESS] 所有样式配置完成")
        except Exception as e:
            print(f"[ERROR] 样式配置失败: {e}")