"""
分段异常值处理对话框模块 - 简单添加年龄范围版本
ui/segmented_outlier_dialog.py

修改内容：
1. 在分段大小旁边添加起始年龄和结束年龄输入框
2. 保持原有界面布局基本不变
3. 生成分段时使用自定义年龄范围
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from config.languages import language_manager


def safe_percentile(data, percentile, interpolation='linear'):
    """
    安全的百分位数计算，兼容不同NumPy版本

    Args:
        data: 数据数组
        percentile: 百分位数 (0-100)
        interpolation: 插值方法

    Returns:
        百分位数值
    """
    try:
        # 尝试使用新版本的method参数 (NumPy >= 1.22.0)
        return np.percentile(data, percentile, method=interpolation)
    except TypeError:
        try:
            # 使用旧版本的interpolation参数 (NumPy 1.15.0 - 1.21.x)
            return np.percentile(data, percentile, interpolation=interpolation)
        except TypeError:
            # 最基础的兼容 (NumPy < 1.15.0)
            return np.percentile(data, percentile)
    except Exception as e:
        print(f"[WARNING] 百分位数计算失败，使用默认方法: {e}")
        return np.percentile(data, percentile)


class SegmentedOutlierDialog:
    """分段异常值处理对话框 - 简单添加年龄范围版本"""

    def __init__(self, parent, data, age_column, numeric_columns):
        self.parent = parent
        self.data = data.copy()
        self.age_column = age_column
        self.numeric_columns = numeric_columns
        self.result = None

        # 分段配置
        self.segments = []
        self.segment_results = {}

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Segmented Outlier Processing")
        self.dialog.geometry("900x500")  # 增加宽度以适应新输入框
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='white')

        # 居中显示
        self._center_dialog()

        # 初始化界面
        self._setup_ui()

        # 自动检测年龄范围并生成建议分段
        self._auto_generate_segments()

    def _center_dialog(self):
        """居中显示对话框"""
        try:
            self.dialog.update_idletasks()
            width = self.dialog.winfo_width()
            height = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
            self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        except:
            pass

    def _setup_ui(self):
        """设置界面"""
        main_frame = tk.Frame(self.dialog, bg='white')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # 创建功能区域
        self._create_parameter_section(main_frame)
        self._create_segments_section(main_frame)
        self._create_button_section(main_frame)

    def _create_parameter_section(self, parent):
        """创建参数设置区域"""
        param_frame = tk.LabelFrame(
            parent,
            text="Basic Parameters",
            font=('Arial', 12, 'bold'),
            bg='white'
        )
        param_frame.pack(fill=tk.X, pady=(0, 15))

        content_frame = tk.Frame(param_frame, bg='white')
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        # 第一行：年龄列和目标列
        row1 = tk.Frame(content_frame, bg='white')
        row1.pack(fill=tk.X, pady=(0, 10))

        # 年龄列选择
        tk.Label(
            row1,
            text="X-Column:",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT)

        self.age_col_var = tk.StringVar(value=self.age_column)
        age_combo = ttk.Combobox(
            row1,
            textvariable=self.age_col_var,
            values=self.numeric_columns,
            width=15,
            state="readonly"
        )
        age_combo.pack(side=tk.LEFT, padx=(10, 30))
        age_combo.bind('<<ComboboxSelected>>', self._on_age_column_changed)

        # 目标列选择
        tk.Label(
            row1,
            text="Y-Column:",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT)

        self.target_col_var = tk.StringVar()
        target_combo = ttk.Combobox(
            row1,
            textvariable=self.target_col_var,
            values=self.numeric_columns,
            width=15,
            state="readonly"
        )
        target_combo.pack(side=tk.LEFT, padx=(10, 0))

        # 第二行：分段参数 - 调整布局顺序
        row2 = tk.Frame(content_frame, bg='white')
        row2.pack(fill=tk.X, pady=(0, 10))

        # 起始年龄
        tk.Label(
            row2,
            text="Start Range:",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT)

        self.start_age_var = tk.StringVar()
        start_age_entry = tk.Entry(row2, textvariable=self.start_age_var, width=8)
        start_age_entry.pack(side=tk.LEFT, padx=(10, 20))

        # 结束年龄
        tk.Label(
            row2,
            text="End Range:",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT)

        self.end_age_var = tk.StringVar()
        end_age_entry = tk.Entry(row2, textvariable=self.end_age_var, width=8)
        end_age_entry.pack(side=tk.LEFT, padx=(10, 20))

        # 分段大小
        tk.Label(
            row2,
            text="Segment size:",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT)

        self.segment_size_var = tk.StringVar(value="100")
        segment_entry = tk.Entry(row2, textvariable=self.segment_size_var, width=8)
        segment_entry.pack(side=tk.LEFT, padx=(10, 0))

        # 第三行：异常值检测参数
        row3 = tk.Frame(content_frame, bg='white')
        row3.pack(fill=tk.X)

        # 检测方法
        tk.Label(
            row3,
            text="Detection Method:",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT)

        self.method_var = tk.StringVar(value="percentile")
        method_combo = ttk.Combobox(
            row3,
            textvariable=self.method_var,
            values=["percentile", "iqr", "std_dev"],
            width=12,
            state="readonly"
        )
        method_combo.pack(side=tk.LEFT, padx=(10, 30))

        # 百分位数范围
        tk.Label(
            row3,
            text="Percentile Range:",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT)

        self.lower_percentile_var = tk.StringVar(value="")
        lower_entry = tk.Entry(row3, textvariable=self.lower_percentile_var, width=8)
        lower_entry.pack(side=tk.LEFT, padx=(10, 5))

        tk.Label(row3, text="-", bg='white').pack(side=tk.LEFT)

        self.upper_percentile_var = tk.StringVar(value="")
        upper_entry = tk.Entry(row3, textvariable=self.upper_percentile_var, width=8)
        upper_entry.pack(side=tk.LEFT, padx=(5, 0))

        # 生成分段按钮
        generate_btn = tk.Button(
            content_frame,
            text="Generate Segments",
            command=self._generate_segments,
            bg='#007bff',
            fg='white',
            font=('Arial', 10),
            cursor='hand2'
        )
        generate_btn.pack(pady=(15, 0))

    def _create_segments_section(self, parent):
        """创建分段管理区域"""
        segments_frame = tk.LabelFrame(
            parent,
            text="Segment Management",
            font=('Arial', 12, 'bold'),
            bg='white'
        )
        segments_frame.pack(fill=tk.X, pady=(0, 8))

        # 分段列表
        list_frame = tk.Frame(segments_frame, bg='white')
        list_frame.pack(fill=tk.X, padx=15, pady=8)

        # 创建Treeview来显示分段
        columns = ('start_age', 'end_age', 'age_range', 'samples', 'outliers', 'status')
        self.segments_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=5)

        # 设置列标题
        self.segments_tree.heading('start_age', text='Start Range')
        self.segments_tree.heading('end_age', text='End Range')
        self.segments_tree.heading('age_range', text='Window Range')
        self.segments_tree.heading('samples', text='Samples')
        self.segments_tree.heading('outliers', text='Outliers')
        self.segments_tree.heading('status', text='Status')

        # 设置列宽
        self.segments_tree.column('start_age', width=100)
        self.segments_tree.column('end_age', width=100)
        self.segments_tree.column('age_range', width=100)
        self.segments_tree.column('samples', width=80)
        self.segments_tree.column('outliers', width=80)
        self.segments_tree.column('status', width=100)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.segments_tree.yview)
        self.segments_tree.configure(yscrollcommand=scrollbar.set)

        self.segments_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 分段操作按钮
        btn_frame = tk.Frame(segments_frame, bg='white')
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 8))

        tk.Button(
            btn_frame,
            text="Process Segment",
            command=self._process_selected_segment,
            bg='#28a745',
            fg='white',
            font=('Arial', 8),
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_frame,
            text="Reset Segment",
            command=self._reset_selected_segment,
            bg='#ffc107',
            fg='black',
            font=('Arial', 8),
            cursor='hand2'
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            btn_frame,
            text="Process All Segments",
            command=self._process_all_segments,
            bg='#6f42c1',
            fg='white',
            font=('Arial', 8),
            cursor='hand2'
        ).pack(side=tk.RIGHT)

    def _create_button_section(self, parent):
        """创建按钮区域"""
        spacer = tk.Frame(parent, bg='white', height=5)
        spacer.pack(fill=tk.X)

        btn_frame = tk.Frame(parent, bg='white')
        btn_frame.pack(fill=tk.X, pady=(0, 8))

        # 导出报告按钮


        # 应用按钮
        apply_btn = tk.Button(
            btn_frame,
            text="Apply Processing",
            command=self._apply_processing,
            bg='#28a745',
            fg='white',
            font=('Arial', 9, 'bold'),
            cursor='hand2',
            padx=8
        )
        apply_btn.pack(side=tk.RIGHT, padx=(2, 0))

        # 取消按钮
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=self._cancel,
            bg='#6c757d',
            fg='white',
            font=('Arial', 9),
            cursor='hand2',
            padx=8
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(2, 0))

    def _auto_generate_segments(self):
        """自动生成分段建议"""
        try:
            if self.age_column not in self.data.columns:
                return

            age_data = pd.to_numeric(self.data[self.age_column], errors='coerce').dropna()
            if len(age_data) == 0:
                return

            min_age = age_data.min()
            max_age = age_data.max()
            age_range = max_age - min_age

            # 设置默认年龄范围
            self.start_age_var.set(f"{min_age:.1f}")
            self.end_age_var.set(f"{max_age:.1f}")

            # 根据年龄范围自动建议分段大小
            if age_range > 3000:
                suggested_size = 200
            elif age_range > 1000:
                suggested_size = 100
            elif age_range > 500:
                suggested_size = 50
            else:
                suggested_size = max(25, int(age_range / 10))

            self.segment_size_var.set(str(suggested_size))

            print(f"[INFO] 自动检测完成: 年龄范围 {min_age:.1f}-{max_age:.1f} Ma, "
                  f"建议分段大小 {suggested_size} Ma")

        except Exception as e:
            print(f"[ERROR] Auto generate segments failed: {e}")

    def _on_age_column_changed(self, event=None):
        """年龄列改变事件"""
        self.age_column = self.age_col_var.get()
        self._auto_generate_segments()

    def _generate_segments(self):
        """生成年龄分段 - 使用自定义年龄范围"""
        try:
            target_column = self.target_col_var.get()
            if not target_column:
                messagebox.showwarning("Warning", "Please select target column")
                return

            # 获取自定义年龄范围
            try:
                start_age = float(self.start_age_var.get())
                end_age = float(self.end_age_var.get())
            except ValueError:
                messagebox.showerror("Error", "Please enter valid start and end ages")
                return

            if start_age >= end_age:
                messagebox.showerror("Error", "Start age must be less than end age")
                return

            segment_size = float(self.segment_size_var.get())
            if segment_size <= 0:
                messagebox.showerror("Error", "Segment size must be greater than 0")
                return

            # 获取年龄数据
            age_data = pd.to_numeric(self.data[self.age_column], errors='coerce')
            target_data = pd.to_numeric(self.data[target_column], errors='coerce')

            valid_mask = age_data.notna() & target_data.notna()

            # 在自定义范围内检查数据
            range_mask = (age_data >= start_age) & (age_data <= end_age) & valid_mask
            if range_mask.sum() == 0:
                messagebox.showerror("Error", f"No valid data in specified age range ({start_age:.1f}-{end_age:.1f} Ma)")
                return

            # 清空现有分段
            self.segments = []
            self.segment_results = {}

            # 清空树形控件
            for item in self.segments_tree.get_children():
                self.segments_tree.delete(item)

            # 在自定义范围内生成分段
            current_start = start_age
            segment_id = 0

            print(f"[INFO] 在自定义范围生成分段: {start_age:.1f} - {end_age:.1f} Ma, 分段大小: {segment_size} Ma")

            while current_start < end_age:
                segment_end = min(current_start + segment_size, end_age)

                # 获取分段内的数据
                segment_mask = (age_data >= current_start) & (age_data < segment_end) & valid_mask

                # 最后一个分段包含结束点
                if segment_end == end_age:
                    segment_mask = (age_data >= current_start) & (age_data <= segment_end) & valid_mask

                segment_samples = segment_mask.sum()

                if segment_samples > 0:
                    segment_info = {
                        'id': segment_id,
                        'start': current_start,
                        'end': segment_end,
                        'samples': segment_samples,
                        'processed': False,
                        'outliers_removed': 0
                    }

                    self.segments.append(segment_info)

                    # 显示详细的年龄范围信息
                    age_span = segment_end - current_start
                    self.segments_tree.insert('', 'end', values=(
                        f"{current_start:.1f}",      # 起始年龄
                        f"{segment_end:.1f}",        # 结束年龄
                        f"{age_span:.1f}",           # 年龄跨度
                        segment_samples,              # 样本数
                        "-",                         # 异常值数（待处理）
                        "Pending"                     # 状态
                    ))

                    segment_id += 1

                current_start = segment_end

            print(f"[INFO] 分段生成完成: {len(self.segments)} 个分段，覆盖范围 {start_age:.1f}-{end_age:.1f} Ma")

        except ValueError as e:
            messagebox.showerror("Error", "Invalid parameter format, please enter valid numeric values")
        except Exception as e:
            messagebox.showerror("Error", f"Error generating segments: {str(e)}")

    def _get_selected_segment(self):
        """获取选中的分段"""
        selection = self.segments_tree.selection()
        if not selection:
            return None

        item = selection[0]
        segment_index = self.segments_tree.index(item)

        if 0 <= segment_index < len(self.segments):
            return self.segments[segment_index]
        return None

    def _process_selected_segment(self):
        """处理选中的分段"""
        segment = self._get_selected_segment()
        if not segment:
            messagebox.showwarning("Warning", "Please select a segment first")
            return

        self._process_segment(segment)

    def _process_segment(self, segment):
        """处理单个分段"""
        try:
            target_column = self.target_col_var.get()
            if not target_column:
                return

            # 获取分段数据
            age_data = pd.to_numeric(self.data[self.age_column], errors='coerce')
            target_data = pd.to_numeric(self.data[target_column], errors='coerce')

            # 分段边界逻辑
            if segment['end'] == age_data.max():
                segment_mask = (
                        (age_data >= segment['start']) &
                        (age_data <= segment['end']) &
                        age_data.notna() &
                        target_data.notna()
                )
            else:
                segment_mask = (
                        (age_data >= segment['start']) &
                        (age_data < segment['end']) &
                        age_data.notna() &
                        target_data.notna()
                )

            segment_indices = self.data.index[segment_mask]
            segment_data = target_data[segment_mask]

            if len(segment_data) == 0:
                print(f"[WARNING] 分段 {segment['start']:.1f}-{segment['end']:.1f} Ma 没有有效数据")
                return

            # 计算异常值阈值
            method = self.method_var.get()
            lower_pct = float(self.lower_percentile_var.get())
            upper_pct = float(self.upper_percentile_var.get())

            if method == "percentile":
                lower_bound = safe_percentile(segment_data, lower_pct, 'linear')
                upper_bound = safe_percentile(segment_data, upper_pct, 'linear')
            elif method == "iqr":
                q1 = safe_percentile(segment_data, 25, 'linear')
                q3 = safe_percentile(segment_data, 75, 'linear')
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
            elif method == "std_dev":
                mean = segment_data.mean()
                std = segment_data.std()
                lower_bound = mean - 2 * std
                upper_bound = mean + 2 * std
            else:
                print(f"[ERROR] 未知的检测方法: {method}")
                return

            # 识别异常值
            outlier_mask = (segment_data < lower_bound) | (segment_data > upper_bound)
            outlier_indices = segment_indices[outlier_mask.values]

            # 直接删除异常值行
            print(f"[DEBUG] 分段 {segment['start']:.1f}-{segment['end']:.1f} Ma:")
            print(f"  删除前数据行数: {len(self.data)}")
            print(f"  检测到异常值行数: {len(outlier_indices)}")

            self.data = self.data.drop(outlier_indices).copy()

            print(f"  删除后数据行数: {len(self.data)}")

            # 更新分段状态
            segment['processed'] = True
            segment['outliers_removed'] = len(outlier_indices)

            # 保存处理结果
            self.segment_results[segment['id']] = {
                'outlier_indices': outlier_indices.tolist(),
                'outlier_count': len(outlier_indices),
                'total_samples': len(segment_data),
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'method': method
            }

            # 更新树形控件显示，保持年龄范围信息
            segment_item = self.segments_tree.get_children()[segment['id']]
            age_span = segment['end'] - segment['start']
            self.segments_tree.item(segment_item, values=(
                f"{segment['start']:.1f}",      # 起始年龄
                f"{segment['end']:.1f}",        # 结束年龄
                f"{age_span:.1f}",              # 年龄跨度
                segment['samples'],              # 样本数
                segment['outliers_removed'],     # 异常值数
                "Processed"                        # 状态
            ))

            print(f"[SUCCESS] 分段处理完成: 直接删除 {len(outlier_indices)} 行异常值数据")

        except Exception as e:
            print(f"[ERROR] 处理分段时出错: {str(e)}")

    def _process_all_segments(self):
        """处理所有分段"""
        if not self.segments:
            messagebox.showwarning("Warning", "No segments to process, please generate segments first")
            return

        target_column = self.target_col_var.get()
        if not target_column:
            messagebox.showwarning("Warning", "Please select target column")
            return

        # 确认处理
        result = messagebox.askyesno(
            "Confirm Processing",
            f"Are you sure you want to process all {len(self.segments)} segments?\n\n"
            f"Target Column: {target_column}\n"
            f"Age Range: {self.start_age_var.get()}-{self.end_age_var.get()} Ma\n"
            f"Detection Method: {self.method_var.get()}\n"
            f"This operation cannot be undone"
        )

        if not result:
            return

        # 处理所有分段
        total_outliers = 0
        processed_segments = 0

        for segment in self.segments:
            if not segment['processed']:
                self._process_segment(segment)
                total_outliers += segment['outliers_removed']
                processed_segments += 1

        # 显示处理结果
        messagebox.showinfo(
            "Success",
            f"Batch processing completed!\n\n"
            f"Segments processed: {processed_segments}\n"
            f"Total outliers removed: {total_outliers}"
        )

        print(f"[INFO] 批量处理完成: {processed_segments} 个分段，总计移除 {total_outliers} 个异常值")

    def _reset_selected_segment(self):
        """重置选中的分段"""
        segment = self._get_selected_segment()
        if not segment:
            messagebox.showwarning("Warning", "Please select a segment first")
            return

        if not segment['processed']:
            messagebox.showinfo("Info", "This segment has not been processed")
            return

        # 确认重置
        result = messagebox.askyesno(
            "Confirm Reset",
            f"Are you sure you want to reset processing results for segment {segment['start']:.1f}-{segment['end']:.1f} Ma?"
        )

        if result:
            self._reset_segment(segment)

    def _reset_segment(self, segment):
        """重置单个分段"""
        try:
            if segment['id'] in self.segment_results:
                segment['processed'] = False
                segment['outliers_removed'] = 0

                del self.segment_results[segment['id']]

                # 更新显示，保持年龄范围信息
                segment_item = self.segments_tree.get_children()[segment['id']]
                age_span = segment['end'] - segment['start']
                self.segments_tree.item(segment_item, values=(
                    f"{segment['start']:.1f}",      # 起始年龄
                    f"{segment['end']:.1f}",        # 结束年龄
                    f"{age_span:.1f}",              # 年龄跨度
                    segment['samples'],              # 样本数
                    "-",                            # 异常值数
                    "Pending"                        # 状态
                ))

                print(f"[INFO] 分段重置完成: {segment['start']:.1f}-{segment['end']:.1f} Ma")

        except Exception as e:
            messagebox.showerror("Error", f"Error resetting segment: {str(e)}")



    def _apply_processing(self):
        """应用处理结果"""
        if not self.segment_results:
            messagebox.showwarning("Warning", "No processing results to apply")
            return

        # 统计处理结果
        total_outliers = sum(result['outlier_count'] for result in self.segment_results.values())
        processed_segments = len(self.segment_results)

        # 创建结果字典
        self.result = {
            'processed_data': self.data.copy(),
            'target_column': self.target_col_var.get(),
            'segments_processed': processed_segments,
            'total_outliers_removed': total_outliers,
            'segment_details': self.segment_results.copy(),
            'processing_method': self.method_var.get(),
            'segment_size': float(self.segment_size_var.get()),
            'custom_start_age': float(self.start_age_var.get()) if self.start_age_var.get() else None,
            'custom_end_age': float(self.end_age_var.get()) if self.end_age_var.get() else None
        }

        self.dialog.destroy()

    def _cancel(self):
        """取消操作"""
        self.result = None
        self.dialog.destroy()

    def get_result(self):
        """获取处理结果"""
        return self.result


def show_segmented_outlier_dialog(parent, data, age_column, numeric_columns):
    """
    显示分段异常值处理对话框

    Args:
        parent: 父窗口
        data: 数据DataFrame
        age_column: 年龄列名
        numeric_columns: 数值列列表

    Returns:
        处理结果字典或None
    """
    try:
        dialog = SegmentedOutlierDialog(parent, data, age_column, numeric_columns)
        parent.wait_window(dialog.dialog)
        return dialog.get_result()
    except Exception as e:
        print(f"[ERROR] 显示分段异常值处理对话框失败: {e}")
        messagebox.showerror("Error", f"Dialog creation failed: {str(e)}")
        return None