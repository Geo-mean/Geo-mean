"""
修复版地球化学分析对话框 - ui/geochem_analysis_dialog.py
确保确认按钮正确显示，完全符合模块化架构和语言管理器规范
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional
from config.languages import language_manager


def show_simplified_geochem_analysis_dialog(parent, numeric_columns: List[str]) -> Optional[Dict]:
    """
    显示简化版地球化学移动窗口分析对话框

    Args:
        parent: 父窗口
        numeric_columns: 数值列列表

    Returns:
        分析参数字典，如果用户取消则返回None
    """

    class ImprovedAnalysisDialog:
        def __init__(self, parent, numeric_columns):
            self.parent = parent
            self.numeric_columns = numeric_columns
            self.result = None

            # 创建对话框窗口
            self.dialog = tk.Toplevel(parent)
            self.dialog.title(f"[Lab] {language_manager.get_text('moving_window_analysis', '移动窗口分析')}")
            self.dialog.geometry("600x500")  # 增加高度确保按钮显示
            self.dialog.resizable(False, False)
            self.dialog.grab_set()
            self.dialog.configure(bg='white')

            # 居中显示
            self._center_window()

            # 初始化变量
            self._init_variables()

            # 创建界面
            self._create_widgets()

            # 绑定事件
            self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        def _center_window(self):
            """居中显示窗口"""
            self.dialog.update_idletasks()
            width = 600
            height = 500
            x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
            self.dialog.geometry(f"{width}x{height}+{x}+{y}")

        def _init_variables(self):
            """初始化变量"""
            self.age_column_var = tk.StringVar()
            self.target_column_var = tk.StringVar()
            self.min_age_var = tk.StringVar(value="100")
            self.max_age_var = tk.StringVar(value="4000")
            self.window_size_var = tk.StringVar(value="200")
            self.step_size_var = tk.StringVar(value="50")

            # 自动选择合适的列
            self._auto_select_columns()

        def _auto_select_columns(self):
            """自动选择合适的列"""
            # 尝试找到年龄列
            age_candidates = ['AGE', 'AGES', 'YEAR', 'YEARS', 'MA', 'TIME']
            for candidate in age_candidates:
                matches = [col for col in self.numeric_columns if candidate in col.upper()]
                if matches:
                    self.age_column_var.set(matches[0])
                    break

            # 如果没找到年龄列，设置第一个数值列
            if not self.age_column_var.get() and self.numeric_columns:
                self.age_column_var.set(self.numeric_columns[0])

            # 尝试找到ThU列
            thu_candidates = ['THU', 'TH_U', 'TH/U', 'TH U', 'THORIUM_URANIUM']
            for candidate in thu_candidates:
                matches = [col for col in self.numeric_columns
                          if candidate in col.upper().replace('/', '_').replace(' ', '_')]
                if matches:
                    self.target_column_var.set(matches[0])
                    break

            # 如果没找到ThU列，设置第二个数值列
            if not self.target_column_var.get() and len(self.numeric_columns) > 1:
                self.target_column_var.set(self.numeric_columns[1])
            elif not self.target_column_var.get() and self.numeric_columns:
                self.target_column_var.set(self.numeric_columns[0])

        def _create_widgets(self):
            """创建界面组件"""
            # 主框架
            main_frame = tk.Frame(self.dialog, bg='white')
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # 标题
            title_label = tk.Label(
                main_frame,
                text=f"[Lab] {language_manager.get_text('moving_window_analysis', '移动窗口分析')}",
                font=('Arial', 16, 'bold'),
                bg='white',
                fg='#2c3e50'
            )
            title_label.pack(pady=(0, 10))

            # 顶部按钮区域 - 放在标题下方
            self._create_top_buttons(main_frame)

            # 数据列选择部分
            self._create_column_selection_section(main_frame)

            # 移动窗口参数部分
            self._create_window_parameters_section(main_frame)

        def _create_column_selection_section(self, parent):
            """创建数据列选择部分"""
            section_frame = tk.LabelFrame(
                parent,
                text=f"[1] {language_manager.get_text('data_column_selection', '数据列选择')}",
                font=('Arial', 12, 'bold'),
                bg='white',
                padx=15,
                pady=10
            )
            section_frame.pack(fill=tk.X, pady=(0, 10))

            # 年龄列选择
            age_frame = tk.Frame(section_frame, bg='white')
            age_frame.pack(fill=tk.X, pady=5)

            tk.Label(
                age_frame,
                text=f"{language_manager.get_text('age_column', '年龄列')}:",
                font=('Arial', 10),
                bg='white',
                width=12,
                anchor='w'
            ).pack(side=tk.LEFT)

            age_combo = ttk.Combobox(
                age_frame,
                textvariable=self.age_column_var,
                values=self.numeric_columns,
                state="readonly",
                width=20
            )
            age_combo.pack(side=tk.LEFT, padx=10)

            # 目标列选择
            target_frame = tk.Frame(section_frame, bg='white')
            target_frame.pack(fill=tk.X, pady=5)

            tk.Label(
                target_frame,
                text=f"{language_manager.get_text('target_column', '目标列')}:",
                font=('Arial', 10),
                bg='white',
                width=12,
                anchor='w'
            ).pack(side=tk.LEFT)

            target_combo = ttk.Combobox(
                target_frame,
                textvariable=self.target_column_var,
                values=self.numeric_columns,
                state="readonly",
                width=20
            )
            target_combo.pack(side=tk.LEFT, padx=10)

            # 说明文字
            help_label = tk.Label(
                section_frame,
                text=language_manager.get_text('auto_detection_help', '系统会自动检测合适的数据列'),
                font=('Arial', 9),
                bg='white',
                fg='#666666'
            )
            help_label.pack(pady=(5, 0))

        def _create_window_parameters_section(self, parent):
            """创建移动窗口参数部分"""
            section_frame = tk.LabelFrame(
                parent,
                text=f"[2] {language_manager.get_text('window_parameters', '窗口参数')}",
                font=('Arial', 12, 'bold'),
                bg='white',
                padx=15,
                pady=10
            )
            section_frame.pack(fill=tk.X, pady=(0, 10))

            # 年龄范围
            range_frame = tk.Frame(section_frame, bg='white')
            range_frame.pack(fill=tk.X, pady=5)

            tk.Label(
                range_frame,
                text=f"{language_manager.get_text('age_range', '年龄范围')} (Ma):",
                font=('Arial', 10),
                bg='white',
                width=18,
                anchor='w'
            ).pack(side=tk.LEFT)

            tk.Entry(
                range_frame,
                textvariable=self.min_age_var,
                width=8,
                font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=5)

            tk.Label(range_frame, text=" - ", bg='white').pack(side=tk.LEFT)

            tk.Entry(
                range_frame,
                textvariable=self.max_age_var,
                width=8,
                font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=5)

            # 窗口大小
            window_frame = tk.Frame(section_frame, bg='white')
            window_frame.pack(fill=tk.X, pady=5)

            tk.Label(
                window_frame,
                text=f"{language_manager.get_text('window_size', '窗口大小')} (Ma):",
                font=('Arial', 10),
                bg='white',
                width=18,
                anchor='w'
            ).pack(side=tk.LEFT)

            tk.Entry(
                window_frame,
                textvariable=self.window_size_var,
                width=10,
                font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=10)

            # 步长
            step_frame = tk.Frame(section_frame, bg='white')
            step_frame.pack(fill=tk.X, pady=5)

            tk.Label(
                step_frame,
                text=f"{language_manager.get_text('step_size', '移动步长')} (Ma):",
                font=('Arial', 10),
                bg='white',
                width=18,
                anchor='w'
            ).pack(side=tk.LEFT)

            tk.Entry(
                step_frame,
                textvariable=self.step_size_var,
                width=10,
                font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=10)

            # Bootstrap说明
            bootstrap_label = tk.Label(
                section_frame,
                text=language_manager.get_text('bootstrap_info', '使用10,000次Bootstrap重采样计算统计误差'),
                font=('Arial', 9),
                bg='white',
                fg='#666666'
            )
            bootstrap_label.pack(pady=(5, 0))

        def _create_analysis_info_section(self, parent):
            """创建分析信息显示区域"""
            info_frame = tk.LabelFrame(
                parent,
                text=f"[3] {language_manager.get_text('analysis_parameters', '分析参数')}",
                font=('Arial', 12, 'bold'),
                bg='white',
                padx=15,
                pady=10
            )
            info_frame.pack(fill=tk.X, pady=(0, 10))

            # 分析信息标签
            self.info_label = tk.Label(
                info_frame,
                text="",
                font=('Arial', 9),
                bg='white',
                fg='#666666',
                justify=tk.LEFT
            )
            self.info_label.pack(anchor=tk.W, pady=5)

            # 绑定参数变化事件（移除分析信息更新）
            # 注释掉原来的实时更新功能，因为已删除分析参数区域
            # self._bind_parameter_events()
            # self._update_analysis_info()

        def _create_top_buttons(self, parent):
            """创建顶部按钮区域 - 放在标题下方"""
            # 按钮容器框架
            button_container = tk.Frame(parent, bg='white')
            button_container.pack(fill=tk.X, pady=(0, 20))

            # 分隔线
            separator = tk.Frame(button_container, height=1, bg='#e0e0e0')
            separator.pack(fill=tk.X, pady=(0, 10))

            # 按钮框架
            button_frame = tk.Frame(button_container, bg='white')
            button_frame.pack(fill=tk.X)

            # 状态提示（左侧）
            status_label = tk.Label(
                button_frame,
                text=language_manager.get_text('ready_for_analysis', '准备就绪，点击开始分析'),
                font=('Arial', 9),
                bg='white',
                fg='#28a745'
            )
            status_label.pack(side=tk.LEFT)

            # 取消按钮（右侧）
            cancel_btn = tk.Button(
                button_frame,
                text=language_manager.get_text('cancel', '取消'),
                command=self._on_cancel,
                bg='#6c757d',
                fg='white',
                font=('Arial', 10),
                cursor='hand2',
                padx=15,
                pady=6,
                relief=tk.FLAT
            )
            cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))

            # 确认按钮（右侧）
            confirm_btn = tk.Button(
                button_frame,
                text=language_manager.get_text('start_analysis', '开始分析'),
                command=self._on_confirm,
                bg='#4A90E2',
                fg='white',
                font=('Arial', 10, 'bold'),
                cursor='hand2',
                padx=15,
                pady=6,
                relief=tk.FLAT
            )
            confirm_btn.pack(side=tk.RIGHT, padx=(10, 0))

            # 添加分隔线
            separator2 = tk.Frame(button_container, height=1, bg='#e0e0e0')
            separator2.pack(fill=tk.X, pady=(10, 0))

        def _bind_parameter_events(self):
            """绑定参数变化事件"""
            self.min_age_var.trace('w', lambda *args: self._update_analysis_info())
            self.max_age_var.trace('w', lambda *args: self._update_analysis_info())
            self.window_size_var.trace('w', lambda *args: self._update_analysis_info())
            self.step_size_var.trace('w', lambda *args: self._update_analysis_info())

        def _update_analysis_info(self):
            """更新分析信息"""
            try:
                min_age = float(self.min_age_var.get())
                max_age = float(self.max_age_var.get())
                window_size = float(self.window_size_var.get())
                step_size = float(self.step_size_var.get())

                # 计算窗口数
                if step_size > 0 and max_age > min_age:
                    total_windows = max(1, int((max_age - min_age) / step_size) + 1)
                else:
                    total_windows = 0

                # 估算时间
                if total_windows <= 50:
                    time_est = language_manager.get_text('less_than_1_minute', '< 1分钟')
                elif total_windows <= 200:
                    time_est = language_manager.get_text('1_3_minutes', '1-3分钟')
                elif total_windows <= 500:
                    time_est = language_manager.get_text('3_10_minutes', '3-10分钟')
                else:
                    time_est = language_manager.get_text('more_than_10_minutes', '> 10分钟')

                info_text = f"{language_manager.get_text('estimated_windows', '预计窗口数')}: {total_windows:,}\n"
                info_text += f"{language_manager.get_text('bootstrap_samples', 'Bootstrap采样')}: {total_windows * 10000:,}\n"
                info_text += f"{language_manager.get_text('estimated_time', '预计时间')}: {time_est}"

                if hasattr(self, 'info_label'):
                    self.info_label.configure(text=info_text)

            except (ValueError, ZeroDivisionError):
                if hasattr(self, 'info_label'):
                    self.info_label.configure(
                        text=language_manager.get_text('please_set_analysis_parameters', '请设置分析参数')
                    )

        def _validate_parameters(self):
            """验证参数"""
            # 检查列选择
            if not self.age_column_var.get():
                return False, language_manager.get_text('please_select_age_column', '请选择年龄列')

            if not self.target_column_var.get():
                return False, language_manager.get_text('please_select_target_column', '请选择目标列')

            if self.age_column_var.get() == self.target_column_var.get():
                return False, language_manager.get_text('age_target_columns_different', '年龄列和目标列不能相同')

            # 检查数值参数
            try:
                min_age = float(self.min_age_var.get())
                max_age = float(self.max_age_var.get())
                window_size = float(self.window_size_var.get())
                step_size = float(self.step_size_var.get())

                if min_age >= max_age:
                    return False, language_manager.get_text('min_age_less_than_max', '最小年龄必须小于最大年龄')

                if window_size <= 0:
                    return False, language_manager.get_text('window_size_greater_than_zero', '窗口大小必须大于0')

                if step_size <= 0:
                    return False, language_manager.get_text('step_size_greater_than_zero', '步长必须大于0')

                if window_size >= (max_age - min_age):
                    return False, language_manager.get_text('window_size_not_exceed_age_range', '窗口大小不能超过年龄范围')

            except ValueError:
                return False, language_manager.get_text('enter_valid_numeric_values', '请输入有效的数值')

            return True, language_manager.get_text('parameter_validation_passed', '参数验证通过')

        def _get_parameters(self):
            """获取分析参数"""
            min_age = float(self.min_age_var.get())
            max_age = float(self.max_age_var.get())
            window_size = float(self.window_size_var.get())
            step_size = float(self.step_size_var.get())

            # 计算预计窗口数
            estimated_windows = max(1, int((max_age - min_age) / step_size) + 1)

            return {
                'age_column': self.age_column_var.get(),
                'target_column': self.target_column_var.get(),
                'min_age': min_age,
                'max_age': max_age,
                'window_size': window_size,
                'step_size': step_size,
                'estimated_windows': estimated_windows,
                'enable_geochem_filter': False,  # 简化版不包含地球化学筛选
                'enable_outlier_removal': False  # 简化版不包含异常值处理
            }

        def _on_confirm(self):
            """确认按钮事件 - 完全符合模块化和语言管理器"""
            try:
                # 验证参数
                is_valid, message = self._validate_parameters()

                if not is_valid:
                    messagebox.showerror(
                        language_manager.get_text('parameter_error', '参数错误'),
                        message
                    )
                    return

                # 获取参数
                params = self._get_parameters()

                # 显示确认对话框
                confirm_text = self._build_confirmation_text(params)

                if messagebox.askyesno(
                        language_manager.get_text('confirm_analysis', '确认分析'),
                        confirm_text
                ):
                    self.result = params
                    self.dialog.destroy()

            except Exception as e:
                messagebox.showerror(
                    language_manager.get_text('error', '错误'),
                    f"{language_manager.get_text('start_analysis_failed', '启动分析失败')}: {str(e)}"
                )

        def _build_confirmation_text(self, params):
            """构建确认文本 - 使用语言管理器"""
            # 简化确认文本，不显示实时计算的信息
            confirm_text = f"""{language_manager.get_text('confirm_analysis_parameters', '确认分析参数')}:

