"""
数据状态管理器模块 - 解决筛选和异常值处理后图表数据源问题
ui/data_state_manager.py

完全模块化设计，符合语言管理器规范
追踪数据处理状态，智能选择图表数据源
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from config.languages import language_manager


class DataState:
    """数据状态枚举类"""
    ORIGINAL = "original"
    FILTERED = "filtered"
    OUTLIER_PROCESSED = "outlier_processed"
    ANALYSIS_RESULT = "analysis_result"


class DataStateManager:
    """数据状态管理器 - 解决图表数据源问题的核心模块"""

    def __init__(self, main_window):
        self.main_window = main_window

        # 数据存储
        self.original_data = None
        self.filtered_data = None
        self.outlier_processed_data = None
        self.analysis_results = None

        # 状态追踪
        self.current_state = DataState.ORIGINAL
        self.processing_history = []
        self.filter_conditions = []
        self.outlier_settings = None

        # 数据元信息
        self.data_metadata = {
            'total_rows_original': 0,
            'total_rows_current': 0,
            'processing_steps': [],
            'data_source_description': ''
        }

    def set_original_data(self, data: pd.DataFrame) -> None:
        """设置原始数据"""
        try:
            if data is None or data.empty:
                return

            self.original_data = data.copy()
            self.current_state = DataState.ORIGINAL
            self.processing_history = []

            # 重置其他数据状态
            self.filtered_data = None
            self.outlier_processed_data = None
            self.analysis_results = None

            # 更新元信息
            self._update_metadata()

            print(f"[DEBUG] {language_manager.get_text('original_data_set', '原始数据已设置')}: "
                  f"{len(data)} {language_manager.get_text('rows', '行')}, "
                  f"{len(data.columns)} {language_manager.get_text('columns', '列')}")

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('set_original_data_failed', '设置原始数据失败')}: {e}")

    def apply_filters(self, filter_conditions: List[Tuple], filtered_data: pd.DataFrame) -> bool:
        """应用筛选条件"""
        try:
            if filtered_data is None or filtered_data.empty:
                print(f"[WARNING] {language_manager.get_text('empty_filtered_data', '筛选后数据为空')}")
                return False

            self.filtered_data = filtered_data.copy()
            self.filter_conditions = filter_conditions.copy()
            self.current_state = DataState.FILTERED

            # 记录处理步骤
            step_info = {
                'type': 'filter',
                'conditions': len(filter_conditions),
                'before_rows': len(self.original_data) if self.original_data is not None else 0,
                'after_rows': len(filtered_data),
                'description': language_manager.get_text('data_filtering_applied',
                                                         f'应用了 {len(filter_conditions)} 个筛选条件')
            }
            self.processing_history.append(step_info)

            self._update_metadata()

            print(f"[INFO] {language_manager.get_text('filters_applied', '筛选条件已应用')}: "
                  f"{step_info['before_rows']} -> {step_info['after_rows']} "
                  f"{language_manager.get_text('rows', '行')}")

            return True

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('apply_filters_failed', '应用筛选失败')}: {e}")
            return False

    def apply_outlier_processing(self, outlier_settings: Dict, processed_data: pd.DataFrame) -> bool:
        """应用异常值处理"""
        try:
            if processed_data is None or processed_data.empty:
                print(f"[WARNING] {language_manager.get_text('empty_processed_data', '异常值处理后数据为空')}")
                return False

            # 确定处理前的数据
            before_data = self.filtered_data if self.filtered_data is not None else self.original_data
            if before_data is None:
                return False

            self.outlier_processed_data = processed_data.copy()
            self.outlier_settings = outlier_settings.copy()
            self.current_state = DataState.OUTLIER_PROCESSED

            # 记录处理步骤
            step_info = {
                'type': 'outlier_removal',
                'column': outlier_settings.get('column', 'unknown'),
                'method': outlier_settings.get('method', 'unknown'),
                'before_rows': len(before_data),
                'after_rows': len(processed_data),
                'description': language_manager.get_text('outlier_processing_applied',
                                                         f'对列 {outlier_settings.get("column", "unknown")} 应用了异常值处理')
            }
            self.processing_history.append(step_info)

            self._update_metadata()

            print(f"[INFO] {language_manager.get_text('outlier_processing_applied_success', '异常值处理已应用')}: "
                  f"{step_info['before_rows']} -> {step_info['after_rows']} "
                  f"{language_manager.get_text('rows', '行')}")

            return True

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('apply_outlier_processing_failed', '应用异常值处理失败')}: {e}")
            return False

    def set_analysis_results(self, results: pd.DataFrame, analysis_type: str = 'moving_window') -> bool:
        """设置分析结果"""
        try:
            if results is None or results.empty:
                print(f"[WARNING] {language_manager.get_text('empty_analysis_results', '分析结果为空')}")
                return False

            self.analysis_results = results.copy()
            self.current_state = DataState.ANALYSIS_RESULT

            # 记录处理步骤
            step_info = {
                'type': 'analysis',
                'analysis_type': analysis_type,
                'result_rows': len(results),
                'description': language_manager.get_text('analysis_completed',
                                                         f'{analysis_type} 分析完成，生成 {len(results)} 个结果')
            }
            self.processing_history.append(step_info)

            self._update_metadata()

            print(f"[INFO] {language_manager.get_text('analysis_results_set', '分析结果已设置')}: "
                  f"{len(results)} {language_manager.get_text('rows', '行')}")

            return True

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('set_analysis_results_failed', '设置分析结果失败')}: {e}")
            return False

    def get_chart_data_source(self, x_col: str, y_col: str) -> Tuple[Optional[pd.DataFrame], str, str]:
        """
        智能获取图表数据源

        Returns:
            (数据DataFrame, 数据源描述, 数据源类型)
        """
        try:
            # 优先级1: 移动窗口分析结果（特定列名）
            if (self.analysis_results is not None and
                    x_col == 'age' and y_col == 'mean'):

                valid_results = self.analysis_results.dropna(subset=['mean'])
                if len(valid_results) > 0:
                    source_desc = language_manager.get_text('moving_window_analysis_results',
                                                            f'移动窗口分析结果 ({len(valid_results)} 个有效窗口)')
                    return valid_results, source_desc, DataState.ANALYSIS_RESULT

            # 优先级2: 异常值处理后的数据
            if self.outlier_processed_data is not None:
                chart_data = self._extract_valid_data(self.outlier_processed_data, x_col, y_col)
                if chart_data is not None and len(chart_data) > 0:
                    source_desc = language_manager.get_text('outlier_processed_data',
                                                            f'异常值处理后数据 ({len(chart_data)} 个有效点)')
                    return chart_data, source_desc, DataState.OUTLIER_PROCESSED

            # 优先级3: 筛选后的数据
            if self.filtered_data is not None:
                chart_data = self._extract_valid_data(self.filtered_data, x_col, y_col)
                if chart_data is not None and len(chart_data) > 0:
                    source_desc = language_manager.get_text('filtered_data',
                                                            f'筛选后数据 ({len(chart_data)} 个有效点)')
                    return chart_data, source_desc, DataState.FILTERED

            # 优先级4: 原始数据
            if self.original_data is not None:
                chart_data = self._extract_valid_data(self.original_data, x_col, y_col)
                if chart_data is not None and len(chart_data) > 0:
                    source_desc = language_manager.get_text('original_data',
                                                            f'原始数据 ({len(chart_data)} 个有效点)')
                    return chart_data, source_desc, DataState.ORIGINAL

            # 没有可用数据
            return None, language_manager.get_text('no_data_available', '没有可用数据'), "none"

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('get_chart_data_source_failed', '获取图表数据源失败')}: {e}")
            return None, language_manager.get_text('data_source_error', '数据源错误'), "error"

    def _extract_valid_data(self, data: pd.DataFrame, x_col: str, y_col: str) -> Optional[pd.DataFrame]:
        """从数据中提取有效的图表数据"""
        try:
            if x_col not in data.columns or y_col not in data.columns:
                return None

            # 提取有效数据（非NaN）
            valid_mask = data[x_col].notna() & data[y_col].notna()
            valid_data = data.loc[valid_mask, [x_col, y_col]]

            return valid_data if len(valid_data) > 0 else None

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('extract_valid_data_failed', '提取有效数据失败')}: {e}")
            return None

    def get_current_data(self) -> Optional[pd.DataFrame]:
        """获取当前状态的数据"""
        try:
            if self.current_state == DataState.ANALYSIS_RESULT and self.analysis_results is not None:
                return self.analysis_results
            elif self.current_state == DataState.OUTLIER_PROCESSED and self.outlier_processed_data is not None:
                return self.outlier_processed_data
            elif self.current_state == DataState.FILTERED and self.filtered_data is not None:
                return self.filtered_data
            elif self.original_data is not None:
                return self.original_data
            else:
                return None

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('get_current_data_failed', '获取当前数据失败')}: {e}")
            return None

    def get_data_status_summary(self) -> Dict[str, Any]:
        """获取数据状态摘要"""
        try:
            summary = {
                'current_state': self.current_state,
                'current_state_name': self._get_state_display_name(self.current_state),
                'has_original': self.original_data is not None,
                'has_filtered': self.filtered_data is not None,
                'has_outlier_processed': self.outlier_processed_data is not None,
                'has_analysis_results': self.analysis_results is not None,
                'processing_steps': len(self.processing_history),
                'metadata': self.data_metadata.copy()
            }

            # 添加数据量信息
            current_data = self.get_current_data()
            if current_data is not None:
                summary['current_rows'] = len(current_data)
                summary['current_columns'] = len(current_data.columns)
            else:
                summary['current_rows'] = 0
                summary['current_columns'] = 0

            return summary

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('get_status_summary_failed', '获取状态摘要失败')}: {e}")
            return {}

    def _get_state_display_name(self, state: str) -> str:
        """获取状态的显示名称"""
        state_names = {
            DataState.ORIGINAL: language_manager.get_text('original_data', '原始数据'),
            DataState.FILTERED: language_manager.get_text('filtered_data', '筛选后数据'),
            DataState.OUTLIER_PROCESSED: language_manager.get_text('outlier_processed_data', '异常值处理后数据'),
            DataState.ANALYSIS_RESULT: language_manager.get_text('analysis_results', '分析结果')
        }
        return state_names.get(state, state)

    def _update_metadata(self) -> None:
        """更新数据元信息"""
        try:
            current_data = self.get_current_data()

            self.data_metadata = {
                'total_rows_original': len(self.original_data) if self.original_data is not None else 0,
                'total_rows_current': len(current_data) if current_data is not None else 0,
                'processing_steps': [step['description'] for step in self.processing_history],
                'data_source_description': self._get_state_display_name(self.current_state),
                'current_state': self.current_state,
                'filter_count': len(self.filter_conditions),
                'has_outlier_processing': self.outlier_settings is not None
            }

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('update_metadata_failed', '更新元信息失败')}: {e}")

    def clear_all_processing(self) -> None:
        """清除所有处理，回到原始数据状态"""
        try:
            self.filtered_data = None
            self.outlier_processed_data = None
            self.analysis_results = None
            self.current_state = DataState.ORIGINAL
            self.processing_history = []
            self.filter_conditions = []
            self.outlier_settings = None

            self._update_metadata()

            print(
                f"[INFO] {language_manager.get_text('all_processing_cleared', '所有数据处理已清除，回到原始数据状态')}")

        except Exception as e:
            print(f"[ERROR] {language_manager.get_text('clear_processing_failed', '清除处理失败')}: {e}")

    def has_any_processing(self) -> bool:
        """检查是否有任何数据处理"""
        return (self.filtered_data is not None or
                self.outlier_processed_data is not None or
                self.analysis_results is not None)

    def get_processing_description(self) -> str:
        """获取处理过程描述"""
        if not self.has_any_processing():
            return language_manager.get_text('no_processing_applied', '未应用任何数据处理')

        descriptions = []

        if self.filter_conditions:
            descriptions.append(language_manager.get_text('filter_applied',
                                                          f'筛选 ({len(self.filter_conditions)} 个条件)'))

        if self.outlier_settings:
            descriptions.append(language_manager.get_text('outlier_processing_applied',
                                                          f'异常值处理 ({self.outlier_settings.get("column", "unknown")} 列)'))

        if self.analysis_results is not None:
            descriptions.append(language_manager.get_text('analysis_completed', '移动窗口分析'))

        return " → ".join(descriptions)