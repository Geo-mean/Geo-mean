"""
地球化学移动窗口分析集成模块 - 清理版
geochemistry/moving_window_integration.py

专注于移动窗口分析，移除重复的筛选和异常值处理功能
修复列名问题：动态使用用户选择的X轴和Y轴列名
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Optional, Callable
from config.languages import language_manager
from .geochem_filter_manager import GeochemicalFilterManager


class MovingWindowIntegration:
    """移动窗口分析集成类 - 清理版"""

    def __init__(self, data_processor):
        """
        初始化移动窗口分析集成

        Args:
            data_processor: DataProcessor实例
        """
        self.data_processor = data_processor
        self.original_data = data_processor.data.copy() if data_processor.data is not None else None
        self.current_data = None  # 存储当前要分析的数据（已经过筛选处理）
        self.analysis_results = None

        # 初始化地球化学筛选管理器（仅用于列检测）
        if self.original_data is not None:
            self.filter_manager = GeochemicalFilterManager(self.original_data)
        else:
            self.filter_manager = None

    def get_available_columns(self) -> Dict[str, List[str]]:
        """
        获取可用列信息

        Returns:
            包含所有列和数值列的字典
        """
        if self.original_data is None:
            return {'all': [], 'numeric': []}

        all_columns = list(self.original_data.columns)
        numeric_columns = list(self.original_data.select_dtypes(include=[np.number]).columns)

        return {
            'all': all_columns,
            'numeric': numeric_columns
        }

    def get_recommended_analysis_parameters(self) -> Optional[Dict]:
        """
        获取推荐的分析参数

        Returns:
            推荐参数字典或None
        """
        if self.original_data is None or self.filter_manager is None:
            return None

        try:
            # 获取检测到的列映射
            detected_columns = self.filter_manager.get_detected_columns()

            # 寻找合适的年龄列和目标列
            age_column = None
            target_column = None

            # 优先选择年龄列
            if 'AGE' in detected_columns:
                age_column = detected_columns['AGE']

            # 优先选择ThU作为目标列
            if 'ThU' in detected_columns:
                target_column = detected_columns['ThU']
            elif 'SiO2' in detected_columns:
                target_column = detected_columns['SiO2']

            if not age_column or not target_column:
                return None

            # 分析年龄数据特征
            age_data = pd.to_numeric(self.original_data[age_column], errors='coerce')
            valid_ages = age_data.dropna()

            if len(valid_ages) < 10:
                return None

            min_age = valid_ages.min()
            max_age = valid_ages.max()
            age_range = max_age - min_age

            # 根据年龄范围推荐参数
            if age_range > 3000:  # 全地质历史
                recommended_params = {
                    'age_column': age_column,
                    'target_column': target_column,
                    'min_age': max(100, int(min_age)),
                    'max_age': min(4000, int(max_age)),
                    'window_size': 200,
                    'step_size': 50,
                    'description': language_manager.get_text('full_geological_history', '全地质历史分析')
                }
            elif max_age > 2500:  # 古老岩石
                recommended_params = {
                    'age_column': age_column,
                    'target_column': target_column,
                    'min_age': max(2500, int(min_age)),
                    'max_age': min(3500, int(max_age)),
                    'window_size': 100,
                    'step_size': 25,
                    'description': language_manager.get_text('archean_analysis', '古老岩石分析')
                }
            elif max_age < 1000:  # 显生宙
                recommended_params = {
                    'age_column': age_column,
                    'target_column': target_column,
                    'min_age': max(50, int(min_age)),
                    'max_age': min(600, int(max_age)),
                    'window_size': 50,
                    'step_size': 25,
                    'description': language_manager.get_text('phanerozoic_analysis', '显生宙分析')
                }
            else:  # 自定义范围
                recommended_params = {
                    'age_column': age_column,
                    'target_column': target_column,
                    'min_age': int(min_age),
                    'max_age': int(max_age),
                    'window_size': max(50, int(age_range / 10)),
                    'step_size': max(25, int(age_range / 20)),
                    'description': language_manager.get_text('custom_range_analysis', '自定义范围分析')
                }

            # 计算预计窗口数
            estimated_windows = int((recommended_params['max_age'] - recommended_params['min_age']) / recommended_params['step_size']) + 1
            recommended_params['estimated_windows'] = estimated_windows

            return recommended_params

        except Exception as e:
            print(f"[ERROR] Error generating recommended parameters: {str(e)}")
            return None

    def set_current_data(self, data: pd.DataFrame):
        """
        设置当前要分析的数据（通常是主窗口筛选后的数据）

        Args:
            data: 当前数据DataFrame
        """
        print(f"[DEBUG] Sliding Window Settings: {len(data)} 行")
        self.current_data = data.copy()

    def run_complete_analysis(self,
                              params: Dict,
                              progress_callback: Optional[Callable] = None) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        运行完整的移动窗口分析 - 添加最小样本数支持
        """
        try:
            min_samples = params.get('min_samples', 5)  # 新增：获取最小样本数参数

            if progress_callback:
                progress_callback(f"Starting sliding window analysis... (min_samples: {min_samples})")

            # 使用当前设置的数据，如果没有则使用原始数据
            if self.current_data is None:
                print("[DEBUG] No external data available, using raw data.")
                analysis_data = self.original_data.copy()
            else:
                print(f"[DEBUG] Use External Data: {len(self.current_data)} ")
                analysis_data = self.current_data.copy()

            # 直接运行移动窗口分析
            if progress_callback:
                progress_callback('Running sliding window analysis...')

            self.analysis_results = self._run_moving_window_analysis(
                analysis_data,
                params['age_column'],
                params['target_column'],
                params['window_size'],
                params['step_size'],
                params['min_age'],
                params['max_age'],
                min_samples,  # 传递最小样本数参数
                progress_callback
            )

            if self.analysis_results is not None and len(self.analysis_results) > 0:
                valid_windows = len(self.analysis_results.dropna(subset=[f'{params["target_column"]}_mean']))
                total_windows = len(self.analysis_results)

                success_msg = f'Analysis complete: Total windows: {total_windows}, Valid windows: {valid_windows}, min_samples: {min_samples}'
                return True, success_msg, self.analysis_results
            else:
                return False, 'The analysis produced no valid results.', None

        except Exception as e:
            error_msg = f"Sliding window analysis failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return False, error_msg, None



    def _run_moving_window_analysis(self,
                                    data: pd.DataFrame,
                                    age_column: str,
                                    target_column: str,
                                    window_size: int,
                                    step_size: int,
                                    min_age: int,
                                    max_age: int,
                                    min_samples: int = 5,  # 新增：最小样本数参数
                                    progress_callback: Optional[Callable] = None) -> Optional[pd.DataFrame]:
        """
        运行移动窗口分析的核心逻辑 - 添加最小样本数支持
        """
        try:
            # 数据验证
            if age_column not in data.columns:
                raise ValueError(f'Age column "{age_column}"is missing')

            if target_column not in data.columns:
                raise ValueError(f'Target column "{target_column}"is missing')

            # 数据类型转换
            age_data = pd.to_numeric(data[age_column], errors='coerce')
            target_data = pd.to_numeric(data[target_column], errors='coerce')

            # 检查有效数据
            valid_mask = age_data.notna() & target_data.notna()
            valid_count = valid_mask.sum()

            if valid_count < 10:
                raise ValueError(f'Valid data is too few（{valid_count} < 10）')

            print(f"[INFO] Sliding window analysis started:")
            print(f"[INFO] Number of valid data pairs: {valid_count}")
            print(f"[INFO] Age range: {age_data[valid_mask].min():.1f} - {age_data[valid_mask].max():.1f} Ma")
            print(f"[INFO] Target value range: {target_data[valid_mask].min():.6f} - {target_data[valid_mask].max():.6f}")
            print(f"[INFO] Window parameters: size={window_size}Ma, step={step_size}Ma, range={min_age}-{max_age}Ma")
            print(f"[INFO] Minimum sample size required: {min_samples}")  # 新增日志

            # 计算窗口参数
            results = []
            start_center = min_age + window_size // 2
            end_center = max_age - window_size // 2
            current_center = start_center

            valid_windows = 0
            total_windows = 0
            skipped_low_samples = 0  # 新增：记录因样本数不足跳过的窗口

            # 移动窗口主循环
            while current_center <= end_center:
                total_windows += 1

                try:
                    # 定义窗口范围
                    window_low = current_center - window_size // 2
                    window_high = current_center + window_size // 2

                    # 获取窗口内的数据
                    window_mask = (age_data >= window_low) & (age_data <= window_high) & valid_mask
                    window_data = target_data[window_mask].dropna()

                    # 修改：使用传入的最小样本数参数
                    if len(window_data) >= min_samples:
                        valid_windows += 1

                        # Bootstrap统计分析
                        bootstrap_means = []
                        window_array = window_data.values

                        # 进行10000次Bootstrap采样
                        np.random.seed(42)  # 确保结果可重现
                        for _ in range(10000):
                            sample = np.random.choice(window_array, size=len(window_array), replace=True)
                            bootstrap_means.append(np.mean(sample))

                        # 计算统计量
                        mean_val = np.mean(bootstrap_means)
                        std_error = 2 * np.std(bootstrap_means)  # 2σ误差
                        sample_count = len(window_data)

                        # 创建组合值字符串
                        combo_value = f"{current_center}-{mean_val:.6f}"

                        # 更新进度回调
                        if progress_callback:
                            progress_callback(f'Processing window {current_center}Ma: {sample_count} samples')

                    else:
                        # 样本数不足
                        mean_val = np.nan
                        std_error = np.nan
                        sample_count = len(window_data)
                        skipped_low_samples += 1  # 记录跳过的窗口

                        # 对于无效数据也创建组合值
                        combo_value = f"{current_center}-NaN"

                        print(f"[SKIP] Window {current_center}Ma has insufficient samples: {sample_count} < {min_samples}")

                    # 保存结果 - 使用动态列名
                    results.append({
                        age_column: current_center,  # 使用实际的X轴列名
                        f'{target_column}_mean': mean_val,  # 使用Y轴列名_mean
                        f'{age_column}-{target_column}_mean': combo_value,  # 新的组合列
                        'std_error': std_error,
                        'sample_count': sample_count,
                        'window_low': window_low,
                        'window_high': window_high
                    })

                except Exception as e:
                    print(f"[ERROR] Error processing window {current_center} {str(e)}")

                # 移动到下一个窗口
                current_center += step_size

            # 分析完成
            if not results:
                print("[WARNING] No results were generated from the sliding window analysis")
                return None

            # 创建结果DataFrame
            results_df = pd.DataFrame(results)

            print(f"[SUCCESS] Sliding window analysis completed:")
            print(f"[SUCCESS] Total windows: {total_windows}, Valid windows: {valid_windows}")
            print(f"[SUCCESS] Skipped due to insufficient samples: {skipped_low_samples} windows")  # 新增日志
            print(f"[SUCCESS] Success rate: {valid_windows / total_windows * 100:.1f}%")
            print(f"[SUCCESS] Minimum sample size threshold: {min_samples}")  # 新增日志

            return results_df

        except Exception as e:
            print(f"[ERROR] An error occurred during sliding window analysis: {str(e)}")
            return None

    def export_analysis_results(self,
                                export_dir: str,
                                include_chart: bool = True,
                                include_data: bool = True,
                                include_report: bool = True) -> Tuple[bool, str]:
        """
        导出分析结果

        Args:
            export_dir: 导出目录
            include_chart: 是否包含图表
            include_data: 是否包含数据
            include_report: 是否包含报告

        Returns:
            (是否成功, 消息)
        """
        try:
            if self.analysis_results is None:
                return False, language_manager.get_text('no_results_to_export', 'no_results_to_export')

            if not os.path.exists(export_dir):
                os.makedirs(export_dir)

            exported_files = []

            # 导出数据
            if include_data:
                data_file = os.path.join(export_dir, 'moving_window_results.xlsx')
                # 重命名std_error列为2SE
                export_data = self.analysis_results.copy()
                export_data.rename(columns={'std_error': '2SE'}, inplace=True)
                export_data.to_excel(data_file, index=False)
                exported_files.append(data_file)

            # 导出筛选报告
            if include_report and self.filter_manager:
                report_file = os.path.join(export_dir, 'analysis_report.xlsx')
                # 创建简单报告（不包含筛选详情）
                with pd.ExcelWriter(report_file) as writer:
                    export_data = self.analysis_results.copy()
                    export_data.rename(columns={'std_error': '2SE'}, inplace=True)
                    export_data.to_excel(writer, sheet_name='Results', index=False)
                exported_files.append(report_file)

            # 导出图表（如果需要）
            if include_chart:
                try:
                    import matplotlib.pyplot as plt

                    # 创建图表
                    fig, ax = plt.subplots(figsize=(12, 8))

                    # 获取列名 - 动态获取mean列名，更新特殊列列表
                    mean_column = None
                    x_column = None
                    special_columns = ['std_error', '2SE', 'sample_count', 'window_low', 'window_high',
                                       'window_start', 'window_end', 'boundary_mode']

                    for col in self.analysis_results.columns:
                        if col.endswith('_mean') and not '-' in col:
                            mean_column = col
                        elif (col not in special_columns and
                              not col.endswith('_mean') and
                              '-' not in col):
                            x_column = col

                    # 绘制有效结果
                    if mean_column and x_column:
                        valid_results = self.analysis_results.dropna(subset=[mean_column])

                        if len(valid_results) > 0:
                            # 检查误差列名（可能是std_error或2SE）
                            error_col = 'std_error' if 'std_error' in valid_results.columns else '2SE'

                            ax.errorbar(valid_results[x_column], valid_results[mean_column],
                                        yerr=valid_results[error_col] if error_col in valid_results.columns else None,
                                        marker='o', linewidth=2.5, markersize=7,
                                        capsize=6, capthick=2,
                                        color='#2E86AB', markerfacecolor='#A23B72',
                                        markeredgecolor='white', markeredgewidth=1.5,
                                        ecolor='#FF6B6B', alpha=0.8)

                            ax.set_xlabel(f'{x_column}', fontweight='bold', fontsize=12)
                            ax.set_ylabel(f'{mean_column}', fontweight='bold', fontsize=12)
                            ax.set_title('Moving Window Analysis Results', fontweight='bold', fontsize=14)
                            ax.grid(True, alpha=0.3)

                            chart_file = os.path.join(export_dir, 'moving_window_chart.png')
                            fig.savefig(chart_file, dpi=300, bbox_inches='tight')
                            exported_files.append(chart_file)

                    plt.close(fig)

                except Exception as e:
                    print(f"[WARNING] ERROR: {str(e)}")

            success_msg = language_manager.get_text('export_complete',
                                                    f'export_complete: {export_dir}')

            return True, success_msg

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return False, error_msg


