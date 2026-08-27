"""
全局数据管理器 - 确保所有模块使用一致的数据状态
core/global_data_manager.py
"""
import pandas as pd
import numpy as np
from datetime import datetime
from config.languages import language_manager


class GlobalDataManager:
    """全局数据管理器 - 统一管理数据状态，确保所有模块读取一致的数据"""

    def __init__(self):
        self.original_data = None  # 原始加载的数据，永不改变
        self.current_data = None  # 当前处理后的数据，各模块都应该使用这个
        self.processing_history = []  # 处理历史记录
        self.data_metadata = {}  # 数据元信息
        self._listeners = []  # 数据变化监听器

    def set_original_data(self, data, file_path="", source_info=""):
        """设置原始数据 - 只在文件加载时调用"""
        try:
            if data is None:
                print("[WARNING] 尝试设置空数据为原始数据")
                return False

            self.original_data = data.copy()
            self.current_data = data.copy()  # 当前数据初始化为原始数据

            # 重置处理历史
            self.processing_history = [{
                'timestamp': datetime.now(),
                'operation': f"加载原始数据: {source_info}",
                'data_shape': data.shape,
                'file_path': file_path
            }]

            # 更新元信息
            self.data_metadata = {
                'original_rows': len(data),
                'original_columns': len(data.columns),
                'current_rows': len(data),
                'current_columns': len(data.columns),
                'file_path': file_path,
                'source_info': source_info,
                'last_modified': datetime.now()
            }

            print(f"[DEBUG-GLOBAL] 原始数据已设置: {len(data)} 行 x {len(data.columns)} 列")

            # 通知所有监听器
            self._notify_listeners('data_loaded', self.current_data)

            return True

        except Exception as e:
            print(f"[ERROR] 设置原始数据失败: {e}")
            return False

    def update_current_data(self, new_data, operation_name, metadata=None):
        """更新当前处理后的数据 - 所有数据处理操作都应该调用这个方法"""
        try:
            if new_data is None:
                print(f"[WARNING] 尝试更新为空数据: {operation_name}")
                return False

            # 验证数据有效性
            if not isinstance(new_data, pd.DataFrame):
                print(f"[ERROR] 数据不是DataFrame类型: {type(new_data)}")
                return False

            # 更新当前数据
            old_data = self.current_data.copy() if self.current_data is not None else None
            self.current_data = new_data.copy()

            # 记录处理历史
            history_entry = {
                'timestamp': datetime.now(),
                'operation': operation_name,
                'data_shape': new_data.shape,
                'rows_changed': len(new_data) - (len(old_data) if old_data is not None else 0)
            }

            if metadata:
                history_entry.update(metadata)

            self.processing_history.append(history_entry)

            # 更新元信息
            self.data_metadata.update({
                'current_rows': len(new_data),
                'current_columns': len(new_data.columns),
                'last_modified': datetime.now(),
                'last_operation': operation_name
            })

            if metadata:
                self.data_metadata.update(metadata)

            print(f"[DEBUG-GLOBAL] 数据已更新: {operation_name} -> {len(new_data)} 行")

            # 通知所有监听器数据已更改
            self._notify_listeners('data_updated', self.current_data)

            return True

        except Exception as e:
            print(f"[ERROR] 更新当前数据失败 ({operation_name}): {e}")
            return False

    def get_current_data(self, copy=True):
        """获取当前数据 - 所有模块都应该通过这个方法获取数据"""
        if self.current_data is None:
            print("[WARNING] 当前数据为空，请先加载数据")
            return None

        if copy:
            return self.current_data.copy()
        else:
            return self.current_data

    def get_original_data(self, copy=True):
        """获取原始数据（未处理的）"""
        if self.original_data is None:
            return None

        if copy:
            return self.original_data.copy()
        else:
            return self.original_data

    def reset_to_original(self):
        """重置到原始数据状态"""
        try:
            if self.original_data is None:
                print("[WARNING] 没有原始数据可以重置")
                return False

            self.current_data = self.original_data.copy()

            # 添加重置记录
            self.processing_history.append({
                'timestamp': datetime.now(),
                'operation': '重置到原始数据',
                'data_shape': self.original_data.shape,
                'rows_changed': 0
            })

            # 更新元信息
            self.data_metadata.update({
                'current_rows': len(self.original_data),
                'current_columns': len(self.original_data.columns),
                'last_modified': datetime.now(),
                'last_operation': '重置到原始数据'
            })

            print(f"[DEBUG-GLOBAL] 已重置到原始数据: {len(self.original_data)} 行")

            # 通知监听器
            self._notify_listeners('data_reset', self.current_data)

            return True

        except Exception as e:
            print(f"[ERROR] 重置到原始数据失败: {e}")
            return False

    def get_processing_status(self):
        """获取处理状态信息"""
        return {
            'has_data': self.current_data is not None,
            'has_original': self.original_data is not None,
            'history_count': len(self.processing_history),
            'history': self.processing_history.copy(),
            'metadata': self.data_metadata.copy(),
            'current_shape': self.current_data.shape if self.current_data is not None else None,
            'original_shape': self.original_data.shape if self.original_data is not None else None
        }

    def get_processing_summary(self):
        """获取处理摘要信息（用于显示）"""
        if not self.current_data is not None:
            return "没有数据"

        summary = []

        if self.original_data is not None:
            original_rows = len(self.original_data)
            current_rows = len(self.current_data)

            if current_rows != original_rows:
                change = current_rows - original_rows
                summary.append(f"数据行数: {original_rows} -> {current_rows} ({change:+d})")
            else:
                summary.append(f"数据行数: {current_rows}")
        else:
            summary.append(f"now data: {len(self.current_data)} row")

        # 添加最近的处理操作
        if len(self.processing_history) > 1:  # 除了加载操作
            recent_ops = [h['operation'] for h in self.processing_history[-3:] if not h['operation'].startswith('加载')]
            if recent_ops:
                summary.append(f"最近操作: {' -> '.join(recent_ops)}")

        return " | ".join(summary)

    def add_data_listener(self, callback):
        """添加数据变化监听器"""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_data_listener(self, callback):
        """移除数据变化监听器"""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, event_type, data):
        """通知所有监听器数据已变化"""
        for listener in self._listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                print(f"[WARNING] 数据监听器出错: {e}")

    def validate_current_data(self):
        """验证当前数据的有效性"""
        if self.current_data is None:
            return False, "当前数据为空"

        if self.current_data.empty:
            return False, "当前数据为空DataFrame"

        return True, "数据有效"

    def get_numeric_columns(self):
        """获取当前数据的数值列"""
        if self.current_data is None:
            return []
        return list(self.current_data.select_dtypes(include=[np.number]).columns)

    def get_all_columns(self):
        """获取当前数据的所有列"""
        if self.current_data is None:
            return []
        return list(self.current_data.columns)

    def get_data_info(self):
        """获取当前数据的基本信息"""
        if self.current_data is None:
            return None

        try:
            return {
                'rows': len(self.current_data),
                'columns': len(self.current_data.columns),
                'numeric_columns': len(self.get_numeric_columns()),
                'memory_usage_mb': self.current_data.memory_usage(deep=True).sum() / 1024 / 1024,
                'has_nan': self.current_data.isnull().any().any(),
                'processing_steps': len(self.processing_history)
            }
        except Exception as e:
            print(f"[ERROR] 获取数据信息失败: {e}")
            return None


# 创建全局单例实例
global_data_manager = GlobalDataManager()


def get_global_data_manager():
    """获取全局数据管理器实例"""
    return global_data_manager