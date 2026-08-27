"""
增强的地球化学分析器 - core/analyzer.py (更新版)
集成筛选、移动窗口分析等核心功能
"""

import pandas as pd
import numpy as np
from config.languages import language_manager


class GeochemicalAnalyzer:
    """地球化学数据分析器"""

    def __init__(self, data):
        self.data = data
        self.filtered_data = None
        self.analysis_results = None

    def apply_filters(self, filters):
        """应用多重筛选条件"""
        try:
            if self.data is None:
                print("[ERROR] 没有可用的数据进行筛选")
                return None

            filtered_data = self.data.copy()

            if not filters:
                self.filtered_data = filtered_data
                return filtered_data

            print(f"[DEBUG] 开始应用 {len(filters)} 个筛选条件")
            print(f"[DEBUG] 原始数据行数: {len(filtered_data)}")

            for i, (column, condition, value) in enumerate(filters):
                if column not in filtered_data.columns:
                    print(f"[WARNING] 列 '{column}' 不存在于数据中")
                    continue

                # 确保列是数值型
                if not pd.api.types.is_numeric_dtype(filtered_data[column]):
                    try:
                        filtered_data[column] = pd.to_numeric(filtered_data[column], errors='coerce')
                        print(f"[INFO] 列 '{column}' 已转换为数值型")
                    except Exception as e:
                        print(f"[WARNING] 无法将列 '{column}' 转换为数值型: {e}")
                        continue

                # 记录筛选前的有效数据数量
                before_count = filtered_data[column].notna().sum()

                try:
                    # 应用筛选条件
                    if condition == ">=":
                        mask = filtered_data[column] >= value
                    elif condition == "<=":
                        mask = filtered_data[column] <= value
                    elif condition == ">":
                        mask = filtered_data[column] > value
                    elif condition == "<":
                        mask = filtered_data[column] < value
                    else:
                        print(f"[WARNING] 未知的筛选条件: {condition}")
                        continue

                    # 将不符合条件的数据设为NaN（保持MATLAB风格的筛选逻辑）
                    filtered_data.loc[~mask, column] = np.nan

                    # 记录筛选后的有效数据数量
                    after_count = filtered_data[column].notna().sum()
                    print(f"[DEBUG] 筛选条件 {i + 1}: {column} {condition} {value}")
                    print(f"[DEBUG] 有效数据: {before_count} -> {after_count} (减少 {before_count - after_count})")

                except Exception as e:
                    print(f"[ERROR] 应用筛选条件时出错: {column} {condition} {value}, 错误: {str(e)}")
                    continue

            self.filtered_data = filtered_data

            # 统计最终结果
            valid_rows_info = []
            for col in filtered_data.select_dtypes(include=[np.number]).columns:
                valid_count = filtered_data[col].notna().sum()
                if valid_count > 0:
                    valid_rows_info.append(f"{col}: {valid_count}")

            print(f"[DEBUG] 筛选完成")
            print(f"[DEBUG] 各列有效数据统计: {', '.join(valid_rows_info[:5])}")  # 只显示前5列

            return filtered_data

        except Exception as e:
            print(f"[ERROR] 筛选数据时发生错误: {str(e)}")
            self.filtered_data = self.data.copy() if self.data is not None else None
            return self.filtered_data

    def remove_outliers(self, column, lower_percentile=2.5, upper_percentile=97.5):
        """去除异常值"""
        try:
            if self.filtered_data is None:
                print("[WARNING] 没有筛选数据可用于异常值处理")
                return None

            if column not in self.filtered_data.columns:
                print(f"[WARNING] 列 '{column}' 不存在")
                return None

            # 获取有效数据
            data_col = self.filtered_data[column].dropna()
            if len(data_col) == 0:
                print(f"[WARNING] 列 '{column}' 没有有效数据")
                return None

            before_count = len(data_col)

            try:
                # 计算百分位数
                lower_bound = np.percentile(data_col, lower_percentile)
                upper_bound = np.percentile(data_col, upper_percentile)

                print(f"[DEBUG] 异常值检测范围: {lower_bound:.4f} - {upper_bound:.4f}")

            except Exception as e:
                print(f"[ERROR] 计算百分位数时出错: {str(e)}")
                return self.filtered_data

            try:
                # 应用异常值筛选
                mask = (self.filtered_data[column] >= lower_bound) & (self.filtered_data[column] <= upper_bound)
                self.filtered_data.loc[~mask, column] = np.nan

                after_count = self.filtered_data[column].notna().sum()
                removed_count = before_count - after_count

                print(f"[INFO] 异常值处理完成: {column}")
                print(f"[INFO] 移除了 {removed_count} 个异常值 ({removed_count/before_count*100:.1f}%)")

            except Exception as e:
                print(f"[ERROR] 应用异常值筛选时出错: {str(e)}")

            return self.filtered_data

        except Exception as e:
            print(f"[ERROR] 去除异常值时发生错误: {str(e)}")
            return self.filtered_data

    def moving_window_analysis(self, age_column, target_column, window_size=200, step_size=50,
                               min_age=100, max_age=4000, progress_callback=None):
        """移动窗口分析 - MATLAB兼容版"""
        try:
            if self.filtered_data is None:
                print("[ERROR] 没有筛选数据可用于分析")
                return None

            # 验证列是否存在
            if age_column not in self.filtered_data.columns:
                print(f"[ERROR] 年龄列 '{age_column}' 不存在")
                return None

            if target_column not in self.filtered_data.columns:
                print(f"[ERROR] 目标列 '{target_column}' 不存在")
                return None

            # 数据类型转换和验证
            try:
                age_data = pd.to_numeric(self.filtered_data[age_column], errors='coerce')
                target_data = pd.to_numeric(self.filtered_data[target_column], errors='coerce')
            except Exception as e:
                print(f"[ERROR] 数据类型转换失败: {str(e)}")
                return None

            # 检查有效数据
            valid_mask = age_data.notna() & target_data.notna()
            valid_count = valid_mask.sum()

            if valid_count == 0:
                print("[ERROR] 没有同时具有有效年龄和目标值的数据")
                return None

            print(f"[INFO] MATLAB兼容移动窗口分析开始:")
            print(f"[INFO] 有效数据对数: {valid_count}")
            print(f"[INFO] 年龄范围: {age_data[valid_mask].min():.1f} - {age_data[valid_mask].max():.1f} Ma")
            print(f"[INFO] 目标值范围: {target_data[valid_mask].min():.6f} - {target_data[valid_mask].max():.6f}")
            print(f"[INFO] 窗口参数: 大小={window_size}Ma, 步长={step_size}Ma, 范围={min_age}-{max_age}Ma")

            # 计算窗口参数 - MATLAB风格：从高年龄开始向低年龄移动
            results = []
            current_low = max_age - window_size
            current_high = max_age
            window_id = 0

            valid_windows = 0
            total_windows = 0

            # 进度回调初始化
            if progress_callback:
                try:
                    progress_callback(
                        current_high, 0, 0, False,
                        message=language_manager.get_text('analysis_init', '正在初始化移动窗口分析...')
                    )
                except:
                    pass

            # 移动窗口主循环 - MATLAB风格
            while current_low >= min_age:
                total_windows += 1
                window_id += 1
                window_center = (current_low + current_high) / 2

                try:
                    # 获取窗口内的数据
                    window_mask = (age_data >= current_low) & (age_data <= current_high) & valid_mask
                    window_data = target_data[window_mask].dropna()

                    if len(window_data) >= 5:  # 最少需要5个样本
                        valid_windows += 1
                        try:
                            # MATLAB兼容的Bootstrap统计分析
                            window_array = window_data.values

                            # 设置与MATLAB兼容的随机种子
                            seed = 42 + window_id * 137  # 使用质数确保不同窗口有不同的随机序列
                            np.random.seed(seed)

                            bootstrap_means = []

                            # 进行10000次Bootstrap采样 - 使用MATLAB兼容的方法
                            for _ in range(10000):
                                # MATLAB的bootstrp使用 randi(n, n, 1) 生成索引
                                sample_indices = np.random.randint(0, len(window_array), size=len(window_array))
                                sample = window_array[sample_indices]
                                bootstrap_means.append(np.mean(sample))

                            # 计算统计量 - 使用MATLAB相同的方法
                            mean_val = np.mean(bootstrap_means)
                            std_error = np.std(bootstrap_means, ddof=0)  # 使用N作为分母，与MATLAB一致
                            confidence_interval = 2 * std_error  # 2σ误差
                            sample_count = len(window_data)

                            print(f"[DEBUG] 窗口 {window_id} (中心: {window_center:.0f}Ma): {sample_count} 样本, "
                                  f"均值={mean_val:.6f}, 2σ误差={confidence_interval:.6f}")

                            # 更新进度回调
                            if progress_callback:
                                try:
                                    progress_callback(window_center, sample_count, mean_val, True)
                                except Exception as e:
                                    print(f"[WARNING] 进度回调出错: {e}")

                        except Exception as e:
                            print(f"[ERROR] Bootstrap分析出错 (窗口中心 {window_center}): {str(e)}")
                            mean_val = np.nan
                            confidence_interval = np.nan
                            sample_count = len(window_data)

                            if progress_callback:
                                try:
                                    progress_callback(window_center, sample_count, 0, False)
                                except:
                                    pass
                    else:
                        # 样本数不足
                        mean_val = np.nan
                        confidence_interval = np.nan
                        sample_count = len(window_data)

                        if sample_count > 0:
                            print(
                                f"[DEBUG] 窗口 {window_id} (中心: {window_center:.0f}Ma): 样本数不足 ({sample_count} < 5)")

                        # 更新进度回调
                        if progress_callback:
                            try:
                                progress_callback(window_center, sample_count, 0, False)
                            except:
                                pass

                    # 保存结果
                    results.append({
                        'age': window_center,
                        'mean': mean_val,
                        'std_error': confidence_interval,
                        'sample_count': sample_count,
                        'window_low': current_low,
                        'window_high': current_high,
                        'window_id': window_id
                    })

                except Exception as e:
                    print(f"[ERROR] 处理窗口 {window_id} (中心: {window_center:.0f}Ma) 时出错: {str(e)}")
                    if progress_callback:
                        try:
                            progress_callback(window_center, 0, 0, False)
                        except:
                            pass

                # 移动到下一个窗口 - MATLAB风格：向低年龄方向移动
                current_low -= step_size
                current_high -= step_size

            # 分析完成
            if not results:
                print("[WARNING] 移动窗口分析没有产生任何结果")
                return None

            # 创建结果DataFrame并按年龄排序（从小到大）
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('age').reset_index(drop=True)
            self.analysis_results = results_df

            print(f"[SUCCESS] MATLAB兼容移动窗口分析完成:")
            print(f"[SUCCESS] 总窗口数: {total_windows}, 有效窗口数: {valid_windows}")
            print(f"[SUCCESS] 成功率: {valid_windows / total_windows * 100:.1f}%")

            return results_df

        except Exception as e:
            print(f"[ERROR] 移动窗口分析发生错误: {str(e)}")
            return None

    def get_analysis_summary(self):
        """获取分析摘要信息"""
        if self.analysis_results is None:
            return None

        try:
            valid_results = self.analysis_results.dropna(subset=['mean'])

            summary = {
                'total_windows': len(self.analysis_results),
                'valid_windows': len(valid_results),
                'success_rate': len(valid_results) / len(self.analysis_results) * 100,
                'age_range': (self.analysis_results['age'].min(), self.analysis_results['age'].max()),
                'mean_range': (valid_results['mean'].min(), valid_results['mean'].max()) if len(valid_results) > 0 else (None, None),
                'sample_stats': {
                    'min_samples': valid_results['sample_count'].min() if len(valid_results) > 0 else 0,
                    'max_samples': valid_results['sample_count'].max() if len(valid_results) > 0 else 0,
                    'avg_samples': valid_results['sample_count'].mean() if len(valid_results) > 0 else 0
                }
            }

            return summary

        except Exception as e:
            print(f"[ERROR] 生成分析摘要时出错: {str(e)}")
            return None

    def export_results(self, file_path, include_invalid=False):
        """导出分析结果"""
        if self.analysis_results is None:
            print("[ERROR] 没有分析结果可以导出")
            return False

        try:
            if include_invalid:
                export_data = self.analysis_results
            else:
                export_data = self.analysis_results.dropna(subset=['mean'])

            # 重命名列名
            export_data.rename(columns={'std_error': '2SE'}, inplace=True)

            if file_path.endswith('.csv'):
                export_data.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                export_data.to_excel(file_path, index=False)
            else:
                # 默认CSV格式
                export_data.to_csv(file_path + '.csv', index=False)

            print(f"[SUCCESS] 分析结果已导出到: {file_path}")
            return True

        except Exception as e:
            print(f"[ERROR] 导出分析结果失败: {str(e)}")
            return False

    def validate_data_for_analysis(self, age_column, target_column):
        """验证数据是否适合进行分析"""
        if self.filtered_data is None:
            return False, language_manager.get_text('no_filtered_data', '没有筛选后的数据')

        if age_column not in self.filtered_data.columns:
            return False, language_manager.get_text('age_column_missing', f'年龄列 "{age_column}" 不存在')

        if target_column not in self.filtered_data.columns:
            return False, language_manager.get_text('target_column_missing', f'目标列 "{target_column}" 不存在')

        # 检查数据类型
        try:
            age_data = pd.to_numeric(self.filtered_data[age_column], errors='coerce')
            target_data = pd.to_numeric(self.filtered_data[target_column], errors='coerce')
        except:
            return False, language_manager.get_text('numeric_conversion_failed', '数据类型转换失败')

        # 检查有效数据数量
        valid_mask = age_data.notna() & target_data.notna()
        valid_count = valid_mask.sum()

        if valid_count < 10:
            return False, language_manager.get_text('insufficient_data', f'有效数据太少（{valid_count} < 10）')

        # 检查年龄范围
        age_range = age_data[valid_mask].max() - age_data[valid_mask].min()
        if age_range < 50:
            return False, language_manager.get_text('insufficient_age_range', f'年龄范围太小（{age_range:.1f} Ma < 50 Ma）')

        return True, language_manager.get_text('data_validation_passed', '数据验证通过')

    def get_recommended_parameters(self, age_column):
        """根据数据特征推荐分析参数"""
        if self.filtered_data is None:
            return None

        try:
            age_data = pd.to_numeric(self.filtered_data[age_column], errors='coerce')
            valid_ages = age_data.dropna()

            if len(valid_ages) == 0:
                return None

            min_age = valid_ages.min()
            max_age = valid_ages.max()
            age_range = max_age - min_age

            # 根据年龄范围推荐参数
            recommendations = {}

            if age_range > 3000:  # 全地质历史
                recommendations = {
                    'min_age': max(100, int(min_age)),
                    'max_age': min(4000, int(max_age)),
                    'window_size': 200,
                    'step_size': 50,
                    'description': language_manager.get_text('full_geological_history', '全地质历史分析')
                }
            elif max_age > 2500:  # 古老岩石
                recommendations = {
                    'min_age': max(2500, int(min_age)),
                    'max_age': min(3500, int(max_age)),
                    'window_size': 100,
                    'step_size': 25,
                    'description': language_manager.get_text('archean_analysis', '古老岩石分析')
                }
            elif max_age < 1000:  # 显生宙
                recommendations = {
                    'min_age': max(50, int(min_age)),
                    'max_age': min(600, int(max_age)),
                    'window_size': 50,
                    'step_size': 25,
                    'description': language_manager.get_text('phanerozoic_analysis', '显生宙分析')
                }
            else:  # 中等范围
                recommendations = {
                    'min_age': int(min_age),
                    'max_age': int(max_age),
                    'window_size': max(50, int(age_range / 10)),
                    'step_size': max(25, int(age_range / 20)),
                    'description': language_manager.get_text('custom_range_analysis', '自定义范围分析')
                }

            recommendations['data_range'] = (float(min_age), float(max_age))
            recommendations['sample_count'] = len(valid_ages)

            return recommendations

        except Exception as e:
            print(f"[ERROR] 生成推荐参数时出错: {str(e)}")
            return None

    def get_filter_statistics(self):
        """获取筛选统计信息"""
        if self.data is None:
            return None

        try:
            stats = {
                'original_rows': len(self.data),
                'original_columns': len(self.data.columns),
                'numeric_columns': len(self.data.select_dtypes(include=[np.number]).columns)
            }

            if self.filtered_data is not None:
                # 计算各列的有效数据数量
                column_stats = {}
                for col in self.filtered_data.select_dtypes(include=[np.number]).columns:
                    original_count = self.data[col].notna().sum() if col in self.data.columns else 0
                    filtered_count = self.filtered_data[col].notna().sum()
                    retention_rate = (filtered_count / original_count * 100) if original_count > 0 else 0

                    column_stats[col] = {
                        'original': original_count,
                        'filtered': filtered_count,
                        'retention_rate': retention_rate
                    }

                stats['filtered_stats'] = column_stats
                stats['has_filtered_data'] = True
            else:
                stats['has_filtered_data'] = False

            return stats

        except Exception as e:
            print(f"[ERROR] 生成筛选统计信息时出错: {str(e)}")
            return None