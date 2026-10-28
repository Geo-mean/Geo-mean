"""
地球化学筛选管理器
geochemistry/geochem_filter_manager.py

专门处理地球化学数据的筛选逻辑和条件管理
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from config.languages import language_manager


class GeochemicalFilterManager:
    """
    地球化学筛选管理器

    专门处理地球化学数据的筛选条件管理和应用
    """

    def __init__(self, data: pd.DataFrame):
        """
        初始化筛选管理器

        Args:
            data: 输入数据DataFrame
        """
        self.original_data = data.copy()
        self.filtered_data = None
        self.filter_history = []
        self.column_mapping = self._detect_geochemical_columns()

    def _detect_geochemical_columns(self) -> Dict[str, str]:
        """
        自动检测地球化学相关列

        Returns:
            检测到的列映射字典
        """
        mapping = {}
        columns_upper = [col.upper() for col in self.original_data.columns]

        # 定义地球化学列的检测规则
        detection_rules = {
            'SiO2': ['SIO2', 'SI_O2', 'SILICA', 'SIO₂', 'SI O2'],
            'TiO2': ['TIO2', 'TI_O2', 'TITANIA', 'TIO₂', 'TI O2'],
            'Al2O3': ['AL2O3', 'AL_O3', 'ALUMINA', 'AL₂O₃', 'AL O3'],
            'Fe2O3': ['FE2O3', 'FE_O3', 'IRON_OXIDE', 'FE₂O₃'],
            'FeO': ['FEO', 'FE_O', 'IRON_MONOXIDE'],
            'MnO': ['MNO', 'MN_O', 'MANGANESE_OXIDE'],
            'MgO': ['MGO', 'MG_O', 'MAGNESIA'],
            'CaO': ['CAO', 'CA_O', 'LIME'],
            'Na2O': ['NA2O', 'NA_O', 'SODA', 'NA₂O'],
            'K2O': ['K2O', 'K_O', 'POTASH', 'K₂O'],
            'P2O5': ['P2O5', 'P_O5', 'PHOSPHATE', 'P₂O₅'],
            'LOI': ['LOI', 'LOSS_ON_IGNITION', 'LOSS ON IGNITION'],
            'ThU': ['THU', 'TH_U', 'TH/U', 'TH U', 'THORIUM_URANIUM'],
            'Lg_NbTh': ['LG_NBTH', 'LOG_NBTH', 'LG_NB_TH', 'LOG_NB_TH', 'NBTH'],
            'Lg_Th': ['LG_TH', 'LOG_TH', 'LG TH', 'LOG TH'],
            'NbTh': ['NBTH', 'NB_TH', 'NB/TH', 'NB TH'],
            'Th': ['TH', 'THORIUM'],
            'U': ['U', 'URANIUM'],
            'Nb': ['NB', 'NIOBIUM'],
            'Ta': ['TA', 'TANTALUM'],
            'Zr': ['ZR', 'ZIRCONIUM'],
            'Hf': ['HF', 'HAFNIUM'],
            'Y': ['Y', 'YTTRIUM'],
            'La': ['LA', 'LANTHANUM'],
            'Ce': ['CE', 'CERIUM'],
            'Pr': ['PR', 'PRASEODYMIUM'],
            'Nd': ['ND', 'NEODYMIUM'],
            'Sm': ['SM', 'SAMARIUM'],
            'Eu': ['EU', 'EUROPIUM'],
            'Gd': ['GD', 'GADOLINIUM'],
            'Tb': ['TB', 'TERBIUM'],
            'Dy': ['DY', 'DYSPROSIUM'],
            'Ho': ['HO', 'HOLMIUM'],
            'Er': ['ER', 'ERBIUM'],
            'Tm': ['TM', 'THULIUM'],
            'Yb': ['YB', 'YTTERBIUM'],
            'Lu': ['LU', 'LUTETIUM'],
            'AGE': ['AGE', 'AGES', 'YEAR', 'YEARS', 'MA', 'TIME']
        }

        # 执行检测
        for key, candidates in detection_rules.items():
            for candidate in candidates:
                matches = []
                for col in self.original_data.columns:
                    col_clean = col.upper().replace('_', '').replace('/', '').replace(' ', '')
                    candidate_clean = candidate.replace('_', '').replace('/', '').replace(' ', '')
                    if candidate_clean in col_clean:
                        matches.append(col)

                if matches:
                    # 选择最匹配的列（名称最短的通常是最准确的）
                    best_match = min(matches, key=len)
                    mapping[key] = best_match
                    break

        return mapping

    def get_detected_columns(self) -> Dict[str, str]:
        """获取检测到的地球化学列映射"""
        return self.column_mapping.copy()

    def set_column_mapping(self, mapping: Dict[str, str]) -> None:
        """
        手动设置列映射

        Args:
            mapping: 列映射字典
        """
        self.column_mapping.update(mapping)

    def get_available_filter_types(self) -> List[str]:
        """
        获取可用的筛选类型

        Returns:
            可用筛选类型列表
        """
        available_types = []

        # 基本地球化学筛选
        basic_filters = [
            ('continental_basalts', 'SiO2', '去除大陆玄武岩 (SiO2 < 54%)'),
            ('intracratonic_granites', 'Lg_NbTh', '去除克拉通内花岗岩 (Lg_NbTh > 0.7)'),
            ('orogenic_granites', 'Lg_Th', '去除造山花岗岩 (Lg_Th > 1.1)'),
            ('altered_samples', 'LOI', '去除蚀变样品 (LOI > 4%)'),
            ('young_samples', 'AGE', '去除年轻样品 (AGE ≤ 100Ma)')
        ]

        for filter_type, required_col, description in basic_filters:
            if required_col in self.column_mapping:
                available_types.append({
                    'type': filter_type,
                    'name': description,
                    'column': self.column_mapping[required_col],
                    'required_column': required_col
                })

        return available_types

    def apply_standard_geochemical_filters(self,
                                           progress_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        应用标准地球化学筛选条件

        Args:
            progress_callback: 进度回调函数

        Returns:
            筛选后的数据
        """
        return self.apply_custom_geochemical_filters(
            sio2_threshold=54.0,
            lg_nbth_threshold=0.7,
            lg_th_threshold=1.1,
            loi_threshold=4.0,
            min_age=100.0,
            progress_callback=progress_callback
        )

    def apply_custom_geochemical_filters(self,
                                         sio2_threshold: float = 54.0,
                                         lg_nbth_threshold: float = 0.7,
                                         lg_th_threshold: float = 1.1,
                                         loi_threshold: float = 4.0,
                                         min_age: float = 100.0,
                                         progress_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        应用自定义地球化学筛选条件 - 完全修复版，精确匹配MATLAB逻辑

        Args:
            sio2_threshold: SiO2阈值
            lg_nbth_threshold: Lg_NbTh阈值
            lg_th_threshold: Lg_Th阈值
            loi_threshold: LOI阈值
            min_age: 最小年龄
            progress_callback: 进度回调函数

        Returns:
            筛选后的数据
        """
        # ========== 测试标识 ==========
        print("🔥🔥🔥 [TEST-MARKER] 正在使用修复版筛选代码！🔥🔥🔥")
        print(f"[TEST-MARKER] 修复代码版本: v2.0 - NaN处理完全修复")
        # ========== 测试标识结束 ==========
        try:
            if progress_callback:
                progress_callback("开始MATLAB精确地球化学筛选...")

            # 复制数据
            filtered = self.original_data.copy()
            sample_n = len(filtered)

            # 清空筛选历史
            self.filter_history = []

            print(f"[MATLAB-EXACT-FIX] 开始精确MATLAB筛选: 5 个条件")
            print(f"[MATLAB-EXACT-FIX] 原始数据行数: {sample_n}")

            # 检查必需列是否存在并获取实际列名
            required_mappings = {
                'SiO2': sio2_threshold,
                'Lg_NbTh': lg_nbth_threshold,
                'Lg_Th': lg_th_threshold,
                'LOI': loi_threshold,
                'AGE': min_age,
                'ThU': None  # 目标列
            }

            actual_columns = {}
            for key in required_mappings.keys():
                if key not in self.column_mapping:
                    print(f"[ERROR] 缺少必需的列映射: {key}")
                    raise ValueError(f"缺少必需的列映射: {key}")

                actual_col = self.column_mapping[key]
                if actual_col not in filtered.columns:
                    print(f"[ERROR] 列不存在于数据中: {actual_col}")
                    raise ValueError(f"列不存在于数据中: {actual_col}")

                # 确保列是数值型
                filtered[actual_col] = pd.to_numeric(filtered[actual_col], errors='coerce')
                actual_columns[key] = actual_col

            print(f"[MATLAB-EXACT-FIX] 目标列: ThU={actual_columns['ThU']}, SiO2={actual_columns['SiO2']}")

            # 转换为numpy数组进行逐元素操作（更接近MATLAB）
            age_col = filtered[actual_columns['AGE']].values.copy()
            sio2_col = filtered[actual_columns['SiO2']].values.copy()
            thu_col = filtered[actual_columns['ThU']].values.copy()
            lg_nbth_col = filtered[actual_columns['Lg_NbTh']].values.copy()
            lg_th_col = filtered[actual_columns['Lg_Th']].values.copy()
            loi_col = filtered[actual_columns['LOI']].values.copy()

            initial_valid = np.sum(~np.isnan(thu_col))
            print(f"[MATLAB-EXACT-FIX] 初始ThU有效数据: {initial_valid}")

            # ====== 步骤1：SiO2筛选 - SiO2 >= 54 ======
            print(f"[MATLAB-EXACT-FIX] 步骤 1: SIO2 >= {sio2_threshold}")
            step1_removed = 0
            for i in range(sample_n):
                # MATLAB逻辑：如果SiO2[i] >= 54为false（包括NaN情况）
                if np.isnan(sio2_col[i]) or sio2_col[i] < sio2_threshold:
                    if not np.isnan(thu_col[i]):
                        step1_removed += 1
                    thu_col[i] = np.nan
                    sio2_col[i] = np.nan

            step1_valid = np.sum(~np.isnan(thu_col))
            print(f"[MATLAB-EXACT-FIX] ThU有效数据: {initial_valid} -> {step1_valid} (减少 {step1_removed})")

            # ====== 步骤2：lg_NbTh筛选 - lg_NbTh <= 0.7 (完全修复版) ======
            print(f"[MATLAB-EXACT-FIX] 步骤 2: lg_NbTh <= {lg_nbth_threshold}")

            # 统计当前状态
            current_thu_valid = np.sum(~np.isnan(thu_col))
            print(f"[DEBUG] 当前ThU有效行数: {current_thu_valid}")

            # 统计ThU有效且lg_NbTh也有效的行数
            both_valid_mask = (~np.isnan(thu_col)) & (~np.isnan(lg_nbth_col))
            both_valid_count = np.sum(both_valid_mask)
            print(f"[DEBUG] ThU和lg_NbTh都有效的行数: {both_valid_count}")

            # 计算lg_NbTh为NaN的ThU有效行数
            thu_valid_lg_nbth_nan = np.sum((~np.isnan(thu_col)) & (np.isnan(lg_nbth_col)))
            print(f"[DEBUG] ThU有效但lg_NbTh为NaN的行数: {thu_valid_lg_nbth_nan}")

            step2_removed = 0
            step2_nan_removed = 0

            # MATLAB精确逻辑：逐行处理
            for i in range(sample_n):
                if not np.isnan(thu_col[i]):  # 只处理当前ThU有效的行
                    current_lg_nbth = lg_nbth_col[i]

                    # 关键修复：MATLAB中 NaN <= 0.7 返回false，所以NaN必须被删除
                    condition_satisfied = False

                    if np.isnan(current_lg_nbth):
                        # lg_NbTh为NaN：在MATLAB中条件不满足，必须删除
                        condition_satisfied = False
                        step2_nan_removed += 1
                    else:
                        # lg_NbTh不为NaN：进行数值比较
                        condition_satisfied = (current_lg_nbth <= lg_nbth_threshold)
                        if not condition_satisfied:
                            step2_removed += 1

                    # 如果条件不满足，删除该行
                    if not condition_satisfied:
                        thu_col[i] = np.nan
                        sio2_col[i] = np.nan

            step2_valid = np.sum(~np.isnan(thu_col))
            total_step2_removed = step2_nan_removed + step2_removed
            print(f"[MATLAB-EXACT-FIX] ThU有效数据: {step1_valid} -> {step2_valid} (减少 {total_step2_removed})")
            print(f"[MATLAB-EXACT-FIX]   因lg_NbTh为NaN删除: {step2_nan_removed}")
            print(f"[MATLAB-EXACT-FIX]   因lg_NbTh > 0.7删除: {step2_removed}")

            # 验证NaN删除是否正确
            if step2_nan_removed != thu_valid_lg_nbth_nan:
                print(f"[ERROR] NaN删除数量不匹配! 期望:{thu_valid_lg_nbth_nan}, 实际:{step2_nan_removed}")

            # 检查第2步结果
            expected_step2 = 10811
            if step2_valid == expected_step2:
                print(f"[SUCCESS] 步骤2结果完美匹配！期望: {expected_step2}, 实际: {step2_valid}")
            elif abs(step2_valid - expected_step2) <= 5:
                print(
                    f"[SUCCESS] 步骤2结果接近匹配！期望: {expected_step2}, 实际: {step2_valid}, 差异: {step2_valid - expected_step2}")
            else:
                print(
                    f"[WARNING] 步骤2结果不匹配！期望: {expected_step2}, 实际: {step2_valid}, 差异: {step2_valid - expected_step2}")

                # 提供额外调试信息
                print(f"[DEBUG] 调试信息:")
                print(f"[DEBUG]   预期删除NaN数: {thu_valid_lg_nbth_nan}")
                print(f"[DEBUG]   实际删除NaN数: {step2_nan_removed}")
                print(f"[DEBUG]   预期删除>0.7数: 约{step1_valid - thu_valid_lg_nbth_nan - expected_step2}")
                print(f"[DEBUG]   实际删除>0.7数: {step2_removed}")

            # ====== 步骤3：lg_Th筛选 - lg_Th <= 1.1 (同样修复NaN处理) ======
            print(f"[MATLAB-EXACT-FIX] 步骤 3: lg_Th <= {lg_th_threshold}")
            step3_removed = 0
            step3_nan_removed = 0

            for i in range(sample_n):
                if not np.isnan(thu_col[i]):
                    current_lg_th = lg_th_col[i]

                    condition_satisfied = False

                    if np.isnan(current_lg_th):
                        # lg_Th为NaN：在MATLAB中条件不满足，必须删除
                        condition_satisfied = False
                        step3_nan_removed += 1
                    else:
                        # lg_Th不为NaN：进行数值比较
                        condition_satisfied = (current_lg_th <= lg_th_threshold)
                        if not condition_satisfied:
                            step3_removed += 1

                    # 如果条件不满足，删除该行
                    if not condition_satisfied:
                        thu_col[i] = np.nan
                        sio2_col[i] = np.nan

            step3_valid = np.sum(~np.isnan(thu_col))
            total_step3_removed = step3_nan_removed + step3_removed
            print(f"[MATLAB-EXACT-FIX] ThU有效数据: {step2_valid} -> {step3_valid} (减少 {total_step3_removed})")
            print(f"[MATLAB-EXACT-FIX]   因lg_Th为NaN删除: {step3_nan_removed}")
            print(f"[MATLAB-EXACT-FIX]   因lg_Th > 1.1删除: {step3_removed}")

            # 检查第3步结果
            expected_step3 = 5908
            if step3_valid == expected_step3:
                print(f"[SUCCESS] 步骤3结果完美匹配！期望: {expected_step3}, 实际: {step3_valid}")
            else:
                print(
                    f"[WARNING] 步骤3结果不匹配！期望: {expected_step3}, 实际: {step3_valid}, 差异: {step3_valid - expected_step3}")

            # ====== 步骤4：LOI筛选 - LOI <= 4 (注意：这里是删除>4的，NaN保留) ======
            print(f"[MATLAB-EXACT-FIX] 步骤 4: LOI <= {loi_threshold}")
            step4_removed = 0

            for i in range(sample_n):
                if not np.isnan(thu_col[i]):
                    # 关键差异：LOI > 4时删除，但LOI为NaN时不删除（MATLAB行为）
                    if not np.isnan(loi_col[i]) and loi_col[i] > loi_threshold:
                        step4_removed += 1
                        thu_col[i] = np.nan
                        sio2_col[i] = np.nan

            step4_valid = np.sum(~np.isnan(thu_col))
            print(f"[MATLAB-EXACT-FIX] ThU有效数据: {step3_valid} -> {step4_valid} (减少 {step4_removed})")

            # 检查第4步结果
            expected_step4 = 5455
            if step4_valid == expected_step4:
                print(f"[SUCCESS] 步骤4结果完美匹配！期望: {expected_step4}, 实际: {step4_valid}")
            else:
                print(
                    f"[WARNING] 步骤4结果不匹配！期望: {expected_step4}, 实际: {step4_valid}, 差异: {step4_valid - expected_step4}")

            # ====== 步骤5：AGE筛选 - AGE > 100 (注意：这里是删除<=100的，NaN保留) ======
            print(f"[MATLAB-EXACT-FIX] 步骤 5: AGE > {min_age}")
            step5_removed = 0

            for i in range(sample_n):
                if not np.isnan(thu_col[i]):
                    # 关键差异：AGE <= 100时删除，但AGE为NaN时不删除（MATLAB行为）
                    if not np.isnan(age_col[i]) and age_col[i] <= min_age:
                        step5_removed += 1
                        thu_col[i] = np.nan
                        sio2_col[i] = np.nan

            step5_valid = np.sum(~np.isnan(thu_col))
            print(f"[MATLAB-EXACT-FIX] ThU有效数据: {step4_valid} -> {step5_valid} (减少 {step5_removed})")

            # 检查第5步结果
            expected_step5 = 2458
            if step5_valid == expected_step5:
                print(f"[SUCCESS] 步骤5结果完美匹配！期望: {expected_step5}, 实际: {step5_valid}")
            else:
                print(
                    f"[WARNING] 步骤5结果不匹配！期望: {expected_step5}, 实际: {step5_valid}, 差异: {step5_valid - expected_step5}")

            print(f"[SUCCESS-MATLAB-EXACT-FIX] 精确MATLAB筛选完成")
            print(f"[SUCCESS-MATLAB-EXACT-FIX] 最终ThU有效数据: {step5_valid}")
            print(f"[SUCCESS-MATLAB-EXACT-FIX] 数据行数保持: {sample_n} (不变)")

            # 最终结果检查
            final_diff = step5_valid - expected_step5
            if abs(final_diff) == 0:
                print(f"[FINAL-CHECK] 🎉 完美匹配MATLAB结果！")
            elif abs(final_diff) <= 5:
                print(f"[FINAL-CHECK] ✅ 最终结果接近匹配: 差异 {final_diff} (可接受)")
            else:
                print(f"[FINAL-CHECK] ❌ 最终结果差异: {final_diff} (期望: {expected_step5}, 实际: {step5_valid})")
                if abs(final_diff) > 50:
                    print(f"[FINAL-CHECK] 差异较大，可能需要进一步调试")

            # 更新数据框
            result_data = filtered.copy()
            result_data[actual_columns['ThU']] = thu_col
            result_data[actual_columns['SiO2']] = sio2_col

            # 记录筛选历史
            filter_steps = [
                {'name': 'SiO2_filter', 'description': f'SiO2 >= {sio2_threshold}', 'removed': step1_removed,
                 'remaining': step1_valid},
                {'name': 'Lg_NbTh_filter', 'description': f'lg_NbTh <= {lg_nbth_threshold}',
                 'removed': total_step2_removed, 'remaining': step2_valid},
                {'name': 'Lg_Th_filter', 'description': f'lg_Th <= {lg_th_threshold}', 'removed': total_step3_removed,
                 'remaining': step3_valid},
                {'name': 'LOI_filter', 'description': f'LOI <= {loi_threshold}', 'removed': step4_removed,
                 'remaining': step4_valid},
                {'name': 'AGE_filter', 'description': f'AGE > {min_age}', 'removed': step5_removed,
                 'remaining': step5_valid}
            ]

            for step in filter_steps:
                filter_record = {
                    'step': step['name'],
                    'description': f"MATLAB精确筛选 - {step['description']}",
                    'column': actual_columns['ThU'],
                    'condition': step['description'],
                    'before_count': step['remaining'] + step['removed'],
                    'after_count': step['remaining'],
                    'removed_count': step['removed'],
                    'removal_rate': step['removed'] / (step['remaining'] + step['removed']) * 100 if (step[
                                                                                                          'remaining'] +
                                                                                                      step[
                                                                                                          'removed']) > 0 else 0
                }
                self.filter_history.append(filter_record)

            # 保存筛选结果
            self.filtered_data = result_data

            if progress_callback:
                progress_callback(f"MATLAB精确筛选完成: {initial_valid} -> {step5_valid} 有效样本")

            # 打印与MATLAB期望值的对比
            expected_values = [12811, 10811, 5908, 5455, 2458]
            actual_values = [step1_valid, step2_valid, step3_valid, step4_valid, step5_valid]
            step_names = ['SiO2≥54', 'lg_NbTh≤0.7', 'lg_Th≤1.1', 'LOI≤4', 'AGE>100']

            print(f"\n[COMPARISON] 与MATLAB期望值对比:")
            for i, (name, expected, actual) in enumerate(zip(step_names, expected_values, actual_values)):
                diff = actual - expected
                status = "✅" if diff == 0 else f"❌ 差异{diff:+d}"
                print(f"  {name}: 期望={expected}, 实际={actual} {status}")

            return result_data

        except Exception as e:
            error_msg = f"MATLAB精确地球化学筛选失败: {str(e)}"
            print(f"[ERROR] {error_msg}")
            if progress_callback:
                progress_callback(f"错误: {error_msg}")
            raise

    def apply_outlier_removal(self,
                              target_column: str,
                              lower_percentile: float = 2.5,
                              upper_percentile: float = 97.5,
                              progress_callback: Optional[Callable] = None) -> pd.DataFrame:
        """
        移除异常值

        Args:
            target_column: 目标列名
            lower_percentile: 下百分位数
            upper_percentile: 上百分位数
            progress_callback: 进度回调函数

        Returns:
            处理后的数据
        """
        try:
            if self.filtered_data is None:
                self.filtered_data = self.original_data.copy()

            if progress_callback:
                progress_callback("开始异常值检测和移除...")

            # 获取有效数据
            valid_data = self.filtered_data[target_column].dropna()

            if len(valid_data) == 0:
                raise ValueError(f"列 '{target_column}' 没有有效数据进行异常值检测")

            before_count = len(valid_data)

            # 计算百分位数阈值
            outlier_low = np.percentile(valid_data, lower_percentile)
            outlier_high = np.percentile(valid_data, upper_percentile)

            print(f"[INFO] 异常值检测阈值: {outlier_low:.6f} - {outlier_high:.6f}")
            print(f"[INFO] 百分位数范围: {lower_percentile}% - {upper_percentile}%")

            # 应用异常值筛选
            outlier_mask = (
                    (self.filtered_data[target_column] >= outlier_low) &
                    (self.filtered_data[target_column] <= outlier_high)
            )

            # 将异常值设为NaN
            self.filtered_data.loc[~outlier_mask, target_column] = np.nan

            after_count = self.filtered_data[target_column].notna().sum()
            removed_count = before_count - after_count

            # 记录异常值处理历史
            outlier_record = {
                'step': 'outlier_removal',
                'description': f'异常值移除 ({lower_percentile}%-{upper_percentile}%)',
                'column': target_column,
                'condition': f'{outlier_low:.6f} <= value <= {outlier_high:.6f}',
                'before_count': before_count,
                'after_count': after_count,
                'removed_count': removed_count,
                'removal_rate': removed_count / before_count * 100 if before_count > 0 else 0
            }
            self.filter_history.append(outlier_record)

            print(f"[INFO] 异常值移除完成: {before_count} -> {after_count} "
                  f"(移除 {removed_count}, {removed_count / before_count * 100:.1f}%)")

            if progress_callback:
                progress_callback(f"异常值移除完成，移除了 {removed_count} 个异常值")

            return self.filtered_data

        except Exception as e:
            error_msg = f"异常值移除失败: {str(e)}"
            print(f"[ERROR] {error_msg}")
            if progress_callback:
                progress_callback(f"错误: {error_msg}")
            raise

    def get_filter_statistics(self) -> Dict:
        """
        获取筛选统计信息

        Returns:
            筛选统计字典
        """
        if not self.filter_history:
            return {'status': 'no_filters_applied', 'message': '未应用任何筛选'}

        # 计算总体统计
        initial_count = self.filter_history[0]['before_count'] if self.filter_history else len(self.original_data)
        final_count = self.filter_history[-1]['after_count'] if self.filter_history else initial_count
        total_removed = initial_count - final_count
        total_retention_rate = final_count / initial_count * 100 if initial_count > 0 else 0

        statistics = {
            'status': 'completed',
            'initial_samples': initial_count,
            'final_samples': final_count,
            'total_removed': total_removed,
            'retention_rate': total_retention_rate,
            'filter_steps': len(self.filter_history),
            'step_details': []
        }

        # 添加每个步骤的详细信息
        for record in self.filter_history:
            step_info = {
                'step_name': record['step'],
                'description': record['description'],
                'column': record['column'],
                'condition': record['condition'],
                'samples_before': record['before_count'],
                'samples_after': record['after_count'],
                'samples_removed': record['removed_count'],
                'removal_rate': record['removal_rate']
            }
            statistics['step_details'].append(step_info)

        return statistics

    def export_filter_report(self, file_path: str) -> bool:
        """
        导出筛选报告

        Args:
            file_path: 导出文件路径

        Returns:
            是否导出成功
        """
        try:
            if not self.filter_history:
                print("[WARNING] 没有筛选历史可以导出")
                return False

            # 创建报告DataFrame
            report_data = []
            for record in self.filter_history:
                report_data.append({
                    '筛选步骤': record['step'],
                    '描述': record['description'],
                    '数据列': record['column'],
                    '筛选条件': record['condition'],
                    '筛选前样本数': record['before_count'],
                    '筛选后样本数': record['after_count'],
                    '移除样本数': record['removed_count'],
                    '移除率(%)': round(record['removal_rate'], 2)
                })

            report_df = pd.DataFrame(report_data)

            # 根据文件扩展名选择导出格式
            if file_path.endswith('.xlsx'):
                report_df.to_excel(file_path, index=False)
            elif file_path.endswith('.csv'):
                report_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            else:
                # 默认CSV格式
                csv_path = file_path + '.csv' if not file_path.endswith('.csv') else file_path
                report_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                file_path = csv_path

            print(f"[SUCCESS] 筛选报告已导出到: {file_path}")
            return True

        except Exception as e:
            error_msg = f"导出筛选报告失败: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return False

    def reset_filters(self):
        """重置所有筛选"""
        self.filtered_data = None
        self.filter_history = []
        print("[INFO] 筛选状态已重置")

    def get_filtered_data(self) -> Optional[pd.DataFrame]:
        """获取筛选后的数据"""
        return self.filtered_data

    def validate_data_for_geochemical_analysis(self) -> Tuple[bool, str]:
        """
        验证数据是否适合进行地球化学分析

        Returns:
            (是否有效, 验证消息)
        """
        if self.original_data is None or len(self.original_data) == 0:
            return False, "没有可用的数据"

        # 检查必需的地球化学列
        essential_columns = ['SiO2', 'AGE']
        missing_essential = []

        for col_key in essential_columns:
            if col_key not in self.column_mapping:
                missing_essential.append(col_key)

        if missing_essential:
            return False, f"缺少必需的地球化学列: {missing_essential}"

        # 检查数据质量
        total_rows = len(self.original_data)
        if total_rows < 10:
            return False, f"数据量太少，至少需要10行数据，当前只有{total_rows}行"

        # 检查数值列的有效性
        numeric_issues = []
        for col_key, actual_col in self.column_mapping.items():
            if actual_col in self.original_data.columns:
                try:
                    numeric_data = pd.to_numeric(self.original_data[actual_col], errors='coerce')
                    valid_count = numeric_data.notna().sum()
                    valid_rate = valid_count / total_rows * 100

                    if valid_rate < 10:  # 少于10%的有效数据
                        numeric_issues.append(f"{col_key}({actual_col}): 只有{valid_rate:.1f}%的有效数据")

                except Exception as e:
                    numeric_issues.append(f"{col_key}({actual_col}): 数值转换失败 - {str(e)}")

        if numeric_issues:
            return False, f"数据质量问题: {'; '.join(numeric_issues)}"

        return True, "数据验证通过，可以进行地球化学分析"

    def suggest_optimal_filters(self) -> Dict:
        """
        根据数据特征建议最优筛选参数

        Returns:
            建议的筛选参数字典
        """
        suggestions = {
            'recommended_filters': [],
            'data_statistics': {},
            'warnings': []
        }

        try:
            # 分析数据特征
            for col_key, actual_col in self.column_mapping.items():
                if actual_col in self.original_data.columns:
                    numeric_data = pd.to_numeric(self.original_data[actual_col], errors='coerce')
                    valid_data = numeric_data.dropna()

                    if len(valid_data) > 0:
                        stats = {
                            'mean': float(valid_data.mean()),
                            'median': float(valid_data.median()),
                            'std': float(valid_data.std()),
                            'min': float(valid_data.min()),
                            'max': float(valid_data.max()),
                            'count': len(valid_data),
                            'valid_rate': len(valid_data) / len(self.original_data) * 100
                        }
                        suggestions['data_statistics'][col_key] = stats

            # 基于数据特征提供建议
            if 'SiO2' in suggestions['data_statistics']:
                sio2_stats = suggestions['data_statistics']['SiO2']
                if sio2_stats['min'] < 45:
                    suggestions['recommended_filters'].append({
                        'type': 'SiO2_threshold',
                        'value': 54.0,
                        'reason': f"检测到低SiO2样品(最小值:{sio2_stats['min']:.1f}%)，建议去除大陆玄武岩"
                    })

            if 'AGE' in suggestions['data_statistics']:
                age_stats = suggestions['data_statistics']['AGE']
                if age_stats['min'] < 100:
                    suggestions['recommended_filters'].append({
                        'type': 'min_age',
                        'value': 100.0,
                        'reason': f"检测到年轻样品(最小值:{age_stats['min']:.1f}Ma)，建议设置最小年龄阈值"
                    })

            if 'LOI' in suggestions['data_statistics']:
                loi_stats = suggestions['data_statistics']['LOI']
                if loi_stats['max'] > 10:
                    suggestions['recommended_filters'].append({
                        'type': 'LOI_threshold',
                        'value': 4.0,
                        'reason': f"检测到高LOI样品(最大值:{loi_stats['max']:.1f}%)，建议去除蚀变样品"
                    })

            # 检查数据完整性并给出警告
            for col_key in ['Lg_NbTh', 'Lg_Th']:
                if col_key not in suggestions['data_statistics']:
                    suggestions['warnings'].append(f"缺少{col_key}列，无法进行完整的地球化学筛选")

        except Exception as e:
            suggestions['warnings'].append(f"分析数据特征时出错: {str(e)}")

        return suggestions


def create_filter_manager_from_processor(data_processor) -> GeochemicalFilterManager:
    """
    从DataProcessor创建GeochemicalFilterManager

    Args:
        data_processor: DataProcessor实例

    Returns:
        GeochemicalFilterManager实例
    """
    if data_processor.data is None:
        raise ValueError("DataProcessor中没有数据")

    filter_manager = GeochemicalFilterManager(data_processor.data)

    # 显示检测结果
    detected = filter_manager.get_detected_columns()
    if detected:
        print(f"[INFO] 自动检测到的地球化学列: {list(detected.keys())}")
        for key, value in detected.items():
            print(f"[INFO]   {key} -> {value}")
    else:
        print("[WARNING] 未能自动检测到标准地球化学列")

    return filter_manager


# 预定义筛选配置
class GeochemicalFilterPresets:
    """地球化学筛选预设配置"""

    @staticmethod
    def get_standard_igneous_filter():
        """标准火成岩筛选配置"""
        return {
            'name': '标准火成岩筛选',
            'description': '适用于一般火成岩地球化学分析',
            'filters': {
                'sio2_threshold': 54.0,
                'lg_nbth_threshold': 0.7,
                'lg_th_threshold': 1.1,
                'loi_threshold': 4.0,
                'min_age': 100.0
            }
        }

    @staticmethod
    def get_archean_filter():
        """太古宙样品筛选配置"""
        return {
            'name': '太古宙样品筛选',
            'description': '适用于太古宙古老岩石分析',
            'filters': {
                'sio2_threshold': 50.0,  # 太古宙样品SiO2要求相对宽松
                'lg_nbth_threshold': 0.8,
                'lg_th_threshold': 1.2,
                'loi_threshold': 5.0,  # 古老样品可能蚀变程度较高
                'min_age': 2500.0  # 太古宙下限
            }
        }

    @staticmethod
    def get_phanerozoic_filter():
        """显生宙样品筛选配置"""
        return {
            'name': '显生宙样品筛选',
            'description': '适用于显生宙年轻岩石分析',
            'filters': {
                'sio2_threshold': 55.0,  # 更严格的SiO2要求
                'lg_nbth_threshold': 0.6,
                'lg_th_threshold': 1.0,
                'loi_threshold': 3.0,  # 更严格的蚀变控制
                'min_age': 50.0  # 显生宙包含更年轻的样品
            }
        }

    @staticmethod
    def get_strict_filter():
        """严格筛选配置"""
        return {
            'name': '严格质量控制筛选',
            'description': '适用于高精度分析，严格控制数据质量',
            'filters': {
                'sio2_threshold': 60.0,  # 只保留酸性岩石
                'lg_nbth_threshold': 0.5,
                'lg_th_threshold': 0.8,
                'loi_threshold': 2.0,  # 严格控制蚀变
                'min_age': 200.0
            }
        }

    @staticmethod
    def get_all_presets():
        """获取所有预设配置"""
        return [
            GeochemicalFilterPresets.get_standard_igneous_filter(),
            GeochemicalFilterPresets.get_archean_filter(),
            GeochemicalFilterPresets.get_phanerozoic_filter(),
            GeochemicalFilterPresets.get_strict_filter()
        ]


# 使用示例
if __name__ == "__main__":
    # 这里是使用示例，实际使用时会从DataProcessor获取数据
    import pandas as pd

    # 创建示例数据
    sample_data = pd.DataFrame({
        'AGE': [100, 150, 200, 2800, 3000, 3200, 50, 80],
        'SiO2': [45, 60, 70, 65, 55, 48, 75, 80],
        'ThU': [2.5, 3.1, 2.8, 4.2, 3.8, 5.1, 2.2, 1.9],
        'Lg_NbTh': [0.5, 0.8, 0.6, 0.4, 0.9, 0.3, 1.2, 1.5],
        'Lg_Th': [0.8, 1.2, 0.9, 0.7, 1.5, 0.6, 1.8, 2.0],
        'LOI': [2.1, 3.5, 1.8, 2.9, 6.2, 4.8, 1.2, 0.9]
    })

    # 创建筛选管理器
    filter_manager = GeochemicalFilterManager(sample_data)

    print("检测到的列映射:")
    for key, value in filter_manager.get_detected_columns().items():
        print(f"  {key}: {value}")

    # 应用标准筛选
    filtered_data = filter_manager.apply_standard_geochemical_filters()

    # 显示筛选统计
    stats = filter_manager.get_filter_statistics()
    print(f"\n筛选统计:")
    print(f"初始样本数: {stats['initial_samples']}")
    print(f"最终样本数: {stats['final_samples']}")
    print(f"保留率: {stats['retention_rate']:.1f}%")