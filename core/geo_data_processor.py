# -*- coding: utf-8 -*-
"""
修复版地理数据处理器 - 兼容原版和增强版，新增Location聚合支持
完全替换你的 core/geo_data_processor.py 文件
"""

import pandas as pd
import numpy as np
import threading
from typing import Dict, Any, Callable, Optional
import math


class SimpleGeoDataProcessor:
    """原版兼容地理数据处理器 - 保持原接口"""

    def __init__(self):
        self.debug_mode = True

    def perform_aggregation(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行地理聚合的主入口函数 - 原版兼容

        Args:
            data: 输入数据DataFrame
            params: 聚合参数字典，包含：
                - latitude_column: 纬度列名
                - longitude_column: 经度列名
                - age_column: 年龄列名
                - coord_aggregation: 经纬度聚合方式 ('divide_10', 'divide_100', 'no_change')
                - age_aggregation: 年龄聚合方式 (统一使用10Ma聚合)

        Returns:
            包含聚合结果的字典
        """
        try:
            print(f"[DEBUG] Starting original compatible geographic aggregation, parameters: {params}")

            # 验证参数
            self._validate_parameters(params)

            # 验证数据
            clean_data = self._validate_and_clean_data(data, params)

            # 执行聚合
            aggregated_data, statistics = self._execute_simple_aggregation(clean_data, params)

            # 构造返回结果
            result = {
                'aggregated_data': aggregated_data,
                'aggregation_method': 'simple_geographic_rounding',
                'group_column': self._get_group_description(params),
                'target_columns': self._get_element_columns(clean_data, params),
                'aggregation_functions': ['mean'],
                'statistics': statistics
            }

            print(
                f"[SUCCESS] geographic aggregation completed: {statistics['original_count']} -> {statistics['aggregated_count']} ")
            return result

        except Exception as e:
            print(f"[ERROR] geographic aggregation failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _validate_parameters(self, params: Dict[str, Any]) -> None:
        """验证输入参数"""
        required_keys = ['latitude_column', 'longitude_column', 'age_column',
                         'coord_aggregation', 'age_aggregation']

        for key in required_keys:
            if key not in params:
                raise ValueError(f"Missing required parameter: {key}")

        valid_agg_types = ['divide_10', 'divide_100', 'no_change', 'custom']
        if params['coord_aggregation'] not in valid_agg_types:
            raise ValueError(f"Invalid coordinate aggregation method: {params['coord_aggregation']}")
        if params['age_aggregation'] not in valid_agg_types:
            raise ValueError(f"Invalid age aggregation method: {params['age_aggregation']}")

    def _validate_and_clean_data(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """验证和清理数据"""
        print("[VALIDATION] 验证数据...")

        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']

        # 检查列是否存在
        missing_cols = []
        for col in [lat_col, lon_col, age_col]:
            if col not in data.columns:
                missing_cols.append(col)

        if missing_cols:
            raise ValueError(f"missing_cols: {missing_cols}")

        # 转换为数值类型并验证
        clean_data = data.copy()

        # 转换并验证纬度
        lat_data = pd.to_numeric(clean_data[lat_col], errors='coerce')
        valid_lat = (lat_data >= -90) & (lat_data <= 90) & lat_data.notna()

        # 转换并验证经度
        lon_data = pd.to_numeric(clean_data[lon_col], errors='coerce')
        valid_lon = (lon_data >= -180) & (lon_data <= 180) & lon_data.notna()

        # 转换并验证年龄
        age_data = pd.to_numeric(clean_data[age_col], errors='coerce')
        valid_age = age_data.notna() & (age_data >= 0)

        # 综合有效性检查
        valid_mask = valid_lat & valid_lon & valid_age

        # 排除(0,0)坐标点（通常是无效数据）
        not_zero_coords = ~((lat_data == 0) & (lon_data == 0))
        valid_mask = valid_mask & not_zero_coords

        if not valid_mask.any():
            raise ValueError("No valid coordinate and age data")

        # 应用清理
        clean_data = clean_data[valid_mask].copy()
        clean_data[lat_col] = lat_data[valid_mask]
        clean_data[lon_col] = lon_data[valid_mask]
        clean_data[age_col] = age_data[valid_mask]

        invalid_count = len(data) - len(clean_data)
        if invalid_count > 0:
            print(f"[WARNING] Removed  {invalid_count} invalid data points")

        print(f"[VALIDATION] Valid data: {len(clean_data)} rows")
        return clean_data

    def _execute_simple_aggregation(self, data: pd.DataFrame, params: Dict[str, Any]) -> tuple:
        """执行简单聚合"""
        print("[AGGREGATION] Starting original compatible geographic aggregation...")

        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']
        coord_agg = params['coord_aggregation']
        age_agg = 'divide_10'  # 强制使用10Ma聚合

        original_count = len(data)

        # 应用聚合规则创建聚合键
        working_data = data.copy()

        working_data['lat_agg'] = working_data[lat_col].apply(
            lambda x: self._apply_aggregation_rule(x, coord_agg, 'coordinate')
        )
        working_data['lon_agg'] = working_data[lon_col].apply(
            lambda x: self._apply_aggregation_rule(x, coord_agg, 'coordinate')
        )
        working_data['age_agg'] = working_data[age_col].apply(
            lambda x: self._apply_aggregation_rule(x, age_agg, 'age')
        )

        # 创建聚合键
        working_data['agg_key'] = (
                working_data['lat_agg'].astype(str) + "_" +
                working_data['lon_agg'].astype(str) + "_" +
                working_data['age_agg'].astype(str)
        )

        # 获取要聚合的元素列
        element_columns = self._get_element_columns(working_data, params)

        # 按聚合键分组并执行聚合计算
        grouped = working_data.groupby('agg_key')
        aggregated_rows = []

        for agg_key, group in grouped:
            row = {
                'agg_key': agg_key,
                lat_col: group['lat_agg'].iloc[0],
                lon_col: group['lon_agg'].iloc[0],
                age_col: group['age_agg'].iloc[0],
                'sample_count': len(group)
            }

            # 计算元素列的算术平均值
            for col in element_columns:
                if col in group.columns:
                    valid_values = group[col].dropna()
                    if len(valid_values) > 0:
                        row[col] = valid_values.mean()
                    else:
                        row[col] = np.nan

            # 复制重要的非数值列
            important_text_columns = ['Location', 'Rock type', 'Continent', 'Country', 'Reference', 'SAMPLE_ID']
            for col in working_data.columns:
                if (col in important_text_columns and
                        col not in row and
                        not pd.api.types.is_numeric_dtype(working_data[col])):
                    row[col] = group[col].iloc[0]

            aggregated_rows.append(row)

        # 创建结果DataFrame
        result_df = pd.DataFrame(aggregated_rows)
        result_df = self._clean_result_columns(result_df, params)

        aggregated_count = len(result_df)

        # 计算统计信息
        statistics = self._calculate_statistics(
            original_count, aggregated_count, result_df, params
        )

        print(f"[AGGREGATION] aggregation completed: {len(result_df)} aggregation groups")
        return result_df, statistics

    def _apply_aggregation_rule(self, value: float, agg_type: str, data_type: str = 'coordinate') -> float:
        """应用聚合规则"""
        if pd.isna(value):
            return np.nan

        try:
            if agg_type == "divide_10":
                if data_type == 'age':
                    return math.ceil(value / 10) * 10  # 年龄向上取整
                else:
                    return round(value / 10) * 10  # 坐标四舍五入
            elif agg_type == "divide_100":
                return round(value / 100) * 100
            else:  # no_change or custom
                return float(value)
        except (ValueError, OverflowError):
            print(f"[WARNING] Custom precision rule application failed, value: {value}, precision: {agg_type}")
            return np.nan

    def _get_element_columns(self, data: pd.DataFrame, params: Dict[str, Any]) -> list:
        """获取要聚合的元素列"""
        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']

        numeric_columns = list(data.select_dtypes(include=[np.number]).columns)
        exclude_columns = {lat_col, lon_col, age_col, 'lat_agg', 'lon_agg', 'age_agg'}
        element_columns = [col for col in numeric_columns if col not in exclude_columns]

        print(f"[DEBUG] Found {len(element_columns)} element columns for aggregation")
        return element_columns

    def _get_group_description(self, params: Dict[str, Any]) -> str:
        """获取分组描述"""
        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']
        coord_agg = params['coord_aggregation']

        agg_desc = {
            'divide_10': '÷10向上取整×10',
            'divide_100': '÷100取整×100',
            'no_change': '不变'
        }

        coord_desc = agg_desc.get(coord_agg, coord_agg)
        age_desc = '÷10向上取整×10'  # 年龄统一

        return f"地理聚合({lat_col}[{coord_desc}], {lon_col}[{coord_desc}], {age_col}[{age_desc}])"

    def _calculate_statistics(self, original_count: int, aggregated_count: int,
                              result_df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算统计信息"""
        agg_descriptions = {
            'divide_10': '除以10向上取整再乘10',
            'divide_100': '除以100取整再乘100',
            'no_change': '保持原值'
        }

        coord_desc = agg_descriptions.get(params['coord_aggregation'], params['coord_aggregation'])
        age_desc = '除以10向上取整再乘10 (10Ma单位)'

        statistics = {
            'original_count': original_count,
            'aggregated_count': aggregated_count,
            'compression_ratio': (original_count - aggregated_count) / original_count if original_count > 0 else 0,
            'aggregation_ratio': aggregated_count / original_count if original_count > 0 else 0,
            'method': 'simple_geographic_rounding_fixed',
            'parameters': {
                'coord_aggregation': params['coord_aggregation'],
                'age_aggregation': 'divide_10_ceil',
                'coord_description': coord_desc,
                'age_description': age_desc
            },
            'avg_samples_per_group': result_df['sample_count'].mean() if len(result_df) > 0 else 0,
            'max_samples_per_group': result_df['sample_count'].max() if len(result_df) > 0 else 0,
            'min_samples_per_group': result_df['sample_count'].min() if len(result_df) > 0 else 0,
            'unique_groups': aggregated_count,
            'element_columns_processed': self._get_element_columns(result_df, params)
        }

        return statistics

    def _clean_result_columns(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        修复版：清理结果DataFrame，确保正确的列顺序
        地理聚合数据的标准列顺序：基本信息 -> 坐标 -> 聚合信息 -> 主量元素 -> 微量元素 -> 其他信息
        """
        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']

        print(f"[DEBUG] 原始列数: {len(df.columns)}")
        print(f"[DEBUG] 坐标列: {lat_col}, {lon_col}, {age_col}")

        # 获取所有数值列（排除特殊列）
        excluded_cols = {
            age_col, lat_col, lon_col, 'Location', 'agg_key', 'sample_count',
            'Rock type', 'Continent', 'Country', 'Reference', 'SAMPLE_ID',
            'lat_agg', 'lon_agg', 'age_agg', 'error'
        }

        element_columns = []
        for col in df.columns:
            if (pd.api.types.is_numeric_dtype(df[col]) and
                    col not in excluded_cols and
                    not col.endswith('_std') and
                    not col.startswith('original_')):
                element_columns.append(col)

        print(f"[DEBUG] 识别到 {len(element_columns)} 个元素列")

        # 构建标准的列顺序
        final_columns = []

        # 1. 年龄列（最重要的基础信息）
        if age_col in df.columns:
            final_columns.append(age_col)

        # 2. 坐标列（紧跟年龄）
        if lat_col in df.columns:
            final_columns.append(lat_col)
        if lon_col in df.columns:
            final_columns.append(lon_col)

        # 3. 位置信息
        if 'Location' in df.columns:
            final_columns.append('Location')

        # 4. 聚合关键信息
        for col in ['agg_key', 'sample_count']:
            if col in df.columns:
                final_columns.append(col)

        # 5. 主量元素（按标准顺序）
        major_elements_order = [
            'SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'Fe2O3T', 'FeO', 'FeOT',
            'MnO', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5'
        ]

        for element in major_elements_order:
            # 处理带空格的列名
            for col in element_columns:
                clean_col = col.strip()
                if clean_col == element or col == element:
                    final_columns.append(col)
                    if col in element_columns:
                        element_columns.remove(col)
                    break

        # 6. 重要的微量元素
        important_trace_elements = [
            'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
            'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Yb', 'Lu', 'Th', 'U'
        ]

        for element in important_trace_elements:
            for col in element_columns[:]:  # 使用切片避免修改迭代中的列表
                clean_col = col.strip()
                if clean_col == element or col == element:
                    final_columns.append(col)
                    element_columns.remove(col)
                    break

        # 7. 其他数值列（按字母顺序）
        remaining_numeric = sorted(element_columns)
        final_columns.extend(remaining_numeric)

        # 8. 重要的非数值列
        important_info_columns = ['Rock type', 'Continent', 'Country']
        for col in important_info_columns:
            if col in df.columns and col not in final_columns:
                final_columns.append(col)

        # 9. 其他剩余列
        for col in df.columns:
            if col not in final_columns:
                final_columns.append(col)

        # 去重并只保留存在的列
        final_columns = list(dict.fromkeys(final_columns))
        existing_columns = [col for col in final_columns if col in df.columns]

        print(f"[DEBUG] Final column order first 10: {existing_columns[:10]}")
        print(f"[DEBUG] Column count cleaning: {len(df.columns)} -> {len(existing_columns)}")

        return df[existing_columns]


class EnhancedGeoDataProcessor:
    """增强版地理数据处理器 - 支持自定义精度聚合和Location聚合"""

    def __init__(self):
        self.debug_mode = True

    def perform_custom_aggregation(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行自定义精度地理聚合的主入口函数

        Args:
            data: 输入数据DataFrame
            params: 聚合参数字典，包含：
                - latitude_column: 纬度列名
                - longitude_column: 经度列名
                - age_column: 年龄列名
                - coord_precision: 经纬度精度 (度)
                - age_precision: 年龄精度 (Ma)
                - age_strategy: 年龄聚合策略 ('round_up', 'round_down', 'round_nearest')

        Returns:
            包含聚合结果的字典
        """
        try:
            print(f"[DEBUG]  {params}")

            # 验证参数
            self._validate_custom_parameters(params)

            # 验证数据
            clean_data = self._validate_and_clean_data(data, params)

            # 执行自定义聚合
            aggregated_data, statistics = self._execute_custom_aggregation(clean_data, params)

            # 构造返回结果
            result = {
                'aggregated_data': aggregated_data,
                'aggregation_method': 'custom_precision_geographic',
                'group_column': self._get_custom_group_description(params),
                'target_columns': self._get_element_columns(clean_data, params),
                'aggregation_functions': ['mean'],
                'statistics': statistics
            }

            print(
                f"[SUCCESS]  {statistics['original_count']} -> {statistics['aggregated_count']} 点")
            return result

        except Exception as e:
            print(f"[ERROR]  {e}")
            import traceback
            traceback.print_exc()
            raise

    def perform_location_aggregation(self, data: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行基于Location的地理聚合

        Args:
            data: 输入数据DataFrame
            params: 聚合参数字典，包含：
                - location_column: Location列名
                - age_column: 年龄列名
                - age_precision: 年龄精度 (Ma)
                - age_strategy: 年龄聚合策略 ('round_up', 'round_down', 'round_nearest')

        Returns:
            包含聚合结果的字典
        """
        try:
            print(f"[DEBUG] STARTING Location，: {params}")

            # 验证参数
            self._validate_location_parameters(params)

            # 验证数据
            clean_data = self._validate_and_clean_location_data(data, params)

            # 执行Location聚合
            aggregated_data, statistics = self._execute_location_aggregation(clean_data, params)

            # 构造返回结果
            result = {
                'aggregated_data': aggregated_data,
                'aggregation_method': 'location_based_geographic',
                'group_column': self._get_location_group_description(params),
                'target_columns': self._get_element_columns_for_location(clean_data, params),
                'aggregation_functions': ['mean'],
                'statistics': statistics
            }

            print(f"[SUCCESS] Location SUCCESS: {statistics['original_count']} -> {statistics['aggregated_count']} ")
            return result

        except Exception as e:
            print(f"[ERROR] Location ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _validate_custom_parameters(self, params: Dict[str, Any]) -> None:
        """验证自定义聚合参数"""
        required_keys = ['latitude_column', 'longitude_column', 'age_column',
                         'coord_precision', 'age_precision', 'age_strategy']

        for key in required_keys:
            if key not in params:
                raise ValueError(f"MISSING PARAMS: {key}")

        if params['coord_precision'] <= 0:
            raise ValueError(f"Coordinate precision must be greater than 0: {params['coord_precision']}")
        if params['age_precision'] <= 0:
            raise ValueError(f"Age precision must be greater than 0: {params['age_precision']}")

        valid_strategies = ['round_up', 'round_down', 'round_nearest']
        if params['age_strategy'] not in valid_strategies:
            raise ValueError(f"Invalid age aggregation strategy: {params['age_strategy']}")

    def _validate_location_parameters(self, params: Dict[str, Any]) -> None:
        """验证Location聚合参数"""
        required_keys = ['location_column', 'age_column', 'age_precision', 'age_strategy']

        for key in required_keys:
            if key not in params:
                raise ValueError(f"Missing required parameter: {key}")

        if params['age_precision'] <= 0:
            raise ValueError(f"Age precision must be greater than 0: {params['age_precision']}")

        valid_strategies = ['round_up', 'round_down', 'round_nearest']
        if params['age_strategy'] not in valid_strategies:
            raise ValueError(f"Invalid age aggregation strategy: {params['age_strategy']}")

    def _validate_and_clean_data(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """验证和清理数据"""
        print("[VALIDATION] Validating enhanced data...")

        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']

        # 检查列是否存在
        missing_cols = []
        for col in [lat_col, lon_col, age_col]:
            if col not in data.columns:
                missing_cols.append(col)

        if missing_cols:
            raise ValueError(f"missing_cols: {missing_cols}")

        # 转换为数值类型并验证
        clean_data = data.copy()

        lat_data = pd.to_numeric(clean_data[lat_col], errors='coerce')
        valid_lat = (lat_data >= -90) & (lat_data <= 90) & lat_data.notna()

        lon_data = pd.to_numeric(clean_data[lon_col], errors='coerce')
        valid_lon = (lon_data >= -180) & (lon_data <= 180) & lon_data.notna()

        age_data = pd.to_numeric(clean_data[age_col], errors='coerce')
        valid_age = age_data.notna() & (age_data >= 0)

        valid_mask = valid_lat & valid_lon & valid_age
        not_zero_coords = ~((lat_data == 0) & (lon_data == 0))
        valid_mask = valid_mask & not_zero_coords

        if not valid_mask.any():
            raise ValueError("No valid coordinate and age data")

        clean_data = clean_data[valid_mask].copy()
        clean_data[lat_col] = lat_data[valid_mask]
        clean_data[lon_col] = lon_data[valid_mask]
        clean_data[age_col] = age_data[valid_mask]

        invalid_count = len(data) - len(clean_data)
        if invalid_count > 0:
            print(f"[WARNING] Removed {invalid_count} invalid data points")

        print(f"[VALIDATION] Valid data: {len(clean_data)} rows")
        return clean_data

    def _validate_and_clean_location_data(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """验证和清理Location聚合数据"""
        print("[VALIDATION] Validating Location aggregation data...")

        location_col = params['location_column']
        age_col = params['age_column']

        # 检查列是否存在
        missing_cols = []
        for col in [location_col, age_col]:
            if col not in data.columns:
                missing_cols.append(col)

        if missing_cols:
            raise ValueError(f"missing_cols: {missing_cols}")

        # 转换为数值类型并验证
        clean_data = data.copy()

        # 验证Location列（允许文本数据，但不能为空）
        location_data = clean_data[location_col].astype(str).str.strip()
        valid_location = (location_data != '') & (location_data != 'nan') & location_data.notna()

        # 验证年龄列
        age_data = pd.to_numeric(clean_data[age_col], errors='coerce')
        valid_age = age_data.notna() & (age_data >= 0)

        valid_mask = valid_location & valid_age

        if not valid_mask.any():
            raise ValueError("No valid Location and age data")

        clean_data = clean_data[valid_mask].copy()
        clean_data[location_col] = location_data[valid_mask]
        clean_data[age_col] = age_data[valid_mask]

        invalid_count = len(data) - len(clean_data)
        if invalid_count > 0:
            print(f"[WARNING] Removed {invalid_count} invalid data points")

        # 统计Location信息
        unique_locations = clean_data[location_col].nunique()
        print(f"[INFO] Detected {unique_locations} different Locations")

        print(f"[VALIDATION] Valid data: {len(clean_data)} rows")
        return clean_data

    def _execute_custom_aggregation(self, data: pd.DataFrame, params: Dict[str, Any]) -> tuple:
        """执行自定义精度聚合"""
        print("[AGGREGATION] Starting enhanced geographic aggregation...")

        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']
        coord_precision = params['coord_precision']
        age_precision = params['age_precision']
        age_strategy = params['age_strategy']

        original_count = len(data)

        # 应用自定义聚合规则创建聚合键
        working_data = data.copy()

        working_data['lat_agg'] = working_data[lat_col].apply(
            lambda x: self._apply_custom_precision_rule(x, coord_precision, 'coordinate')
        )
        working_data['lon_agg'] = working_data[lon_col].apply(
            lambda x: self._apply_custom_precision_rule(x, coord_precision, 'coordinate')
        )
        working_data['age_agg'] = working_data[age_col].apply(
            lambda x: self._apply_custom_precision_rule(x, age_precision, 'age', age_strategy)
        )

        # 创建聚合键
        working_data['agg_key'] = (
                working_data['lat_agg'].round(6).astype(str) + "_" +
                working_data['lon_agg'].round(6).astype(str) + "_" +
                working_data['age_agg'].round(2).astype(str)
        )

        # 获取要聚合的元素列
        element_columns = self._get_element_columns(working_data, params)

        # 按聚合键分组并执行聚合
        grouped = working_data.groupby('agg_key')
        aggregated_rows = []

        for agg_key, group in grouped:
            row = {
                'agg_key': agg_key,
                lat_col: group['lat_agg'].iloc[0],
                lon_col: group['lon_agg'].iloc[0],
                age_col: group['age_agg'].iloc[0],
                'sample_count': len(group)
            }

            # 计算元素列的算术平均值
            for col in element_columns:
                if col in group.columns:
                    valid_values = group[col].dropna()
                    if len(valid_values) > 0:
                        row[col] = valid_values.mean()
                    else:
                        row[col] = np.nan

            # 复制重要的非数值列
            important_text_columns = ['Location', 'Rock type', 'Continent', 'Country', 'Reference', 'SAMPLE_ID']
            for col in working_data.columns:
                if (col in important_text_columns and
                        col not in row and
                        not pd.api.types.is_numeric_dtype(working_data[col])):
                    mode_values = group[col].mode()
                    if len(mode_values) > 0:
                        row[col] = mode_values.iloc[0]
                    else:
                        row[col] = group[col].iloc[0]

            aggregated_rows.append(row)

        # 创建结果DataFrame
        result_df = pd.DataFrame(aggregated_rows)
        result_df = self._clean_result_columns(result_df, params)

        aggregated_count = len(result_df)

        # 计算统计信息
        statistics = self._calculate_custom_statistics(
            original_count, aggregated_count, result_df, params
        )

        print(f"[AGGREGATION] aggregation completed: {len(result_df)} aggregation groups")
        return result_df, statistics

    def _execute_location_aggregation(self, data: pd.DataFrame, params: Dict[str, Any]) -> tuple:
        """执行Location聚合"""
        print("[AGGREGATION] Starting Location aggregation...")

        location_col = params['location_column']
        age_col = params['age_column']
        age_precision = params['age_precision']
        age_strategy = params['age_strategy']

        original_count = len(data)

        # 应用年龄聚合规则
        working_data = data.copy()
        working_data['age_agg'] = working_data[age_col].apply(
            lambda x: self._apply_custom_precision_rule(x, age_precision, 'age', age_strategy)
        )

        # 创建聚合键：Location + 聚合后的年龄
        working_data['agg_key'] = (
                working_data[location_col].astype(str) + "_" +
                working_data['age_agg'].round(2).astype(str)
        )

        # 获取要聚合的元素列
        element_columns = self._get_element_columns_for_location(working_data, params)

        # 按聚合键分组并执行聚合
        grouped = working_data.groupby('agg_key')
        aggregated_rows = []

        for agg_key, group in grouped:
            row = {
                'agg_key': agg_key,
                location_col: group[location_col].iloc[0],  # 使用原始Location值
                age_col: group['age_agg'].iloc[0],
                'sample_count': len(group)
            }

            # 计算元素列的算术平均值
            for col in element_columns:
                if col in group.columns:
                    valid_values = group[col].dropna()
                    if len(valid_values) > 0:
                        row[col] = valid_values.mean()
                    else:
                        row[col] = np.nan

            # 复制重要的非数值列（如果有坐标信息的话）
            important_columns = ['LATITUDE', 'LONGITUDE', 'Rock type', 'Continent', 'Country', 'Reference', 'SAMPLE_ID']
            for col in working_data.columns:
                if (col in important_columns and
                        col not in row and
                        col in group.columns):
                    if pd.api.types.is_numeric_dtype(working_data[col]):
                        # 数值列取平均
                        valid_values = group[col].dropna()
                        if len(valid_values) > 0:
                            row[col] = valid_values.mean()
                        else:
                            row[col] = np.nan
                    else:
                        # 文本列取第一个
                        row[col] = group[col].iloc[0]

            aggregated_rows.append(row)

        # 创建结果DataFrame
        result_df = pd.DataFrame(aggregated_rows)
        result_df = self._clean_location_result_columns(result_df, params)

        aggregated_count = len(result_df)

        # 计算统计信息
        statistics = self._calculate_location_statistics(
            original_count, aggregated_count, result_df, params
        )

        print(f"[AGGREGATION] SUCCESS: {len(result_df)} ")
        return result_df, statistics

    def _apply_custom_precision_rule(self, value: float, precision: float,
                                     data_type: str = 'coordinate', strategy: str = 'round_nearest') -> float:
        """应用自定义精度聚合规则"""
        if pd.isna(value) or precision <= 0:
            return np.nan

        try:
            if data_type == 'age':
                if strategy == 'round_up':
                    return math.ceil(value / precision) * precision
                elif strategy == 'round_down':
                    return math.floor(value / precision) * precision
                else:  # round_nearest
                    return round(value / precision) * precision
            else:
                # 坐标使用标准的四舍五入
                return round(value / precision) * precision
        except (ValueError, OverflowError):
            print(f"[WARNING] Custom precision rule application failed，value: {value}, precision: {precision}")
            return np.nan

    def _get_element_columns(self, data: pd.DataFrame, params: Dict[str, Any]) -> list:
        """获取要聚合的元素列"""
        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']

        numeric_columns = list(data.select_dtypes(include=[np.number]).columns)
        exclude_columns = {lat_col, lon_col, age_col, 'lat_agg', 'lon_agg', 'age_agg', 'sample_count'}
        element_columns = [col for col in numeric_columns if col not in exclude_columns]

        print(f"[DEBUG] Found {len(element_columns)} element columns for aggregation")
        return element_columns

    def _get_element_columns_for_location(self, data: pd.DataFrame, params: Dict[str, Any]) -> list:
        """获取Location聚合的元素列"""
        location_col = params['location_column']
        age_col = params['age_column']

        numeric_columns = list(data.select_dtypes(include=[np.number]).columns)
        exclude_columns = {location_col, age_col, 'age_agg', 'sample_count'}
        element_columns = [col for col in numeric_columns if col not in exclude_columns]

        print(f"[DEBUG] FOUND {len(element_columns)} element columns for Location")
        return element_columns

    def _get_custom_group_description(self, params: Dict[str, Any]) -> str:
        """获取自定义聚合的分组描述"""
        strategy_desc = {
            'round_up': 'round up',
            'round_down': 'round down',
            'round_nearest': 'round nearest'
        }

        coord_desc = f"{params['coord_precision']}°precision"
        age_desc = f"{params['age_precision']}Ma precision({strategy_desc[params['age_strategy']]})"

        return f"Custom precision geographic aggregation({coord_desc}, {age_desc})"

    def _get_location_group_description(self, params: Dict[str, Any]) -> str:
        """获取Location聚合的分组描述"""
        strategy_desc = {
            'round_up': 'round up',
            'round_down': 'round down',
            'round_nearest': 'round nearest'
        }

        location_col = params['location_column']
        age_desc = f"{params['age_precision']}Ma precision({strategy_desc[params['age_strategy']]})"

        return f"Location aggregation({location_col} + {age_desc})"

    def _calculate_custom_statistics(self, original_count: int, aggregated_count: int,
                                     result_df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算自定义聚合的统计信息"""
        strategy_descriptions = {
            'round_up': 'round_up',
            'round_down': 'round_down',
            'round_nearest': 'round_nearest'
        }

        coord_desc = f"{params['coord_precision']}degrees precision"
        age_desc = f"{params['age_precision']}Ma precision ({strategy_descriptions[params['age_strategy']]})"

        statistics = {
            'original_count': original_count,
            'aggregated_count': aggregated_count,
            'compression_ratio': (original_count - aggregated_count) / original_count if original_count > 0 else 0,
            'aggregation_ratio': aggregated_count / original_count if original_count > 0 else 0,
            'method': 'custom_precision_geographic',
            'parameters': {
                'coord_precision': params['coord_precision'],
                'age_precision': params['age_precision'],
                'age_strategy': params['age_strategy'],
                'coord_description': coord_desc,
                'age_description': age_desc,
                'age_strategy_desc': strategy_descriptions[params['age_strategy']]
            },
            'avg_samples_per_group': result_df['sample_count'].mean() if len(result_df) > 0 else 0,
            'max_samples_per_group': result_df['sample_count'].max() if len(result_df) > 0 else 0,
            'min_samples_per_group': result_df['sample_count'].min() if len(result_df) > 0 else 0,
            'unique_groups': aggregated_count,
            'element_columns_averaged': self._get_element_columns(result_df, params)
        }

        return statistics

    def _calculate_location_statistics(self, original_count: int, aggregated_count: int,
                                       result_df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """计算Location聚合的统计信息"""
        strategy_descriptions = {
            'round_up': 'round_up',
            'round_down': 'round_down',
            'round_nearest': 'round_nearest'
        }

        location_desc = f" {params['location_column']} "
        age_desc = f"{params['age_precision']}Ma precision ({strategy_descriptions[params['age_strategy']]})"

        statistics = {
            'original_count': original_count,
            'aggregated_count': aggregated_count,
            'compression_ratio': (original_count - aggregated_count) / original_count if original_count > 0 else 0,
            'aggregation_ratio': aggregated_count / original_count if original_count > 0 else 0,
            'method': 'location_based_geographic',
            'parameters': {
                'location_column': params['location_column'],
                'age_precision': params['age_precision'],
                'age_strategy': params['age_strategy'],
                'location_description': location_desc,
                'age_description': age_desc,
                'age_strategy_desc': strategy_descriptions[params['age_strategy']]
            },
            'avg_samples_per_group': result_df['sample_count'].mean() if len(result_df) > 0 else 0,
            'max_samples_per_group': result_df['sample_count'].max() if len(result_df) > 0 else 0,
            'min_samples_per_group': result_df['sample_count'].min() if len(result_df) > 0 else 0,
            'unique_groups': aggregated_count,
            'unique_locations': result_df[params['location_column']].nunique() if len(result_df) > 0 else 0,
            'element_columns_averaged': self._get_element_columns_for_location(result_df, params)
        }

        return statistics

    def _clean_result_columns(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        修复版：清理结果DataFrame，确保正确的列顺序
        地理聚合数据的标准列顺序：基本信息 -> 坐标 -> 聚合信息 -> 主量元素 -> 微量元素 -> 其他信息
        """
        lat_col = params['latitude_column']
        lon_col = params['longitude_column']
        age_col = params['age_column']

        print(f"[DEBUG] column count: {len(df.columns)}")
        print(f"[DEBUG] columns: {lat_col}, {lon_col}, {age_col}")

        # 获取所有数值列（排除特殊列）
        excluded_cols = {
            age_col, lat_col, lon_col, 'Location', 'agg_key', 'sample_count',
            'Rock type', 'Continent', 'Country', 'Reference', 'SAMPLE_ID',
            'lat_agg', 'lon_agg', 'age_agg', 'error'
        }

        element_columns = []
        for col in df.columns:
            if (pd.api.types.is_numeric_dtype(df[col]) and
                    col not in excluded_cols and
                    not col.endswith('_std') and
                    not col.startswith('original_')):
                element_columns.append(col)

        print(f"[DEBUG] FOUND {len(element_columns)} element columns")

        # 构建标准的列顺序
        final_columns = []

        # 1. 年龄列（最重要的基础信息）
        if age_col in df.columns:
            final_columns.append(age_col)

        # 2. 坐标列（紧跟年龄）
        if lat_col in df.columns:
            final_columns.append(lat_col)
        if lon_col in df.columns:
            final_columns.append(lon_col)

        # 3. 位置信息
        if 'Location' in df.columns:
            final_columns.append('Location')

        # 4. 聚合关键信息
        for col in ['agg_key', 'sample_count']:
            if col in df.columns:
                final_columns.append(col)

        # 5. 主量元素（按标准顺序）
        major_elements_order = [
            'SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'Fe2O3T', 'FeO', 'FeOT',
            'MnO', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5'
        ]

        for element in major_elements_order:
            # 处理带空格的列名
            for col in element_columns:
                clean_col = col.strip()
                if clean_col == element or col == element:
                    final_columns.append(col)
                    if col in element_columns:
                        element_columns.remove(col)
                    break

        # 6. 重要的微量元素
        important_trace_elements = [
            'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
            'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Yb', 'Lu', 'Th', 'U'
        ]

        for element in important_trace_elements:
            for col in element_columns[:]:  # 使用切片避免修改迭代中的列表
                clean_col = col.strip()
                if clean_col == element or col == element:
                    final_columns.append(col)
                    element_columns.remove(col)
                    break

        # 7. 其他数值列（按字母顺序）
        remaining_numeric = sorted(element_columns)
        final_columns.extend(remaining_numeric)

        # 8. 重要的非数值列
        important_info_columns = ['Rock type', 'Continent', 'Country']
        for col in important_info_columns:
            if col in df.columns and col not in final_columns:
                final_columns.append(col)

        # 9. 其他剩余列
        for col in df.columns:
            if col not in final_columns:
                final_columns.append(col)

        # 去重并只保留存在的列
        final_columns = list(dict.fromkeys(final_columns))
        existing_columns = [col for col in final_columns if col in df.columns]

        print(f"[DEBUG] Final column order first 10: {existing_columns[:10]}")
        print(f"[DEBUG] Column count cleaning: {len(df.columns)} -> {len(existing_columns)}")

        return df[existing_columns]

    def _clean_location_result_columns(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """清理Location聚合结果DataFrame的列顺序"""
        location_col = params['location_column']
        age_col = params['age_column']

        print(f"[DEBUG] Location aggregation original column count: {len(df.columns)}")
        print(f"[DEBUG] Location aggregation key columns: {location_col}, {age_col}")

        # 构建标准的列顺序
        final_columns = []

        # 1. 年龄列（基础信息）
        if age_col in df.columns:
            final_columns.append(age_col)

        # 2. Location列
        if location_col in df.columns:
            final_columns.append(location_col)

        # 3. 坐标列（如果有的话）
        coordinate_cols = ['LATITUDE', 'LONGITUDE']
        for coord_col in coordinate_cols:
            if coord_col in df.columns:
                final_columns.append(coord_col)

        # 4. 聚合关键信息
        for col in ['agg_key', 'sample_count']:
            if col in df.columns:
                final_columns.append(col)

        # 5. 获取数值列并按重要性排序
        excluded_cols = set(final_columns + ['age_agg'])
        element_columns = []

        for col in df.columns:
            if (pd.api.types.is_numeric_dtype(df[col]) and
                    col not in excluded_cols and
                    not col.endswith('_std') and
                    not col.startswith('original_')):
                element_columns.append(col)

        # 6. 主量元素
        major_elements_order = [
            'SiO2', 'TiO2', 'Al2O3', 'Fe2O3', 'Fe2O3T', 'FeO', 'FeOT',
            'MnO', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5'
        ]

        for element in major_elements_order:
            for col in element_columns[:]:
                clean_col = col.strip()
                if clean_col == element or col == element:
                    final_columns.append(col)
                    element_columns.remove(col)
                    break

        # 7. 微量元素
        important_trace_elements = [
            'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
            'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Yb', 'Lu', 'Th', 'U'
        ]

        for element in important_trace_elements:
            for col in element_columns[:]:
                clean_col = col.strip()
                if clean_col == element or col == element:
                    final_columns.append(col)
                    element_columns.remove(col)
                    break

        # 8. 其他数值列
        remaining_numeric = sorted(element_columns)
        final_columns.extend(remaining_numeric)

        # 9. 其他重要非数值列
        important_info_columns = ['Rock type', 'Continent', 'Country', 'Reference']
        for col in important_info_columns:
            if col in df.columns and col not in final_columns:
                final_columns.append(col)

        # 10. 其他剩余列
        for col in df.columns:
            if col not in final_columns:
                final_columns.append(col)

        # 去重并只保留存在的列
        final_columns = list(dict.fromkeys(final_columns))
        existing_columns = [col for col in final_columns if col in df.columns]

        print(f"[DEBUG] Location aggregation final column order first 10: {existing_columns[:10]}")
        print(f"[DEBUG] Location aggregation column count cleaning: {len(df.columns)} -> {len(existing_columns)}")

        return df[existing_columns]


# ===== 兼容函数 =====

def create_simple_geo_processor():
    """创建简单地理数据处理器实例"""
    return SimpleGeoDataProcessor()


def create_enhanced_geo_processor():
    """创建增强版地理数据处理器实例"""
    return EnhancedGeoDataProcessor()


# ===== 异步执行支持 =====

def execute_simple_geo_aggregation(data: pd.DataFrame,
                                   params: Dict[str, Any],
                                   on_success: Callable,
                                   on_error: Callable) -> None:
    """异步执行简单地理聚合"""

    def run_aggregation():
        try:
            required_keys = ['latitude_column', 'longitude_column', 'age_column',
                             'coord_aggregation', 'age_aggregation']

            for key in required_keys:
                if key not in params:
                    on_error(f"MISSING PARAMS: {key}")
                    return

            processor = SimpleGeoDataProcessor()
            data_copy = data.copy()
            result = processor.perform_aggregation(data_copy, params)
            on_success(result)

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            on_error(error_msg)

    thread = threading.Thread(target=run_aggregation)
    thread.daemon = True
    thread.start()


def execute_custom_geo_aggregation(data: pd.DataFrame,
                                   params: Dict[str, Any],
                                   on_success: Callable,
                                   on_error: Callable) -> None:
    """异步执行自定义精度地理聚合"""

    def run_aggregation():
        try:
            required_keys = ['latitude_column', 'longitude_column', 'age_column',
                             'coord_precision', 'age_precision', 'age_strategy']

            for key in required_keys:
                if key not in params:
                    on_error(f"MISSING PARAMS: {key}")
                    return

            processor = EnhancedGeoDataProcessor()
            data_copy = data.copy()
            result = processor.perform_custom_aggregation(data_copy, params)
            on_success(result)

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            on_error(error_msg)

    thread = threading.Thread(target=run_aggregation)
    thread.daemon = True
    thread.start()


def execute_location_geo_aggregation(data: pd.DataFrame,
                                     params: Dict[str, Any],
                                     on_success: Callable,
                                     on_error: Callable) -> None:
    """异步执行Location地理聚合"""

    def run_aggregation():
        try:
            required_keys = ['location_column', 'age_column', 'age_precision', 'age_strategy']

            for key in required_keys:
                if key not in params:
                    on_error(f"MISSING PARAMS: {key}")
                    return

            processor = EnhancedGeoDataProcessor()
            data_copy = data.copy()
            result = processor.perform_location_aggregation(data_copy, params)
            on_success(result)

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            on_error(error_msg)

    thread = threading.Thread(target=run_aggregation)
    thread.daemon = True
    thread.start()


# ===== 智能处理器选择 =====

def create_smart_geo_processor(mode='auto'):
    """智能创建地理数据处理器"""
    if mode == 'simple':
        return SimpleGeoDataProcessor()
    elif mode == 'enhanced':
        return EnhancedGeoDataProcessor()
    else:  # auto
        # 默认返回增强版，保持向下兼容
        return EnhancedGeoDataProcessor()


def execute_geo_aggregation_smart(data: pd.DataFrame,
                                  params: Dict[str, Any],
                                  on_success: Callable,
                                  on_error: Callable) -> None:
    """智能执行地理聚合 - 根据参数自动选择处理器"""

    # 判断参数格式来决定使用哪个处理器
    if 'location_column' in params:
        # Location聚合
        execute_location_geo_aggregation(data, params, on_success, on_error)
    elif 'coord_precision' in params and 'age_precision' in params:
        # 新版参数格式，使用增强处理器
        execute_custom_geo_aggregation(data, params, on_success, on_error)
    else:
        # 旧版参数格式，使用简单处理器
        execute_simple_geo_aggregation(data, params, on_success, on_error)


# ===== 测试函数 =====

if __name__ == "__main__":
    # 测试原版兼容处理器
    print("=== TEST ===")

    import numpy as np

    np.random.seed(42)

    # 生成测试数据
    test_data = pd.DataFrame({
        'LATITUDE': np.random.uniform(-30, -25, 10),
        'LONGITUDE': np.random.uniform(125, 130, 10),
        'AGE': [8.9, 15.3, 19.7, 56.9, 75, 100, 150, 200, 500, 1000],
        'SiO2': np.random.normal(55, 5, 10),
        'Al2O3': np.random.normal(15, 2, 10),
        'Location': ['Test_A', 'Test_A', 'Test_B', 'Test_B', 'Test_C'] * 2
    })

    # 测试简单处理器
    simple_params = {
        'latitude_column': 'LATITUDE',
        'longitude_column': 'LONGITUDE',
        'age_column': 'AGE',
        'coord_aggregation': 'divide_10',
        'age_aggregation': 'divide_10'
    }

    processor = SimpleGeoDataProcessor()
    result = processor.perform_aggregation(test_data, simple_params)

    print(f"Original compatible aggregation result: {len(result['aggregated_data'])} aggregation groups")
    print("Original compatible aggregation ages:", sorted(result['aggregated_data']['AGE'].unique()))

    # 测试增强处理器
    print("\n=== TEST ===")

    enhanced_params = {
        'latitude_column': 'LATITUDE',
        'longitude_column': 'LONGITUDE',
        'age_column': 'AGE',
        'coord_precision': 1.0,
        'age_precision': 10.0,
        'age_strategy': 'round_up'
    }

    enhanced_processor = EnhancedGeoDataProcessor()
    enhanced_result = enhanced_processor.perform_custom_aggregation(test_data, enhanced_params)

    print(f"Enhanced aggregation result: {len(enhanced_result['aggregated_data'])} aggregation groups")
    print("Enhanced aggregation ages:", sorted(enhanced_result['aggregated_data']['AGE'].unique()))

    # 测试Location聚合
    print("\n=== TEST ===")

    location_params = {
        'location_column': 'Location',
        'age_column': 'AGE',
        'age_precision': 50.0,
        'age_strategy': 'round_up'
    }

    location_result = enhanced_processor.perform_location_aggregation(test_data, location_params)

    print(f"Location聚合结果: {len(location_result['aggregated_data'])} 个聚合组")
    print("Location聚合Location值:", sorted(location_result['aggregated_data']['Location'].unique()))
    print("Location聚合年龄:", sorted(location_result['aggregated_data']['AGE'].unique()))

    print("\n=== 兼容性测试完成 ===")
    print("✓ 原版SimpleGeoDataProcessor正常工作")
    print("✓ 增强版EnhancedGeoDataProcessor正常工作")
    print("✓ Location聚合功能正常工作")
    print("✓ 完整的地理聚合架构就绪")