"""
语言选择对话框 - 简化版
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from config.languages import language_manager


class LanguageSelectionDialog:
    def __init__(self, parent=None):
        self.result = False
        self.selected_language = None

        # 创建主窗口
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title("Language Selection / 语言选择")
        self.root.geometry("500x400")  # 增加高度确保按钮可见
        self.root.resizable(False, False)

        # 设置窗口居中
        self.center_window()

        # 设置窗口属性
        if parent:
            self.root.transient(parent)
            self.root.grab_set()

        # 创建界面
        self.create_widgets()

        # 设置默认选择
        self.language_var.set("zh_CN")  # 默认选择中文

    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = 500
        height = 400  # 增加高度
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="LANG",
            font=("Arial", 24, "bold"),
            fg="#4A90E2"
        )
        title_label.pack(pady=(0, 10))

        # 副标题
        subtitle_label = tk.Label(
            main_frame,
            text="Language Selection / 语言选择",
            font=("Arial", 16, "bold"),
            fg="#4A90E2"
        )
        subtitle_label.pack(pady=(0, 20))

        # 说明文字
        instruction_label = tk.Label(
            main_frame,
            text="Please select your preferred language:\n请选择您的首选语言：",
            font=("Arial", 12),
            fg="#666666"
        )
        instruction_label.pack(pady=(0, 20))

        # 语言选择框架
        language_frame = ttk.Frame(main_frame)
        language_frame.pack(pady=10)

        # 语言选择变量
        self.language_var = tk.StringVar(value="zh_CN")

        # 获取可用语言并创建选项
        try:
            available_languages = language_manager.get_available_languages()
            print(f"[DEBUG] 语言选择对话框 - 可用语言: {available_languages}")

            # 手动创建语言选项（移除旗帜图标以兼容tkinter）
            language_options = [
                ("zh_CN", "中文 (Chinese)"),
                ("en_US", "English")
            ]

            # 创建单选按钮
            for lang_code, display_text in language_options:
                if lang_code in available_languages:  # 只创建可用语言的选项
                    rb = ttk.Radiobutton(
                        language_frame,
                        text=display_text,
                        variable=self.language_var,
                        value=lang_code
                    )
                    rb.pack(anchor=tk.W, pady=8, padx=20)

        except Exception as e:
            print(f"[ERROR] 创建语言选择按钮失败: {e}")
            # 如果出错，创建默认选项
            ttk.Radiobutton(
                language_frame,
                text="中文 (Chinese)",
                variable=self.language_var,
                value="zh_CN"
            ).pack(anchor=tk.W, pady=8, padx=20)

            ttk.Radiobutton(
                language_frame,
                text="English",
                variable=self.language_var,
                value="en_US"
            ).pack(anchor=tk.W, pady=8, padx=20)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20, fill=tk.X)  # 减少pady确保可见

        # 取消按钮（左侧）
        cancel_button = tk.Button(
            button_frame,
            text="Cancel / 取消",
            command=self.cancel_selection,
            bg="#CCCCCC",
            fg="#333333",
            font=("Arial", 12),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        cancel_button.pack(side=tk.LEFT)

        # 确认按钮（右侧）
        confirm_button = tk.Button(
            button_frame,
            text="Confirm / 确认",
            command=self.confirm_selection,
            bg="#4A90E2",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        confirm_button.pack(side=tk.RIGHT)

        # 绑定快捷键
        self.root.bind('<Return>', lambda event: self.confirm_selection())
        self.root.bind('<Escape>', lambda event: self.cancel_selection())

        # 确保窗口获得焦点
        self.root.focus_force()

    def confirm_selection(self):
        """确认选择"""
        self.selected_language = self.language_var.get()

        try:
            # 设置语言
            success = language_manager.set_language(self.selected_language)
            print(f"[DEBUG] 设置语言结果: {success}, 选择的语言: {self.selected_language}")

            self.result = True

        except Exception as e:
            print(f"[ERROR] 设置语言时出错: {e}")
            self.result = True  # 即使出错也继续

        self.root.destroy()

    def cancel_selection(self):
        """取消选择"""
        self.result = False
        self.selected_language = None
        self.root.destroy()

    def show(self):
        """显示对话框并返回结果"""
        self.root.focus_set()
        self.root.wait_window()
        return self.result, self.selected_language


def show_language_selection(parent=None):
    """显示语言选择对话框的便捷函数"""
    try:
        dialog = LanguageSelectionDialog(parent)
        return dialog.show()
    except Exception as e:
        print(f"[ERROR] 显示语言选择对话框失败: {e}")
        # 如果对话框失败，返回默认值
        return True, "zh_CN"


# 测试代码
if __name__ == "__main__":
    # 创建测试窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 显示语言选择对话框
    result, selected_language = show_language_selection()

    if result:
        print(f"选择的语言: {selected_language}")
        print(f"当前语言名称: {language_manager.get_current_language_name()}")
    else:
        print("用户取消了选择")

    root.destroy()