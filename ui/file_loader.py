"""
修复版本的文件加载器 - 移除"正在初始化检测"文字
ui/file_loader.py
"""

import threading
from tkinter import filedialog, messagebox
from config.languages import language_manager


class FileLoader:
    """文件加载器模块 - 修复版本"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.loading_cancelled = False

    def select_and_load_file(self):
        """选择并加载文件"""
        try:
            # 获取当前语言的文件对话框标题
            title = language_manager.get_text('file_selection', '选择数据文件')

            file_path = filedialog.askopenfilename(
                title=title,
                filetypes=[
                    ("Excel/CSV files", "*.xlsx *.xls *.csv"),
                    ("Excel files", "*.xlsx *.xls"),
                    ("CSV files", "*.csv"),
                    ("All files", "*.*")
                ]
            )

            if file_path:
                print(f"[DEBUG] 选择的文件: {file_path}")
                self.main_window.set_file_path(file_path)

                # 使用当前语言更新状态
                loading_msg = language_manager.get_text('loading_file', '正在加载文件...')
                self.main_window.update_status(f"[Loading] {loading_msg}")

                self.loading_cancelled = False

                # 创建进度窗口
                progress_window = self._create_progress_window()

                # 在后台线程中加载文件
                self._start_loading_thread(file_path, progress_window)
            else:
                print("[DEBUG] 用户取消了文件选择")

        except Exception as e:
            print(f"[ERROR] 文件选择过程出错: {e}")
            error_msg = language_manager.get_text('file_selection_error', f'文件选择失败: {str(e)}')
            self.main_window.update_status(f"[Error] {error_msg}")

    def _create_progress_window(self):
        """创建进度窗口 - 修复版本，完全不显示文字"""
        try:
            from ui.progress_windows import ModernProgressWindow
            # 创建时只传入标题，不显示任何状态文字
            progress_window = ModernProgressWindow(
                self.main_window.root,
                title=language_manager.get_text('loading_file_title', '正在加载文件...')
            )
            print("[DEBUG] 进度窗口创建成功")
            return progress_window
        except Exception as e:
            print(f"[WARNING] 无法创建进度窗口: {e}")
            return None

    def _start_loading_thread(self, file_path, progress_window):
        """启动加载线程 - 修复版本"""

        def load_file():
            """文件加载主函数"""
            print("[DEBUG] 开始文件加载线程")

            def progress_callback(message_text):
                """进度回调函数 - 修复闭包问题"""
                if not self.loading_cancelled and progress_window and not progress_window.cancelled:
                    # 修复：创建独立的更新函数，避免闭包问题
                    def update_ui():
                        try:
                            if progress_window and hasattr(progress_window, 'update_progress'):
                                # 确保传递的是有意义的消息，而不是默认文字
                                if message_text and message_text.strip():
                                    progress_window.update_progress(message_text)
                                else:
                                    progress_window.update_progress("正在处理数据...")
                            else:
                                print(f"[DEBUG] 进度更新: {message_text}")
                        except Exception as update_error:
                            print(f"[WARNING] 更新进度失败: {update_error}")

                    # 使用after方法安全地更新UI
                    try:
                        self.main_window.root.after(0, update_ui)
                    except Exception as after_error:
                        print(f"[WARNING] after调用失败: {after_error}")

            # 初始化结果变量
            success = False
            message = ""

            try:
                print(f"[DEBUG] 开始加载文件: {file_path}")

                # 立即更新进度窗口显示
                if progress_window:
                    try:
                        self.main_window.root.after(0, lambda: progress_window.update_progress("正在读取数据文件..."))
                    except:
                        pass

                if not self.loading_cancelled:
                    # 调用数据处理器加载文件（自动识别Excel/CSV）
                    success, message = self.main_window.data_processor.load_data(file_path, progress_callback)
                    print(f"[DEBUG] 文件加载结果: success={success}, message={message}")

            except Exception as load_exception:
                # 修复：立即处理异常，避免闭包问题
                print(f"[ERROR] 文件加载异常: {load_exception}")
                success = False
                message = f"加载异常: {str(load_exception)}"

                # 显示错误到进度窗口
                try:
                    if progress_callback:
                        error_msg = language_manager.get_text('load_error', f'加载失败: {str(load_exception)}')
                        progress_callback(error_msg)
                except Exception as callback_error:
                    print(f"[WARNING] 错误回调失败: {callback_error}")

            finally:
                # 确保在任何情况下都调用完成回调
                print("[DEBUG] 准备调用完成回调")
                if not self.loading_cancelled:
                    def handle_completion():
                        try:
                            print(f"[DEBUG] 执行完成回调: success={success}")
                            self._on_file_loaded(success, message, progress_window)
                        except Exception as completion_error:
                            print(f"[ERROR] 处理加载完成回调失败: {completion_error}")
                            # 即使回调失败也要更新状态
                            fallback_msg = language_manager.get_text('load_error', f'处理加载结果时出错: {str(completion_error)}')
                            self.main_window.update_status(f"[Error] {fallback_msg}")

                    try:
                        self.main_window.root.after(0, handle_completion)
                    except Exception as after_error:
                        print(f"[ERROR] 无法调度完成回调: {after_error}")
                        # 最后的后备方案：直接调用
                        try:
                            self._on_file_loaded(success, message, progress_window)
                        except Exception as direct_error:
                            print(f"[ERROR] 直接调用完成回调也失败: {direct_error}")

        # 启动后台线程
        try:
            thread = threading.Thread(target=load_file, daemon=True)
            thread.start()
            print("[DEBUG] 文件加载线程已启动")
        except Exception as thread_error:
            print(f"[ERROR] 启动加载线程失败: {thread_error}")
            error_msg = language_manager.get_text('load_error', f'无法启动文件加载: {str(thread_error)}')
            self.main_window.update_status(f"[Error] {error_msg}")

    def _on_file_loaded(self, success, message, progress_window):
        """文件加载完成回调"""
        try:
            print(f"[DEBUG] 文件加载完成回调: success={success}")

            # 关闭进度窗口
            if progress_window:
                try:
                    progress_window.close()
                    print("[DEBUG] 进度窗口已关闭")
                except Exception as close_error:
                    print(f"[WARNING] 关闭进度窗口失败: {close_error}")

            # 检查是否被取消
            if progress_window and hasattr(progress_window, 'cancelled') and progress_window.cancelled:
                cancel_msg = language_manager.get_text('load_cancelled', '文件加载已取消')
                self.main_window.update_status(f"[Cancelled] {cancel_msg}")
                print("[DEBUG] 文件加载被用户取消")
                return

            # 处理加载结果
            if success:
                print("[DEBUG] 通知主窗口加载成功")
                # 通知主窗口加载成功
                self.main_window.on_file_load_success(message)
            else:
                print(f"[DEBUG] 通知主窗口加载失败: {message}")
                # 通知主窗口加载失败
                self.main_window.on_file_load_error(message)

        except Exception as callback_error:
            print(f"[ERROR] 文件加载完成处理异常: {callback_error}")
            # 确保即使出错也有反馈
            try:
                error_msg = language_manager.get_text('load_error', f'处理加载结果时出错: {str(callback_error)}')
                self.main_window.update_status(f"[Error] {error_msg}")
            except Exception as status_error:
                print(f"[ERROR] 连状态更新都失败了: {status_error}")

    def cancel_loading(self):
        """取消加载"""
        print("[DEBUG] 用户请求取消加载")
        self.loading_cancelled = True