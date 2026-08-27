"""
图表主题配色模块 - ui/chart_themes.py
提供现代化的图表主题和配色方案
"""

import matplotlib.pyplot as plt
import numpy as np
from config.languages import language_manager


class ModernTheme:
    """现代化主题 - 简洁明亮"""

    def __init__(self):
        self.name = "Modern"
        self.colors = {
            'primary': '#2563eb',  # 蓝色
            'secondary': '#7c3aed',  # 紫色
            'accent': '#059669',  # 绿色
            'warning': '#d97706',  # 橙色
            'error': '#dc2626',  # 红色
            'background': '#ffffff',  # 白色背景
            'surface': '#f8fafc',  # 浅灰背景
            'text_primary': '#1e293b',  # 深灰文字
            'text_secondary': '#64748b',  # 中灰文字
            'grid': '#e2e8f0',  # 网格线颜色
            'border': '#cbd5e1'  # 边框颜色
        }

    def apply_style(self, fig, ax):
        """应用现代化样式"""
        # 设置背景色
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['surface'])

        # 设置网格样式
        ax.grid(True, alpha=0.4, linestyle='-', linewidth=0.8, color=self.colors['grid'])
        ax.set_axisbelow(True)

        # 设置坐标轴样式
        for spine in ax.spines.values():
            spine.set_linewidth(1.5)
            spine.set_color(self.colors['border'])
            spine.set_alpha(0.8)

        # 设置刻度样式
        ax.tick_params(
            colors=self.colors['text_secondary'],
            labelsize=11,
            direction='out',
            length=6,
            width=1.2
        )

        # 设置标签样式
        ax.xaxis.label.set_color(self.colors['text_primary'])
        ax.yaxis.label.set_color(self.colors['text_primary'])
        ax.title.set_color(self.colors['text_primary'])

        # 设置字体
        ax.xaxis.label.set_fontsize(12)
        ax.yaxis.label.set_fontsize(12)
        ax.title.set_fontsize(14)
        ax.title.set_fontweight('bold')

    def get_line_style(self):
        """获取折线图样式"""
        return {
            'color': self.colors['primary'],
            'linewidth': 3.0,
            'marker': 'o',
            'markersize': 8,
            'markerfacecolor': self.colors['secondary'],
            'markeredgecolor': 'white',
            'markeredgewidth': 2.0,
            'alpha': 0.9
        }

    def get_scatter_style(self):
        """获取散点图样式"""
        return {
            'c': self.colors['primary'],
            's': 80,
            'alpha': 0.8,
            'edgecolors': 'white',
            'linewidth': 1.5
        }


class ScientificTheme:
    """科学研究主题 - 专业严谨"""

    def __init__(self):
        self.name = "Scientific"
        self.colors = {
            'primary': '#1e40af',  # 深蓝
            'secondary': '#7c2d12',  # 深棕
            'accent': '#166534',  # 深绿
            'background': '#ffffff',
            'surface': '#fefefe',
            'text_primary': '#111827',
            'text_secondary': '#4b5563',
            'grid': '#d1d5db',
            'error_bar': '#ef4444'
        }

    def apply_style(self, fig, ax):
        """应用科学研究样式"""
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['surface'])

        # 更精细的网格
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8, color=self.colors['grid'])
        ax.minorticks_on()
        ax.grid(True, which='minor', alpha=0.15, linestyle=':', linewidth=0.5)
        ax.set_axisbelow(True)

        # 专业的坐标轴
        for spine in ax.spines.values():
            spine.set_linewidth(1.8)
            spine.set_color('#374151')

        ax.tick_params(
            colors=self.colors['text_secondary'],
            labelsize=11,
            direction='out',
            length=8,
            width=1.5
        )

    def get_line_style(self):
        """获取折线图样式"""
        return {
            'color': self.colors['primary'],
            'linewidth': 2.5,
            'marker': 's',
            'markersize': 6,
            'markerfacecolor': self.colors['accent'],
            'markeredgecolor': self.colors['text_primary'],
            'markeredgewidth': 1.0,
            'alpha': 0.95
        }


