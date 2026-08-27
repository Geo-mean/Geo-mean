"""
模块化数据管理器 - 负责数据相关操作 - 修复版
ui/data_manager.py
"""

from config.languages import language_manager


def safe_check_dataframe(df):
    """安全检查DataFrame是否有效"""
    try:
        return df is not None and hasattr(df, 'empty') and not df.empty
    except:
        return False


class DataManager:
    """数据管理器模块 - 负责数据处理和界面更新"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.data_processor = None

    def set_data_processor(self, data_processor):
        """设置数据处理器"""
        self.data_processor = data_processor

    def update_data_interface_after_load(self):
        """加载数据后更新界面"""
        if not self.data_processor or not safe_check_dataframe(self.data_processor.data):
            self.clear_interface()
            return

        try:
            # 获取数据信息
            data = self.data_processor.data
            columns = self.data_processor.get_columns()
            numeric_columns = self.data_processor.get_numeric_columns()

            print(f"[DEBUG] 所有列数: {len(columns)}")
            print(f"[DEBUG] 数值列数: {len(numeric_columns)}")

            # 更新主窗口的下拉框
            self.main_window.update_column_selectors(columns, numeric_columns)

            # 设置默认选择 - X/Y轴都从数值列里选
            if numeric_columns:
                self.main_window.set_x_column(numeric_columns[0])
                default_y = numeric_columns[1] if len(numeric_columns) > 1 else numeric_columns[0]
                self.main_window.set_y_column(default_y)

            # 更新图表类型
            self.main_window.set_default_chart_type()

            # 显示内存使用情况
            try:
                memory_usage = data.memory_usage(deep=True).sum() / 1024 / 1024
                return f" (Memory usage: {memory_usage:.2f}MB)"
            except:
                return ""

        except Exception as e:
            print(f"[ERROR] : {e}")
            return ""

    def clear_interface(self):
        """清空界面"""
        try:
            self.main_window.clear_column_selectors()
        except Exception as e:
            print(f"[ERROR] 清空界面失败: {e}")

    def validate_data_for_operation(self):
        """验证数据是否可用于操作"""
        if not self.data_processor:
            return False, "数据处理器未初始化"

        if not safe_check_dataframe(self.data_processor.data):
            return False, language_manager.get_text('load_file_first', '请先加载Excel文件')

        return True, "数据有效"

    def get_selected_columns_data(self, x_col, y_col):
        """获取选中列的数据 - 使用全局数据管理器版本"""
        try:
            # 核心修改：优先从全局数据管理器获取当前数据
            if hasattr(self.main_window, 'global_data_manager'):
                current_data = self.main_window.global_data_manager.get_current_data()
                if current_data is not None:
                    print(f"[DEBUG-FIX] 使用全局数据管理器数据: {len(current_data)} 行")
                    result = current_data[[x_col, y_col]].dropna()
                    print(f"[DEBUG-FIX] 提取的图表数据: {len(result)} 行")
                    return result

            # 备用方案：使用主窗口数据
            if hasattr(self.main_window, 'data') and safe_check_dataframe(self.main_window.data):
                current_data = self.main_window.data
                print(f"[DEBUG-FIX] 使用主窗口数据: {len(current_data)} 行")
            # 最后备用：使用data_processor数据
            elif safe_check_dataframe(self.data_processor.data):
                current_data = self.data_processor.data
                print(f"[DEBUG-FIX] 使用data_processor数据: {len(current_data)} 行")
            else:
                print(f"[DEBUG-FIX] 没有可用数据")
                return None

            result = current_data[[x_col, y_col]].dropna()
            print(f"[DEBUG-FIX] 提取的图表数据: {len(result)} 行")
            return result

        except Exception as e:
            print(f"[ERROR] 获取列数据失败: {e}")
            return None

    def get_data_summary(self):
        """获取数据摘要"""
        if not safe_check_dataframe(self.data_processor.data):
            return None

        try:
            data = self.data_processor.data
            return {
                'total_rows': len(data),
                'total_columns': len(data.columns),
                'numeric_columns': len(self.data_processor.get_numeric_columns()),
                'memory_usage_mb': data.memory_usage(deep=True).sum() / 1024 / 1024
            }
        except Exception as e:
            print(f"[ERROR] 获取数据摘要失败: {e}")
            return None