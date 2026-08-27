"""
移动窗口边界处理分析器
geochemistry/boundary_analyzer.py

处理移动窗口分析中边界点的不同分配策略 - 添加性能监控版本
"""

import numpy as np
import pandas as pd
import time
from typing import Dict, List, Tuple, Optional, Any
import warnings

# 导入性能监控模块
try:
    from performance_profiler import get_profiler
    PERFORMANCE_MONITORING = True
except ImportError:
    print("")
    PERFORMANCE_MONITORING = False
    def get_profiler():
        return None

warnings.filterwarnings('ignore')


class BoundaryAnalyzer:
    """移动窗口边界处理分析器"""

    def __init__(self):
        self.boundary_methods = {
            'exclusive': self._exclusive_boundary,
            'inclusive': self._inclusive_boundary,
            'left_priority': self._left_priority_boundary,
            'right_priority': self._right_priority_boundary,
            'weighted_overlap': self._weighted_overlap_boundary
        }

    # 在 boundary_analyzer.py 的 analyze_with_boundary_handling 方法中修改参数提取部分：

    def analyze_with_boundary_handling(self, data: pd.DataFrame, params: Dict, progress_callback=None) -> Dict:
        """
        执行带边界处理的移动窗口分析 - 修复参数提取问题
        """
        profiler = get_profiler() if PERFORMANCE_MONITORING else None

        try:
            # 新增：获取最小样本数参数
            min_samples = params.get('min_samples', 5)

            # 添加进度回调支持
            if progress_callback:
                progress_callback(f"[BOUNDARY] Start boundary processing analysis... (min_samples: {min_samples})")

            if profiler:
                with profiler.profile_operation("边界分析-参数提取"):
                    # 修复：兼容两种参数名
                    age_col = params.get('age_column') or params.get('age_col')
                    target_col = params.get('target_column') or params.get('target_col')

                    if not age_col:
                        raise ValueError("缺少年龄列参数 (age_column 或 age_col)")
                    if not target_col:
                        raise ValueError("缺少目标列参数 (target_column 或 target_col)")

                    min_age = params['min_age']
                    max_age = params['max_age']
                    window_size = params['window_size']
                    step_size = params['step_size']
                    boundary_mode = params.get('boundary_mode', 'exclusive')

                    profiler.check_analysis_path("边界处理分析", f"模式={boundary_mode}, 最小样本数={min_samples}")

                    if progress_callback:
                        progress_callback(f"[MODE] Boundary mode: {boundary_mode}, Minimum sample size: {min_samples}")
            else:
                # 修复：兼容两种参数名
                age_col = params.get('age_column') or params.get('age_col')
                target_col = params.get('target_column') or params.get('target_col')

                if not age_col:
                    raise ValueError("缺少年龄列参数 (age_column 或 age_col)")
                if not target_col:
                    raise ValueError("缺少目标列参数 (target_column 或 target_col)")

                min_age = params['min_age']
                max_age = params['max_age']
                window_size = params['window_size']
                step_size = params['step_size']
                boundary_mode = params.get('boundary_mode', 'exclusive')

                if progress_callback:
                    progress_callback(f"[MODE] 边界模式: {boundary_mode}, 最小样本数: {min_samples}")

            # 修复：确保 analysis_data 被正确定义
            if profiler:
                with profiler.profile_operation("边界分析-数据准备"):
                    # 数据准备
                    analysis_data = data[[age_col, target_col]].copy()
                    original_size = len(analysis_data)
                    analysis_data = analysis_data.dropna()
                    cleaned_size = len(analysis_data)

                    profiler.log_data_size("边界分析输入数据", original_size)
                    profiler.log_data_size("边界分析清理后数据", cleaned_size)

                    if progress_callback:
                        progress_callback(f"[DATA] 准备数据: {len(analysis_data)} 行有效数据")
            else:
                # 数据准备
                analysis_data = data[[age_col, target_col]].copy()
                analysis_data = analysis_data.dropna()

                if progress_callback:
                    progress_callback(f"[DATA] 准备数据: {len(analysis_data)} 行有效数据")

            # 生成窗口
            if profiler:
                with profiler.profile_operation("边界分析-窗口生成"):
                    if progress_callback:
                        progress_callback("[WINDOW] 生成移动窗口...")
                    windows = self._generate_windows(min_age, max_age, window_size, step_size)

                    profiler.log_operation_count("窗口总数", len(windows))
                    if progress_callback:
                        progress_callback(f"[INFO] 生成了 {len(windows)} 个窗口")
            else:
                if progress_callback:
                    progress_callback("[WINDOW] 生成移动窗口...")
                windows = self._generate_windows(min_age, max_age, window_size, step_size)

                if progress_callback:
                    progress_callback(f"[INFO] 生成了 {len(windows)} 个窗口")

            # 根据边界模式处理
            if params.get('enable_boundary_comparison', False):
                if profiler:
                    with profiler.profile_operation("边界分析-多方法比较"):
                        profiler.check_analysis_path("多边界方法比较")
                        if progress_callback:
                            progress_callback("[COMPARE] 比较所有边界处理方法...")
                        results = self._compare_all_boundary_methods(analysis_data, windows, age_col, target_col,
                                                                     params, progress_callback, min_samples)
                else:
                    if progress_callback:
                        progress_callback("[COMPARE] 比较所有边界处理方法...")
                    results = self._compare_all_boundary_methods(analysis_data, windows, age_col, target_col, params,
                                                                 progress_callback, min_samples)
            else:
                if profiler:
                    with profiler.profile_operation("边界分析-单方法处理"):
                        profiler.check_analysis_path("单边界方法", f"模式={boundary_mode}")
                        if progress_callback:
                            progress_callback(f"[EXEC] 执行 {boundary_mode} 边界处理...")
                        results = self._single_boundary_analysis(analysis_data, windows, age_col, target_col,
                                                                 boundary_mode, params, progress_callback, min_samples)
                else:
                    if progress_callback:
                        progress_callback(f"[EXEC] 执行 {boundary_mode} 边界处理...")
                    results = self._single_boundary_analysis(analysis_data, windows, age_col, target_col, boundary_mode,
                                                             params, progress_callback, min_samples)

            if progress_callback:
                progress_callback("[SUCCESS] 边界处理分析完成！")

            return results

        except Exception as e:
            if progress_callback:
                progress_callback(f"[ERROR] 边界处理分析失败: {str(e)}")
            raise Exception(f"边界处理分析失败: {str(e)}")

    def _generate_windows(self, min_age: float, max_age: float, window_size: float, step_size: float) -> List[
        Tuple[float, float, float]]:
        """生成窗口列表 (center, start, end) - 修复版，包含详细调试信息"""

        # 🔍 添加总体调试信息
        print(f"\n🔍 [WINDOW-GENERATION-DEBUG] 开始生成窗口")
        print(f"🔍 参数: min_age={min_age}, max_age={max_age}, window_size={window_size}, step_size={step_size}")

        windows = []
        current_center = min_age + window_size / 2
        window_count = 0

        print(f"🔍 起始中心: {current_center}")
        print(f"🔍 预计窗口数: {int((max_age - min_age - window_size) / step_size) + 1}")

        while current_center + window_size / 2 <= max_age:
            start = current_center - window_size / 2
            end = current_center + window_size / 2
            windows.append((current_center, start, end))
            window_count += 1

            # 🔍 重点调试1600-1700Ma范围的窗口
            if 1600 <= current_center <= 1700:
                print(f"🎯 [1650Ma-AREA] 窗口{window_count}: 中心={current_center}Ma, 范围={start}-{end}")

                # 检查是否是1650Ma的精确匹配
                if current_center == 1650:
                    print(f"✅ [EXACT-MATCH] 找到1650Ma精确窗口!")
                elif abs(current_center - 1650) <= step_size / 2:
                    print(f"📍 [CLOSE-MATCH] 最接近1650Ma的窗口 (距离: {abs(current_center - 1650)}Ma)")

            # 🔍 显示前5个和后5个窗口用于验证
            if window_count <= 5:
                print(f"🔍 [EARLY-WINDOW] 窗口{window_count}: 中心={current_center}Ma, 范围={start}-{end}")

            current_center += step_size

        # 🔍 显示最后几个窗口
        if len(windows) > 5:
            print(f"🔍 [LATE-WINDOW] 最后5个窗口:")
            for i, (center, start, end) in enumerate(windows[-5:]):
                print(f"🔍   窗口{len(windows) - 4 + i}: 中心={center}Ma, 范围={start}-{end}")

        # 🔍 总结信息
        print(f"🔍 [SUMMARY] 总共生成了 {len(windows)} 个窗口")
        print(f"🔍 [SUMMARY] 第一个窗口中心: {windows[0][0] if windows else 'None'}")
        print(f"🔍 [SUMMARY] 最后一个窗口中心: {windows[-1][0] if windows else 'None'}")

        # 🔍 专门检查是否有1650Ma窗口
        has_1650_exact = any(abs(w[0] - 1650) < 0.1 for w in windows)
        print(f"🔍 [1650-CHECK] 是否有1650Ma精确窗口: {has_1650_exact}")

        if not has_1650_exact:
            # 找最接近1650Ma的窗口
            closest_window = min(windows, key=lambda w: abs(w[0] - 1650))
            distance = abs(closest_window[0] - 1650)
            print(
                f"🔍 [CLOSEST] 最接近1650Ma的窗口: 中心={closest_window[0]}Ma, 范围={closest_window[1]}-{closest_window[2]}")
            print(f"🔍 [DISTANCE] 与1650Ma的距离: {distance}Ma")

            # 🚨 如果距离太远，给出警告
            if distance > 25:
                print(f"🚨 [WARNING] 距离1650Ma太远！这可能导致异常结果")

        # 🔍 检查窗口序列是否合理
        print(f"🔍 [SEQUENCE-CHECK] 检查窗口序列:")
        centers_around_1650 = [w[0] for w in windows if 1550 <= w[0] <= 1750]
        print(f"🔍 1550-1750Ma范围内的窗口中心: {centers_around_1650}")

        # 🔍 检查是否有重叠或遗漏
        if len(centers_around_1650) >= 2:
            gaps = [centers_around_1650[i + 1] - centers_around_1650[i] for i in range(len(centers_around_1650) - 1)]
            print(f"🔍 窗口间隔: {gaps}")
            if all(abs(gap - step_size) < 0.1 for gap in gaps):
                print(f"✅ [SEQUENCE-OK] 窗口序列正常")
            else:
                print(f"❌ [SEQUENCE-ERROR] 窗口序列异常！")

        return windows

    def _exclusive_boundary(self, data: pd.DataFrame, windows: List[Tuple], age_col: str) -> Dict[int, pd.DataFrame]:
        """
        互斥边界处理：每个数据点只属于一个窗口
        边界点分配给距离中心最近的窗口
        """
        window_data = {}
        ages = data[age_col].values

        for i, (center, start, end) in enumerate(windows):
            # 找到在窗口范围内的点
            in_range_mask = (ages >= start) & (ages <= end)
            candidate_data = data[in_range_mask].copy()

            if len(candidate_data) == 0:
                window_data[i] = pd.DataFrame()
                continue

            # 对于边界点，计算到窗口中心的距离
            candidate_ages = candidate_data[age_col].values
            distances = np.abs(candidate_ages - center)

            # 检查是否有其他窗口也包含这些点
            final_indices = []
            for idx, (age, dist) in enumerate(zip(candidate_ages, distances)):
                # 检查这个点是否在其他窗口中有更近的距离
                is_closest = True
                for j, (other_center, other_start, other_end) in enumerate(windows):
                    if i != j and other_start <= age <= other_end:
                        other_dist = abs(age - other_center)
                        if other_dist < dist:
                            is_closest = False
                            break

                if is_closest:
                    final_indices.append(idx)

            window_data[i] = candidate_data.iloc[final_indices].copy()

        return window_data

    def _inclusive_boundary(self, data: pd.DataFrame, windows: List[Tuple], age_col: str) -> Dict[int, pd.DataFrame]:
        """
        包容边界处理：边界数据点可以被相邻窗口共享
        """
        window_data = {}
        ages = data[age_col].values

        for i, (center, start, end) in enumerate(windows):
            # 直接包含所有在窗口范围内的点
            in_range_mask = (ages >= start) & (ages <= end)
            window_data[i] = data[in_range_mask].copy()

        return window_data

    def _left_priority_boundary(self, data: pd.DataFrame, windows: List[Tuple], age_col: str) -> Dict[int, pd.DataFrame]:
        """
        左优先边界处理：边界点优先归属于左侧（年龄较大）窗口
        """
        window_data = {}
        ages = data[age_col].values
        assigned_indices = set()

        # 从左到右处理窗口
        for i, (center, start, end) in enumerate(windows):
            in_range_mask = (ages >= start) & (ages <= end)
            candidate_indices = np.where(in_range_mask)[0]

            # 只取还未被分配的点
            available_indices = [idx for idx in candidate_indices if idx not in assigned_indices]

            if available_indices:
                window_data[i] = data.iloc[available_indices].copy()
                assigned_indices.update(available_indices)
            else:
                window_data[i] = pd.DataFrame()

        return window_data

    def _right_priority_boundary(self, data: pd.DataFrame, windows: List[Tuple], age_col: str) -> Dict[int, pd.DataFrame]:
        """
        右优先边界处理：边界点优先归属于右侧（年龄较小）窗口
        """
        window_data = {}
        ages = data[age_col].values
        assigned_indices = set()

        # 从右到左处理窗口
        for i in reversed(range(len(windows))):
            center, start, end = windows[i]
            in_range_mask = (ages >= start) & (ages <= end)
            candidate_indices = np.where(in_range_mask)[0]

            # 只取还未被分配的点
            available_indices = [idx for idx in candidate_indices if idx not in assigned_indices]

            if available_indices:
                window_data[i] = data.iloc[available_indices].copy()
                assigned_indices.update(available_indices)
            else:
                window_data[i] = pd.DataFrame()

        return window_data

    def _weighted_overlap_boundary(self, data: pd.DataFrame, windows: List[Tuple], age_col: str) -> Dict[int, pd.DataFrame]:
        """
        加权重叠边界处理：根据数据点到窗口中心的距离分配权重
        注意：这种方法需要在后续统计计算中考虑权重
        """
        window_data = {}
        ages = data[age_col].values

        for i, (center, start, end) in enumerate(windows):
            in_range_mask = (ages >= start) & (ages <= end)
            candidate_data = data[in_range_mask].copy()

            if len(candidate_data) == 0:
                window_data[i] = pd.DataFrame()
                continue

            # 计算权重（距离中心越近权重越大）
            candidate_ages = candidate_data[age_col].values
            distances = np.abs(candidate_ages - center)
            max_distance = (end - start) / 2  # 窗口半径

            # 使用高斯权重函数
            weights = np.exp(-(distances ** 2) / (2 * (max_distance / 3) ** 2))

            # 将权重添加到数据中
            candidate_data = candidate_data.copy()
            candidate_data['_weight'] = weights

            window_data[i] = candidate_data

        return window_data

    def _single_boundary_analysis(self, data: pd.DataFrame, windows: List[Tuple],
                                  age_col: str, target_col: str, boundary_mode: str,
                                  params: Dict, progress_callback=None, min_samples=5) -> Dict:
        """执行单一边界处理方法分析 - 添加最小样本数参数"""

        if progress_callback:
            progress_callback(f"[MODE] 使用 {boundary_mode} 模式分配数据... (最小样本数: {min_samples})")

        # 获取边界处理方法
        boundary_func = self.boundary_methods.get(boundary_mode, self._exclusive_boundary)

        # 分配数据到窗口
        window_data = boundary_func(data, windows, age_col)

        if progress_callback:
            progress_callback("[CALC] 计算窗口统计...")

        # 🔧 修复：计算统计结果 - 传递最小样本数和age_column参数
        results = self._calculate_window_statistics(
            window_data, windows, target_col, boundary_mode,
            progress_callback, min_samples, age_column=age_col  # 添加age_column参数
        )

        # 添加边界信息
        if params.get('export_boundary_info', True):
            if progress_callback:
                progress_callback("[ANALYZE] 分析边界点信息...")
            results['boundary_info'] = self._analyze_boundary_points(window_data, windows, age_col, boundary_mode)

        return results

    def _compare_all_boundary_methods(self, data: pd.DataFrame, windows: List[Tuple],
                                      age_col: str, target_col: str, params: Dict,
                                      progress_callback=None, min_samples=5) -> Dict:
        """比较所有边界处理方法 - 添加最小样本数参数"""

        comparison_results = {}
        methods = list(self.boundary_methods.keys())

        for i, (method_name, boundary_func) in enumerate(self.boundary_methods.items()):
            try:
                if progress_callback:
                    progress_callback(f"[METHOD] 分析方法 {i+1}/{len(methods)}: {method_name} (最小样本数: {min_samples})")

                # 分配数据到窗口
                window_data = boundary_func(data, windows, age_col)

                # 计算统计结果 - 传递最小样本数
                method_results = self._calculate_window_statistics(
                    window_data, windows, target_col, method_name,
                    None, min_samples  # 传递最小样本数
                )

                comparison_results[method_name] = method_results

            except Exception as e:
                print(f"[WARNING] 边界方法 {method_name} 分析失败: {e}")
                continue

        if progress_callback:
            progress_callback("[COMPARE] 生成方法比较分析...")

        # 添加比较分析
        comparison_results['comparison_analysis'] = self._generate_method_comparison(comparison_results)

        return comparison_results

    def _calculate_window_statistics(self, window_data: Dict[int, pd.DataFrame],
                                     windows: List[Tuple], target_col: str, method_name: str,
                                     progress_callback=None, min_samples=5, age_column=None) -> Dict:
        """计算窗口统计结果 - 使用传入的最小样本数"""
        profiler = get_profiler() if PERFORMANCE_MONITORING else None

        if profiler:
            with profiler.profile_operation(f"统计计算-{method_name}"):
                return self._calculate_statistics_internal(
                    window_data, windows, target_col, method_name,
                    progress_callback, profiler, min_samples, age_column=age_column  # 传递参数
                )
        else:
            return self._calculate_statistics_internal(
                window_data, windows, target_col, method_name,
                progress_callback, None, min_samples, age_column=age_column  # 传递参数
            )



    def _add_empty_window_results(self, results):
        """添加空窗口结果"""
        results['means'].append(np.nan)
        results['medians'].append(np.nan)
        results['stds'].append(np.nan)
        results['counts'].append(0)
        results['q25'].append(np.nan)
        results['q75'].append(np.nan)
        self._add_empty_bootstrap_results(results)
        results['boundary_points'].append([])

    def _add_empty_bootstrap_results(self, results):
        """添加空Bootstrap结果"""
        results['bootstrap_means'].append(np.nan)
        results['bootstrap_stds'].append(np.nan)
        results['bootstrap_ci_lower'].append(np.nan)
        results['bootstrap_ci_upper'].append(np.nan)

    def _calculate_weighted_statistics(self, values, weights, results):
        """计算加权统计"""
        weighted_mean = np.average(values, weights=weights)
        results['means'].append(weighted_mean)

        weighted_var = np.average((values - weighted_mean) ** 2, weights=weights)
        results['stds'].append(np.sqrt(weighted_var))

        # 其他统计量使用普通方法
        results['medians'].append(np.median(values))
        results['q25'].append(np.percentile(values, 25))
        results['q75'].append(np.percentile(values, 75))

    def _calculate_normal_statistics(self, values, results):
        """计算普通统计"""
        results['means'].append(np.mean(values))
        results['medians'].append(np.median(values))
        results['stds'].append(np.std(values, ddof=1) if len(values) > 1 else 0)
        results['q25'].append(np.percentile(values, 25))
        results['q75'].append(np.percentile(values, 75))

    def _bootstrap_analysis(self, values: np.ndarray, n_bootstrap: int = 10000, window_id: int = 0) -> np.ndarray:
        """Bootstrap重采样分析 - 添加1650Ma调试"""

        # 检查是否为1650Ma附近的窗口（基于window_id推断）
        is_1650_debug = window_id == 32  # 根据调试输出，1650Ma是第32个窗口
        # 强制调试1650Ma窗口 (窗口32)
        if window_id == 32:
            print(f"🎯 [1650Ma-FORCE-DEBUG] 窗口{window_id}, 数据: {values}")
            print(f"🎯 数据数量: {len(values)}, 范围: {np.min(values):.6f}-{np.max(values):.6f}")

        if is_1650_debug:
            print(f"🎯 [1650Ma-BOOTSTRAP-DETAIL] 详细Bootstrap过程")
            print(f"🎯 输入数据: {values}")
            print(f"🎯 数据量: {len(values)}")
            print(f"🎯 Bootstrap次数: {n_bootstrap}")

        # 设置与MATLAB兼容的随机种子
        seed = 42 + window_id * 137  # 使用质数确保不同窗口有不同的随机序列
        np.random.seed(seed)

        if is_1650_debug:
            print(f"🎯 随机种子: {seed}")

        bootstrap_means = []
        n_samples = len(values)

        # 使用与MATLAB bootstrp函数完全相同的采样策略
        for i in range(n_bootstrap):
            # MATLAB的bootstrp使用 randi(n, n, 1) 生成索引
            sample_indices = np.random.randint(0, n_samples, size=n_samples)
            sample = values[sample_indices]
            sample_mean = np.mean(sample)
            bootstrap_means.append(sample_mean)

            # 调试前几次采样
            if is_1650_debug and i < 5:
                print(f"🎯 采样 {i + 1}: 索引={sample_indices}, 样本={sample}, 均值={sample_mean:.6f}")

            # 检查异常高值的采样
            if is_1650_debug and sample_mean > 5.0 and i < 100:
                print(f"🚨 异常采样 {i + 1}: 索引={sample_indices}, 样本={sample}, 均值={sample_mean:.6f}")

        if is_1650_debug:
            bootstrap_array = np.array(bootstrap_means)
            print(f"🎯 [1650Ma-BOOTSTRAP-SUMMARY]")
            print(f"🎯 Bootstrap均值范围: {np.min(bootstrap_array):.6f} - {np.max(bootstrap_array):.6f}")
            print(f"🎯 Bootstrap均值的均值: {np.mean(bootstrap_array):.6f}")
            print(f"🎯 Bootstrap均值的标准差: {np.std(bootstrap_array):.6f}")

            # 统计异常高值
            high_count = np.sum(bootstrap_array > 5.0)
            print(
                f"🎯 >5.0的Bootstrap均值数量: {high_count}/{len(bootstrap_array)} ({high_count / len(bootstrap_array) * 100:.2f}%)")

        return np.array(bootstrap_means)

    # 删除重复的方法，保留这一个修复版本
    def _calculate_statistics_internal(self, window_data: Dict[int, pd.DataFrame],
                                       windows: List[Tuple], target_col: str, method_name: str,
                                       progress_callback=None, profiler=None, min_samples=5,
                                       age_column=None) -> Dict:
        """内部统计计算函数 - 使用传入的最小样本数参数和动态列名"""

        if progress_callback:
            progress_callback(f"[CALC] 计算 {len(windows)} 个窗口的统计量... (最小样本数: {min_samples})")

        # 🔧 修复：使用动态列名构建结果字典
        results = {
            'method': method_name,
            'age_column': age_column,  # 保存原始列名信息
            'target_column': target_col,  # 保存原始列名信息
            'window_centers': [],
            'window_starts': [],
            'window_ends': [],
            'means': [],
            'medians': [],
            'stds': [],
            'counts': [],
            'q25': [],
            'q75': [],
            'bootstrap_means': [],
            'bootstrap_stds': [],
            'bootstrap_ci_lower': [],
            'bootstrap_ci_upper': [],
            'boundary_points': []
        }

        valid_windows = 0
        total_bootstrap_samples = 0

        print(f"🔧 [DEBUG] 开始处理 {len(windows)} 个窗口，最小样本数要求: {min_samples}")
        print(f"🔧 [DEBUG] 动态列名: age_column={age_column}, target_column={target_col}")

        for i, (center, start, end) in enumerate(windows):
            # 每处理10个窗口更新一次进度
            if progress_callback and i % 10 == 0:
                progress_callback(f"[WINDOW] Processing window {i + 1}/{len(windows)} (中心: {center:.0f}Ma)")

            window_df = window_data.get(i, pd.DataFrame())

            # 🔧 关键修改：检查空窗口，直接跳过
            if len(window_df) == 0:
                print(f"[SKIP] 跳过空窗口: {center:.0f}Ma")
                continue

            # 获取目标数据
            values = window_df[target_col].values

            # 🔧 关键修改：使用传入的最小样本数参数
            if len(values) < min_samples:
                print(f"[SKIP] 跳过样本数不足的窗口: {center:.0f}Ma (样本数: {len(values)} < {min_samples})")
                continue

            # 🔧 只有满足条件的窗口才会被添加到结果中
            print(f"[PROCESS] 处理有效窗口: {center:.0f}Ma (样本数: {len(values)})")
            valid_windows += 1

            # 添加窗口信息到结果
            results['window_centers'].append(center)
            results['window_starts'].append(start)
            results['window_ends'].append(end)
            results['counts'].append(len(window_df))

            # 计算基础统计
            if '_weight' in window_df.columns and method_name == 'weighted_overlap':
                # 加权统计
                weights = window_df['_weight'].values
                self._calculate_weighted_statistics(values, weights, results)
            else:
                # 普通统计
                self._calculate_normal_statistics(values, results)

            # Bootstrap分析
            if profiler:
                with profiler.profile_operation(f"Bootstrap-窗口{i}"):
                    bootstrap_means = self._bootstrap_analysis(values, n_bootstrap=10000, window_id=i + 1)
                    total_bootstrap_samples += 10000

                    # 使用MATLAB相同的统计计算方法
                    bootstrap_mean = np.mean(bootstrap_means)
                    bootstrap_std = np.std(bootstrap_means, ddof=0)

                    results['bootstrap_means'].append(bootstrap_mean)
                    results['bootstrap_stds'].append(bootstrap_std)
                    results['bootstrap_ci_lower'].append(np.percentile(bootstrap_means, 2.5))
                    results['bootstrap_ci_upper'].append(np.percentile(bootstrap_means, 97.5))
            else:
                bootstrap_means = self._bootstrap_analysis(values, n_bootstrap=10000, window_id=i + 1)
                total_bootstrap_samples += 10000

                # 使用MATLAB相同的统计计算方法
                bootstrap_mean = np.mean(bootstrap_means)
                bootstrap_std = np.std(bootstrap_means, ddof=0)

                results['bootstrap_means'].append(bootstrap_mean)
                results['bootstrap_stds'].append(bootstrap_std)
                results['bootstrap_ci_lower'].append(np.percentile(bootstrap_means, 2.5))
                results['bootstrap_ci_upper'].append(np.percentile(bootstrap_means, 97.5))

            # 识别边界点
            boundary_points = self._identify_boundary_points(window_df, start, end, target_col)
            results['boundary_points'].append(boundary_points)

        # 记录统计信息
        if profiler:
            profiler.log_operation_count("有效窗口数", valid_windows)
            profiler.log_bootstrap_details(len(windows), 10000, total_bootstrap_samples)

        if progress_callback:
            progress_callback(f"[SUCCESS] 统计完成: {valid_windows}/{len(windows)} 个有效窗口")

        print(
            f"🔧 [FINAL] 最终有效窗口数: {valid_windows}, 原始窗口数: {len(windows)}, 跳过: {len(windows) - valid_windows}")
        print(f"🔧 [FINAL] 使用的最小样本数阈值: {min_samples}")

        return results

    def _identify_boundary_points(self, window_data: pd.DataFrame, start: float, end: float, age_col: str) -> List[Dict]:
        """识别边界点"""
        if len(window_data) == 0 or age_col not in window_data.columns:
            return []

        boundary_points = []
        tolerance = (end - start) * 0.05  # 5%的窗口大小作为边界容差

        for idx, row in window_data.iterrows():
            age = row[age_col]
            is_boundary = False
            boundary_type = None

            if abs(age - start) <= tolerance:
                is_boundary = True
                boundary_type = 'left'
            elif abs(age - end) <= tolerance:
                is_boundary = True
                boundary_type = 'right'

            if is_boundary:
                boundary_points.append({
                    'index': idx,
                    'age': age,
                    'type': boundary_type,
                    'distance_to_start': abs(age - start),
                    'distance_to_end': abs(age - end)
                })

        return boundary_points

    def _analyze_boundary_points(self, window_data: Dict[int, pd.DataFrame],
                                 windows: List[Tuple], age_col: str, method_name: str) -> Dict:
        """分析边界点分布"""

        boundary_analysis = {
            'method': method_name,
            'total_boundary_points': 0,
            'boundary_distribution': {},
            'overlap_statistics': {},
            'boundary_point_details': []
        }

        # 统计所有边界点
        all_boundary_points = []

        for i, (center, start, end) in enumerate(windows):
            window_df = window_data.get(i, pd.DataFrame())
            boundary_points = self._identify_boundary_points(window_df, start, end, age_col)

            boundary_analysis['boundary_distribution'][f'window_{i}'] = {
                'count': len(boundary_points),
                'left_boundary': len([p for p in boundary_points if p['type'] == 'left']),
                'right_boundary': len([p for p in boundary_points if p['type'] == 'right'])
            }

            all_boundary_points.extend(boundary_points)

        boundary_analysis['total_boundary_points'] = len(all_boundary_points)
        boundary_analysis['boundary_point_details'] = all_boundary_points

        # 计算重叠统计
        if method_name in ['inclusive', 'weighted_overlap']:
            boundary_analysis['overlap_statistics'] = self._calculate_overlap_stats(window_data, windows, age_col)

        return boundary_analysis

    def _calculate_overlap_stats(self, window_data: Dict[int, pd.DataFrame],
                                 windows: List[Tuple], age_col: str) -> Dict:
        """计算重叠统计"""
        overlap_stats = {
            'overlapping_pairs': [],
            'total_shared_points': 0,
            'max_overlap_count': 0
        }

        # 检查相邻窗口的重叠
        for i in range(len(windows) - 1):
            window1_data = window_data.get(i, pd.DataFrame())
            window2_data = window_data.get(i + 1, pd.DataFrame())

            if len(window1_data) == 0 or len(window2_data) == 0:
                continue

            # 找到共同的数据点（基于年龄值）
            ages1 = set(window1_data[age_col].values)
            ages2 = set(window2_data[age_col].values)
            shared_ages = ages1.intersection(ages2)

            if shared_ages:
                overlap_info = {
                    'window_pair': (i, i + 1),
                    'shared_count': len(shared_ages),
                    'shared_ages': list(shared_ages)
                }
                overlap_stats['overlapping_pairs'].append(overlap_info)
                overlap_stats['total_shared_points'] += len(shared_ages)
                overlap_stats['max_overlap_count'] = max(overlap_stats['max_overlap_count'], len(shared_ages))

        return overlap_stats

    def _generate_method_comparison(self, comparison_results: Dict) -> Dict:
        """生成方法比较分析"""

        comparison_analysis = {
            'summary': {},
            'differences': {},
            'recommendations': []
        }

        # 提取所有方法的均值结果
        method_means = {}
        for method, results in comparison_results.items():
            if method != 'comparison_analysis' and 'means' in results:
                method_means[method] = np.array(results['means'])

        # 计算方法间差异
        if len(method_means) >= 2:
            method_names = list(method_means.keys())

            for i, method1 in enumerate(method_names):
                for method2 in method_names[i + 1:]:
                    means1 = method_means[method1]
                    means2 = method_means[method2]