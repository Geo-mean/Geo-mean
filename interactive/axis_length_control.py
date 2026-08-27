"""
最简洁的轴长度控制模块 - interactive/axis_length_control.py
仅保留手动数值输入功能，符合语言管理器
"""

import tkinter as tk
from tkinter import messagebox
from config.languages import language_manager


class AxisLengthController:
    """最简洁的轴长度控制器 - 仅手动数值输入"""

    def __init__(self, parent, ax, canvas, chart_data, x_col, y_col):
        self.ax = ax
        self.canvas = canvas
        self.x_col = x_col
        self.y_col = y_col
        self.chart_data = chart_data  # 保存数据引用
        self.parent_root = parent.winfo_toplevel()  # 顶层窗口引用

        # 获取当前轴范围
        self.current_xlim = list(ax.get_xlim())
        self.current_ylim = list(ax.get_ylim())

        # 创建输入控件
        self.create_input_controls(parent)

    def create_input_controls(self, parent):
        """创建输入控件"""
        # 主容器
        control_frame = tk.Frame(parent, bg='white', relief=tk.RIDGE, bd=1)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 内容容器
        content_frame = tk.Frame(control_frame, bg='white', padx=10, pady=8)
        content_frame.pack(fill=tk.X)

        # 标题
        title_label = tk.Label(
            content_frame,
            text=language_manager.get_text('axis_length_control', '轴长度控制'),
            font=('Arial', 11, 'bold'),
            bg='white',
            fg='#1f2937'
        )
        title_label.pack(pady=(0, 8))

        # 输入区域
        input_container = tk.Frame(content_frame, bg='white')
        input_container.pack()

        # X轴控制
        x_frame = tk.Frame(input_container, bg='white')
        x_frame.pack(side=tk.LEFT, padx=(0, 20))

        tk.Label(x_frame, text=f"{language_manager.get_text('x_axis', 'X轴')}:",
                bg='white', font=('Arial', 9, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 5))

        tk.Label(x_frame, text=language_manager.get_text('min_value', '最小值'),
                bg='white', font=('Arial', 9)).grid(row=1, column=0, padx=(0, 5), sticky='e')
        self.x_min_entry = tk.Entry(x_frame, width=10, font=('Consolas', 9))
        self.x_min_entry.grid(row=1, column=1, pady=2)
        self.x_min_entry.insert(0, f"{self.current_xlim[0]:.3f}")

        tk.Label(x_frame, text=language_manager.get_text('max_value', '最大值'),
                bg='white', font=('Arial', 9)).grid(row=2, column=0, padx=(0, 5), sticky='e')
        self.x_max_entry = tk.Entry(x_frame, width=10, font=('Consolas', 9))
        self.x_max_entry.grid(row=2, column=1, pady=2)
        self.x_max_entry.insert(0, f"{self.current_xlim[1]:.3f}")

        # Y轴控制
        y_frame = tk.Frame(input_container, bg='white')
        y_frame.pack(side=tk.LEFT, padx=(20, 0))

        tk.Label(y_frame, text=f"{language_manager.get_text('y_axis', 'Y轴')}:",
                bg='white', font=('Arial', 9, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 5))

        tk.Label(y_frame, text=language_manager.get_text('min_value', '最小值'),
                bg='white', font=('Arial', 9)).grid(row=1, column=0, padx=(0, 5), sticky='e')
        self.y_min_entry = tk.Entry(y_frame, width=10, font=('Consolas', 9))
        self.y_min_entry.grid(row=1, column=1, pady=2)
        self.y_min_entry.insert(0, f"{self.current_ylim[0]:.6f}")

        tk.Label(y_frame, text=language_manager.get_text('max_value', '最大值'),
                bg='white', font=('Arial', 9)).grid(row=2, column=0, padx=(0, 5), sticky='e')
        self.y_max_entry = tk.Entry(y_frame, width=10, font=('Consolas', 9))
        self.y_max_entry.grid(row=2, column=1, pady=2)
        self.y_max_entry.insert(0, f"{self.current_ylim[1]:.6f}")

        # 按钮区域容器，统一宽度
        btn_frame = tk.Frame(content_frame, bg='white')
        btn_frame.pack(fill=tk.X, padx=10, pady=(10, 4))

        apply_btn = tk.Button(
            btn_frame,
            text=language_manager.get_text('apply_axis_range', '应用轴范围'),
            command=self.apply_range,
            bg='#3b82f6', fg='white',
            font=('Arial', 10, 'bold'),
            cursor='hand2', pady=5, relief=tk.FLAT, bd=0
        )
        apply_btn.pack(fill=tk.X, pady=(0, 4))

        tk.Frame(btn_frame, height=1, bg='#e5e7eb').pack(fill=tk.X, pady=(4, 4))

        save_btn = tk.Button(
            btn_frame,
            text="Save Chart",
            command=self._save_chart,
            bg='#3b82f6', fg='white',
            font=('Arial', 10, 'bold'),
            cursor='hand2', pady=5, relief=tk.FLAT, bd=0
        )
        save_btn.pack(fill=tk.X, pady=(0, 4))

        view_btn = tk.Button(
            btn_frame,
            text="View Data",
            command=self._view_data,
            bg='#3b82f6', fg='white',
            font=('Arial', 10, 'bold'),
            cursor='hand2', pady=5, relief=tk.FLAT, bd=0
        )
        view_btn.pack(fill=tk.X)

    def _save_chart(self):
        """保存图表为图片"""
        try:
            from tkinter import filedialog, messagebox
            file_path = filedialog.asksaveasfilename(
                title='Save Chart Image',
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("PDF files", "*.pdf"),
                    ("SVG files", "*.svg"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                self.canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Chart saved to:\n{file_path}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Save failed: {str(e)}")

    def _view_data(self):
        """弹出数据浏览窗口"""
        try:
            from tksheet import Sheet
            import tkinter as tk

            popup = tk.Toplevel(self.parent_root)
            popup.title(f"Data View  —  {self.x_col} vs {self.y_col}  ({len(self.chart_data)} rows)")
            popup.geometry("800x500")
            popup.configure(bg='white')

            # 顶部信息栏 + Export 按钮
            top_bar = tk.Frame(popup, bg='white')
            top_bar.pack(fill=tk.X, padx=10, pady=(8, 2))

            tk.Label(
                top_bar,
                text=f"Rows: {len(self.chart_data)}    Columns: {len(self.chart_data.columns)}",
                font=('Arial', 9), fg='#666666', bg='white'
            ).pack(side=tk.LEFT)

            def export_data():
                from tkinter import filedialog, messagebox
                file_path = filedialog.asksaveasfilename(
                    title='Export Data',
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
                )
                if file_path:
                    if file_path.endswith('.xlsx'):
                        self.chart_data.to_excel(file_path, index=False)
                    else:
                        self.chart_data.to_csv(file_path, index=False, encoding='utf-8-sig')
                    messagebox.showinfo("Success", f"Saved to:\n{file_path}")

            export_btn = tk.Button(
                top_bar,
                text="Export",
                command=export_data,
                bg='#3b82f6', fg='white',
                font=('Arial', 9, 'bold'),
                cursor='hand2', padx=12, pady=2,
                relief=tk.FLAT, bd=0
            )
            export_btn.pack(side=tk.RIGHT)

            sheet_frame = tk.Frame(popup, bg='white')
            sheet_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

            sheet = Sheet(sheet_frame, font=('Arial', 9, 'normal'),
                         header_font=('Arial', 9, 'bold'), row_height=22, column_width=120)
            sheet.enable_bindings(('single_select', 'drag_select', 'column_width_resize',
                                   'double_click_column_resize', 'arrowkeys', 'copy'))
            sheet.pack(fill=tk.BOTH, expand=True)

            display = self.chart_data.reset_index(drop=True).astype(str).replace('nan', '')
            sheet.headers(list(display.columns))
            sheet.set_sheet_data(display.values.tolist())
            sheet.set_all_column_widths(120)

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"View data failed: {str(e)}")

    def apply_range(self):
        """应用用户输入的轴范围"""
        try:
            # 获取输入值
            x_min = float(self.x_min_entry.get())
            x_max = float(self.x_max_entry.get())
            y_min = float(self.y_min_entry.get())
            y_max = float(self.y_max_entry.get())

            # 验证输入
            if x_min >= x_max:
                messagebox.showerror(
                    language_manager.get_text('input_error', '输入错误'),
                    language_manager.get_text('x_min_max_error', 'X轴最小值必须小于最大值')
                )
                return

            if y_min >= y_max:
                messagebox.showerror(
                    language_manager.get_text('input_error', '输入错误'),
                    language_manager.get_text('y_min_max_error', 'Y轴最小值必须小于最大值')
                )
                return

            # 应用到图表
            self.ax.set_xlim(x_min, x_max)
            self.ax.set_ylim(y_min, y_max)
            self.canvas.draw()

            # 更新当前范围
            self.current_xlim = [x_min, x_max]
            self.current_ylim = [y_min, y_max]

            # 显示成功消息
            messagebox.showinfo(
                language_manager.get_text('success', '成功'),
                language_manager.get_text('axis_range_applied', '轴范围已应用')
            )

        except ValueError:
            messagebox.showerror(
                language_manager.get_text('input_error', '输入错误'),
                language_manager.get_text('invalid_number', '请输入有效的数字')
            )
        except Exception as e:
            messagebox.showerror(
                language_manager.get_text('error', '错误'),
                language_manager.get_text('apply_failed', f'应用失败: {str(e)}')
            )