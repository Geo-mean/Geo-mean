"""
修复的筛选窗口模块 - ui/filter_window.py
修复Unicode兼容性问题，移除emoji字符
"""

import tkinter as tk
from tkinter import ttk, messagebox
from config.styles import ModernStyle
from config.languages import language_manager


class SimpleFilterWindow:
    """改进的筛选条件设置窗口 - 添加NaN处理选项"""

    def __init__(self, parent, data_columns):
        self.parent = parent
        self.data_columns = data_columns
        self.filters = []  # 格式: [(column, condition, value, nan_policy)]
        self.result = None

        self.window = tk.Toplevel(parent)
        self.window.title("Conditional Filtering")
        self.window.geometry("900x600")  # 增加宽度容纳新选项
        self.window.transient(parent)
        self.window.grab_set()
        self.window.configure(bg='white')
        self.window.resizable(True, True)

        # 设置最小窗口大小
        self.window.minsize(900, 600)

        # 居中显示
        self.center_window()
        self.setup_ui()
        self.update_filter_count()

    def center_window(self):
        """窗口居中显示"""
        self.window.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (900 // 2)
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (600 // 2)
        self.window.geometry(f"900x600+{x}+{y}")

    def setup_ui(self):
        """设置界面"""
        # 主框架
        main_frame = tk.Frame(self.window, bg='white', padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="Conditional Filtering Setup",
            font=('Arial', 16, 'bold'),
            fg='#2c3e50',
            bg='white'
        )
        title_label.pack(pady=(0, 15))

        # 当前筛选条件列表
        self.create_filter_list_section(main_frame)

        # 添加新条件
        self.create_add_filter_section(main_frame)

        # 操作按钮
        self.create_operation_section(main_frame)

        # 底部按钮
        self.create_bottom_section(main_frame)

    def create_filter_list_section(self, parent):
        """创建筛选条件列表区域"""
        list_frame = tk.LabelFrame(parent, text="Current Filter Conditions", font=('Arial', 12, 'bold'), bg='white')
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 列表容器
        list_container = tk.Frame(list_frame, bg='white')
        list_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # 筛选条件列表
        self.filter_listbox = tk.Listbox(
            list_container,
            height=6,
            font=('Arial', 10),
            bg='white',
            selectbackground='#3498db',
            selectforeground='white'
        )

        # 滚动条
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.filter_listbox.yview)
        self.filter_listbox.configure(yscrollcommand=scrollbar.set)

        self.filter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_add_filter_section(self, parent):
        """创建添加条件区域"""
        add_frame = tk.LabelFrame(parent, text="Add New Filter Condition", font=('Arial', 12, 'bold'), bg='white')
        add_frame.pack(fill=tk.X, pady=(0, 15))

        content_frame = tk.Frame(add_frame, bg='white')
        content_frame.pack(fill=tk.X, padx=15, pady=10)

        # 第一行：基本筛选条件
        input_frame1 = tk.Frame(content_frame, bg='white')
        input_frame1.pack(fill=tk.X, pady=(0, 8))

        # 列名选择
        tk.Label(input_frame1, text="Column:", font=('Arial', 10), bg='white').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 8))

        self.column_var = tk.StringVar()
        column_combo = ttk.Combobox(
            input_frame1,
            textvariable=self.column_var,
            values=self.data_columns,
            width=18,
            state="readonly"
        )
        column_combo.grid(row=0, column=1, padx=(0, 15))

        # 条件选择
        tk.Label(input_frame1, text="Condition:", font=('Arial', 10), bg='white').grid(
            row=0, column=2, sticky=tk.W, padx=(0, 8))

        self.condition_var = tk.StringVar()
        condition_combo = ttk.Combobox(
            input_frame1,
            textvariable=self.condition_var,
            values=[">=", "<=", ">", "<", "==", "!="],
            width=8,
            state="readonly"
        )
        condition_combo.grid(row=0, column=3, padx=(0, 15))

        # 数值输入
        tk.Label(input_frame1, text="Value:", font=('Arial', 10), bg='white').grid(
            row=0, column=4, sticky=tk.W, padx=(0, 8))

        self.value_var = tk.StringVar()
        value_entry = ttk.Entry(input_frame1, textvariable=self.value_var, width=12)
        value_entry.grid(row=0, column=5)

        # 验证输入
        vcmd = (self.window.register(self.validate_number_input), '%S')
        value_entry.config(validate='key', validatecommand=vcmd)

        # 第二行：NaN处理策略
        input_frame2 = tk.Frame(content_frame, bg='white')
        input_frame2.pack(fill=tk.X, pady=(0, 8))

        # NaN处理策略标签
        tk.Label(input_frame2, text="NaN Handling:", font=('Arial', 10, 'bold'), fg='#e67e22', bg='white').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 8))

        # NaN处理策略选择
        self.nan_policy_var = tk.StringVar(value="delete_nan")
        nan_policy_combo = ttk.Combobox(
            input_frame2,
            textvariable=self.nan_policy_var,
            values=[
                "delete_nan",     # 删除NaN行
                "keep_nan"        # 保留NaN行
            ],
            width=15,
            state="readonly"
        )
        nan_policy_combo.grid(row=0, column=1, padx=(0, 20))

        # NaN策略说明
        self.nan_description_label = tk.Label(
            input_frame2,
            text="Delete NaN rows",
            font=('Arial', 9),
            fg='#7f8c8d',
            bg='white'
        )
        self.nan_description_label.grid(row=0, column=2, sticky=tk.W, padx=(0, 20))

        # NaN策略变更事件
        nan_policy_combo.bind("<<ComboboxSelected>>", self.on_nan_policy_change)

        # 添加按钮
        add_btn = tk.Button(
            input_frame2,
            text="Add Condition",
            command=self.add_filter,
            bg='#27ae60',
            fg='white',
            font=('Arial', 10, 'bold'),
            cursor='hand2',
            padx=15,
            pady=5
        )
        add_btn.grid(row=0, column=3)

        # 第三行：详细说明 - 移除emoji字符
        help_frame = tk.Frame(content_frame, bg='white')
        help_frame.pack(fill=tk.X)

        help_text = """[Tips] NaN Handling Strategy:
        - Delete NaN rows: If the column is NaN, the entire row is deleted.
        - Keep NaN rows: If the column is NaN, the entire row is kept."""

        tk.Label(
            help_frame,
            text=help_text,
            font=('Arial', 9),
            fg='#34495e',
            bg='#ecf0f1',
            justify=tk.LEFT,
            relief=tk.FLAT,
            padx=10,
            pady=8
        ).pack(fill=tk.X)

    def on_nan_policy_change(self, event=None):
        """NaN策略变更时更新说明"""
        policy = self.nan_policy_var.get()
        if policy == "delete_nan":
            self.nan_description_label.config(
                text="Delete NaN rows",
                fg='#e74c3c'
            )
        elif policy == "keep_nan":
            self.nan_description_label.config(
                text="Keep NaN rows",
                fg='#27ae60'
            )

    def create_operation_section(self, parent):
        """创建操作按钮区域"""
        op_frame = tk.Frame(parent, bg='white')
        op_frame.pack(fill=tk.X, pady=(0, 15))

        # 删除选中
        remove_btn = tk.Button(
            op_frame,
            text="Remove Selected",
            command=self.remove_filter,
            bg='#e74c3c',
            fg='white',
            font=('Arial', 10),
            cursor='hand2',
            padx=15,
            pady=5
        )
        remove_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 清空全部
        clear_btn = tk.Button(
            op_frame,
            text="Clear All",
            command=self.clear_filters,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 10),
            cursor='hand2',
            padx=15,
            pady=5
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 20))

        # 条件计数
        self.filter_count_label = tk.Label(
            op_frame,
            text="Current Conditions: 0",
            font=('Arial', 10),
            fg='#7f8c8d',
            bg='white'
        )
        self.filter_count_label.pack(side=tk.RIGHT)

    def create_bottom_section(self, parent):
        """创建底部按钮区域"""
        bottom_frame = tk.Frame(parent, bg='white')
        bottom_frame.pack(fill=tk.X)

        # 应用筛选按钮
        apply_btn = tk.Button(
            bottom_frame,
            text="Apply Filtering",
            command=self.apply_and_close_filters,
            bg='#3498db',
            fg='white',
            font=('Arial', 12, 'bold'),
            cursor='hand2',
            padx=25,
            pady=10
        )
        apply_btn.pack(side=tk.LEFT)

        # 取消按钮
        cancel_btn = tk.Button(
            bottom_frame,
            text="Cancel",
            command=self.cancel_filters,
            bg='#95a5a6',
            fg='white',
            font=('Arial', 11),
            cursor='hand2',
            padx=25,
            pady=10
        )
        cancel_btn.pack(side=tk.RIGHT)

    # ===== 保持原有方法名不变 =====

    def add_filter(self):
        """添加筛选条件"""
        column = self.column_var.get()
        condition = self.condition_var.get()
        value_str = self.value_var.get()
        nan_policy = self.nan_policy_var.get()

        # 验证输入
        if not column or not condition or not value_str or not nan_policy:
            messagebox.showwarning("Incomplete Input", "Please fill in complete filter conditions and NaN handling strategy")
            return

        try:
            # 处理小数点输入
            value_str = value_str.replace(',', '.')
            value = float(value_str)

            # 添加到筛选列表（新格式包含nan_policy）
            filter_item = (column, condition, value, nan_policy)
            self.filters.append(filter_item)

            # 显示在列表中
            nan_desc = "Delete NaN" if nan_policy == "delete_nan" else "Keep NaN"
            display_text = f"{column} {condition} {value} [{nan_desc}]"
            self.filter_listbox.insert(tk.END, display_text)

            # 更新计数
            self.update_filter_count()

            # 清空输入框
            self.column_var.set("")
            self.condition_var.set("")
            self.value_var.set("")
            self.nan_policy_var.set("delete_nan")
            self.on_nan_policy_change()  # 重置说明

            print(f"[DEBUG] 已添加增强筛选条件: {column} {condition} {value} [{nan_policy}]")

        except ValueError:
            messagebox.showerror("Input Error", f"Please enter valid numeric value\n\nInput content: '{value_str}'\nSupported formats: 1.1 or 1,1")

    def remove_filter(self):
        """删除选中的筛选条件"""
        selection = self.filter_listbox.curselection()
        if selection:
            index = selection[0]
            del self.filters[index]
            self.filter_listbox.delete(index)
            self.update_filter_count()
        else:
            messagebox.showwarning("No Selection", "Please select a filter condition to delete first")

    def clear_filters(self):
        """清空所有筛选条件"""
        if self.filters:
            result = messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all filter conditions?")
            if result:
                self.filters.clear()
                self.filter_listbox.delete(0, tk.END)
                self.update_filter_count()
        else:
            messagebox.showinfo("Info", "No current filter conditions")

    def update_filter_count(self):
        """更新筛选条件计数"""
        count = len(self.filters)
        self.filter_count_label.config(text=f"Current Conditions: {count}")

    def apply_and_close_filters(self):
        """应用筛选条件并关闭窗口"""
        if not self.filters:
            messagebox.showwarning("No Conditions", "Please add filter conditions first")
            return

        # 显示将要应用的条件
        condition_summary = "About to apply the following filter conditions:\n\n"
        for i, filter_info in enumerate(self.filters, 1):
            if len(filter_info) == 4:
                column, condition, value, nan_policy = filter_info
                nan_desc = "Delete NaN rows" if nan_policy == "delete_nan" else "Keep NaN rows"
                condition_summary += f"{i}. {column} {condition} {value} ({nan_desc})\n"
            else:
                # 兼容旧格式
                column, condition, value = filter_info
                condition_summary += f"{i}. {column} {condition} {value} (Default handling)\n"

        result = messagebox.askyesno(
            "Confirm Apply",
            condition_summary + f"\nTotal {len(self.filters)} conditions, confirm to apply?"
        )
        if result:
            self.result = self.filters.copy()
            self.window.destroy()

    def cancel_filters(self):
        """取消筛选"""
        self.result = None
        self.window.destroy()

    def validate_number_input(self, char):
        """验证数字输入"""
        if char in '0123456789.,-+':
            return True
        return False


# 兼容性函数
def GeochemicalFilterWindow(parent, data_columns):
    """兼容性包装器"""
    return SimpleFilterWindow(parent, data_columns)


def show_geochem_filter_dialog(parent, data_columns):
    """显示筛选对话框的便捷函数"""
    filter_window = SimpleFilterWindow(parent, data_columns)
    parent.wait_window(filter_window.window)
    return filter_window.result