def run_quick_moving_window_analysis(main_window_data, age_column, target_column,
                                     window_size, step_size, min_age, max_age,
                                     min_samples=5,
                                     progress_callback=None):
    """快速移动窗口分析函数 - 修复版：直接计算均值标准差，不用Bootstrap，动态列名"""
    try:
        print(f"[DEBUG] QUICK RUNNING，min_samples: {min_samples}")

        # 数据验证
        if main_window_data is None or len(main_window_data) == 0:
            raise ValueError("no data")

        # 验证列存在
        if age_column not in main_window_data.columns:
            raise ValueError(f"age_column '{age_column}' error")
        if target_column not in main_window_data.columns:
            raise ValueError(f"target_column '{target_column}' error")

        # 数据类型转换
        age_data = pd.to_numeric(main_window_data[age_column], errors='coerce')
        target_data = pd.to_numeric(main_window_data[target_column], errors='coerce')

        # 检查有效数据
        valid_mask = age_data.notna() & target_data.notna()
        valid_count = valid_mask.sum()

        if valid_count < 10:
            raise ValueError(f'valid_count < 10（{valid_count} < 10）')

        # 计算窗口参数
        results = []
        start_center = min_age + window_size // 2
        end_center = max_age - window_size // 2
        current_center = start_center

        valid_windows = 0
        total_windows = 0
        skipped_low_samples = 0

        # 移动窗口主循环 - 快速版本
        while current_center <= end_center:
            total_windows += 1

            try:
                # 定义窗口范围
                window_low = current_center - window_size // 2
                window_high = current_center + window_size // 2

                # 获取窗口内的数据
                window_mask = (age_data >= window_low) & (age_data <= window_high) & valid_mask
                window_data = target_data[window_mask].dropna()

                # 检查最小样本数
                if len(window_data) >= min_samples:
                    valid_windows += 1

                    # 快速统计：直接计算均值和标准差（不用Bootstrap）
                    mean_val = np.mean(window_data)
                    std_val = np.std(window_data, ddof=1) if len(window_data) > 1 else 0
                    std_error = std_val / np.sqrt(len(window_data)) if len(window_data) > 0 else 0
                    sample_count = len(window_data)

                    # 创建组合值字符串
                    combo_value = f"{current_center}-{mean_val:.6f}"

                    # 更新进度回调
                    if progress_callback:
                        progress_callback(f'quick window {current_center}Ma: {sample_count} ')

                else:
                    # 样本数不足
                    mean_val = np.nan
                    std_error = np.nan
                    sample_count = len(window_data)
                    skipped_low_samples += 1

                    # 对于无效数据也创建组合值
                    combo_value = f"{current_center}-NaN"

                    if progress_callback:
                        progress_callback(f'skip window {current_center}Ma:  ({sample_count} < {min_samples})')

                # 保存结果 - 使用动态列名
                results.append({
                    age_column: current_center,  # 使用实际的X轴列名
                    f'{target_column}_mean': mean_val,  # 使用Y轴列名_mean
                    f'{age_column}-{target_column}_mean': combo_value,  # 新的组合列
                    'std_error': std_error,
                    'sample_count': sample_count,
                    'window_low': window_low,
                    'window_high': window_high
                })

            except Exception as e:
                print(f"[ERROR] ERROR {current_center} ERROR: {str(e)}")

            # 移动到下一个窗口
            current_center += step_size

        # 分析完成
        if not results:
            print("[WARNING] QUICK ERROR")
            return None

        # 创建结果DataFrame
        results_df = pd.DataFrame(results)

        print(f"[SUCCESS] Fast moving window analysis completed:")
        print(f"[SUCCESS] Total windows: {total_windows}, Effective windows: {valid_windows}")
        print(f"[SUCCESS] Skip sample size: {skipped_low_samples} windows")
        print(f"[SUCCESS] success rate: {valid_windows / total_windows * 100:.1f}%")
        print(f"[SUCCESS] min_samples: {min_samples}")

        return results_df

    except Exception as e:
        print(f"[ERROR] QUICK ERROR: {e}")
        return None

def create_integration_from_processor(data_processor) -> MovingWindowIntegration:
    """
    从DataProcessor创建MovingWindowIntegration实例

    Args:
        data_processor: DataProcessor实例

    Returns:
        MovingWindowIntegration实例
    """
    if data_processor.data is None:
        raise ValueError("DataProcessor ERROR")

    integration = MovingWindowIntegration(data_processor)

    # 显示检测结果
    if integration.filter_manager:
        detected = integration.filter_manager.get_detected_columns()
        if detected:

            for key, value in detected.items():
                print(f"[INFO]   {key} -> {value}")
        else:
            print()

    return integration