{language_manager.get_text('age_column', '年龄列')}: {params['age_column']}
{language_manager.get_text('target_column', '目标列')}: {params['target_column']}
{language_manager.get_text('age_range', '年龄范围')}: {params['min_age']:.0f} - {params['max_age']:.0f} Ma
{language_manager.get_text('window_size', '窗口大小')}: {params['window_size']:.0f} Ma
{language_manager.get_text('step_size', '步长')}: {params['step_size']:.0f} Ma

{language_manager.get_text('confirm_start_analysis', '确定要开始分析吗')}？"""

            return confirm_text

        def _on_cancel(self):
            """取消按钮事件"""
            self.result = None
            self.dialog.destroy()

        def get_result(self):
            """获取对话框结果"""
            return self.result

    # 创建对话框实例
    dialog = ImprovedAnalysisDialog(parent, numeric_columns)
    parent.wait_window(dialog.dialog)
    return dialog.get_result()


# 测试代码
if __name__ == "__main__":
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()

    # 模拟数值列
    test_columns = ['AGE', 'SiO2', 'ThU', 'Lg_NbTh', 'Lg_Th', 'LOI', 'TiO2', 'Al2O3']

    result = show_simplified_geochem_analysis_dialog(root, test_columns)

    if result:
        print("用户选择的参数:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        print("用户取消了分析")

    root.destroy()