class ElegantTheme:
    """优雅主题 - 高端商务风"""

    def __init__(self):
        self.name = "Elegant"
        self.colors = {
            'primary': '#0f172a',  # 深蓝黑
            'secondary': '#64748b',  # 石板灰
            'accent': '#0ea5e9',  # 天蓝色
            'gold': '#f59e0b',  # 金色
            'background': '#ffffff',
            'surface': '#f8fafc',
            'text_primary': '#0f172a',
            'text_secondary': '#475569',
            'grid': '#e2e8f0'
        }

    def apply_style(self, fig, ax):
        """应用优雅样式"""
        fig.patch.set_facecolor(self.colors['background'])
        ax.set_facecolor(self.colors['surface'])

        # 精致的网格
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=1.0, color=self.colors['grid'])
        ax.set_axisbelow(True)

        # 优雅的坐标轴
        for spine in ax.spines.values():
            spine.set_linewidth(2.0)
            spine.set_color(self.colors['secondary'])

        ax.tick_params(
            colors=self.colors['text_secondary'],
            labelsize=12,
            direction='out',
            length=7,
            width=1.5
        )

    def get_line_style(self):
        """获取折线图样式"""
        return {
            'color': self.colors['primary'],
            'linewidth': 3.5,
            'marker': 'D',
            'markersize': 7,
            'markerfacecolor': self.colors['gold'],
            'markeredgecolor': self.colors['primary'],
            'markeredgewidth': 1.5,
            'alpha': 0.9
        }


class ChartThemeManager:
    """图表主题管理器"""

    def __init__(self):
        self.themes = {
            'modern': ModernTheme(),
            'scientific': ScientificTheme(),
            'elegant': ElegantTheme()
        }
        self.current_theme = 'modern'

    def get_theme(self, theme_name=None):
        """获取主题"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes['modern'])

    def set_theme(self, theme_name):
        """设置当前主题"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False

    def get_available_themes(self):
        """获取可用主题列表"""
        theme_names = {
            'modern': language_manager.get_text('modern_theme', '现代主题'),
            'scientific': language_manager.get_text('scientific_theme', '科学主题'),
            'elegant': language_manager.get_text('elegant_theme', '优雅主题')
        }
        return theme_names

    def apply_theme(self, fig, ax, theme_name=None):
        """应用主题到图表"""
        theme = self.get_theme(theme_name)
        theme.apply_style(fig, ax)
        return theme


class ChartBeautifier:
    """图表美化器"""

    def __init__(self, theme_manager=None):
        self.theme_manager = theme_manager or ChartThemeManager()

    def beautify_line_chart(self, ax, x_data, y_data, theme_name=None, add_fill=True):
        """美化折线图"""
        theme = self.theme_manager.get_theme(theme_name)
        line_style = theme.get_line_style()

        # 数据排序
        sorted_indices = np.argsort(x_data)
        x_sorted = x_data.iloc[sorted_indices] if hasattr(x_data, 'iloc') else np.array(x_data)[sorted_indices]
        y_sorted = y_data.iloc[sorted_indices] if hasattr(y_data, 'iloc') else np.array(y_data)[sorted_indices]

        # 绘制主线条
        line = ax.plot(x_sorted, y_sorted, **line_style, zorder=5)

        # 添加填充区域
        if add_fill and len(x_sorted) > 1:
            ax.fill_between(x_sorted, y_sorted, alpha=0.2,
                            color=line_style['color'], zorder=1)

        return line

    def beautify_scatter_chart(self, ax, x_data, y_data, theme_name=None, colormap='viridis'):
        """美化散点图"""
        theme = self.theme_manager.get_theme(theme_name)

        # 创建颜色映射
        if len(y_data) > 1:
            c_values = (y_data - np.min(y_data)) / (np.max(y_data) - np.min(y_data))
        else:
            c_values = [0.5] * len(y_data)

        scatter = ax.scatter(x_data, y_data,
                             c=c_values,
                             cmap=colormap,
                             s=100,
                             alpha=0.8,
                             edgecolors='white',
                             linewidth=2.0,
                             zorder=5)

        return scatter

    def add_error_bars(self, ax, x_data, y_data, errors, theme_name=None):
        """添加误差棒"""
        theme = self.theme_manager.get_theme(theme_name)

        ax.errorbar(x_data, y_data, yerr=errors,
                    fmt='none',
                    ecolor=theme.colors.get('error_bar', '#ef4444'),
                    capsize=6,
                    capthick=2.5,
                    alpha=0.8,
                    zorder=3)

    def enhance_labels(self, ax, x_col, y_col, title=None):
        """增强标签显示"""
        # 设置坐标轴标签
        ax.set_xlabel(x_col, fontweight='bold', fontsize=13, labelpad=12)
        ax.set_ylabel(y_col, fontweight='bold', fontsize=13, labelpad=12)

        # 设置标题
        if title:
            ax.set_title(title, fontweight='bold', fontsize=15, pad=25)

        # 自动调整刻度格式
        ax.ticklabel_format(useOffset=False, style='plain')


# 创建全局实例
theme_manager = ChartThemeManager()
beautifier = ChartBeautifier(theme_manager)