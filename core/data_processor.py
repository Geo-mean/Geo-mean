"""
增强的数据处理器模块 - 修复位置列数据类型问题
core/data_processor.py
"""
import pandas as pd
import numpy as np
import os
import time
import csv
from config.languages import language_manager


class DataProcessor:
    """数据处理类，负责Excel文件读取和数据处理"""

    def __init__(self):
        self.data = None
        self.file_path = None
        self.total_rows = 0
        self.sample_size = 999999999  # 移除行数限制

    def load_data(self, file_path, progress_callback=None):
        """统一数据加载入口 - 根据文件扩展名自动分发到Excel或CSV读取逻辑"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.csv':
            return self.load_csv(file_path, progress_callback)
        else:
            # 默认按Excel处理，兼容 .xlsx / .xls 以及未知后缀的旧调用方式
            return self.load_excel(file_path, progress_callback)

    def load_excel(self, file_path, progress_callback=None):
        """优化的Excel文件读取方法 - 统一进度回调"""
        try:
            # 1. 文件大小检查
            if progress_callback:
                check_msg = language_manager.get_text('checking_file_size', 'checking_file_size')
                progress_callback(check_msg)

            file_size = os.path.getsize(file_path) / (1024 * 1024)

            if progress_callback:
                size_msg = language_manager.get_text('file_size_detected', f'file size: {file_size:.2f}MB')
                progress_callback(size_msg)

            # 2. 根据文件大小选择处理方式
            if file_size > 100:
                return self._load_large_file(file_path, progress_callback)
            elif file_size > 10:
                return self._load_medium_file(file_path, progress_callback)
            else:
                return self._load_small_file(file_path, progress_callback)

        except Exception as e:
            error_msg = language_manager.get_text('load_error', f'load error: {str(e)}')
            if progress_callback:
                progress_callback(error_msg)
            return False, f"error: {str(e)}"

    def _detect_csv_encoding_and_sep(self, file_path):
        """探测CSV文件的编码和分隔符

        国内地质/地球化学数据的CSV经常是Excel导出的GBK编码，也可能是
        UTF-8（带或不带BOM）；分隔符默认逗号，但也可能是分号或制表符。
        """
        encodings_to_try = ['utf-8-sig', 'utf-8', 'gbk', 'gb18030', 'latin1']
        encoding = 'utf-8'
        sample_text = None

        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    sample_text = f.read(8192)
                encoding = enc
                break
            except (UnicodeDecodeError, UnicodeError, LookupError):
                continue

        sep = ','
        if sample_text:
            try:
                dialect = csv.Sniffer().sniff(sample_text, delimiters=[',', ';', '\t', '|'])
                sep = dialect.delimiter
            except csv.Error:
                sep = ','

        return encoding, sep

    def load_csv(self, file_path, progress_callback=None):
        """CSV文件读取方法 - 进度回调格式与load_excel保持一致

        复用与Excel加载相同的Location列修复和数据类型优化流程，保证
        无论加载CSV还是Excel，得到的数据结构和后续分析行为一致。
        """
        try:
            if progress_callback:
                check_msg = language_manager.get_text('checking_file_size', 'checking_file_size')
                progress_callback(check_msg)

            file_size = os.path.getsize(file_path) / (1024 * 1024)

            if progress_callback:
                size_msg = language_manager.get_text('file_size_detected', f'file size: {file_size:.2f}MB')
                progress_callback(size_msg)

            if progress_callback:
                read_msg = language_manager.get_text('reading_file', 'reading_file')
                progress_callback(read_msg)

            encoding, sep = self._detect_csv_encoding_and_sep(file_path)
            print(f"[DEBUG] CSV检测结果: encoding={encoding}, sep='{sep}'")

            is_large_file = file_size > 100

            try:
                read_kwargs = {'encoding': encoding, 'sep': sep}
                if is_large_file:
                    # 超大CSV先只读取一部分样本，避免卡死界面
                    read_kwargs['nrows'] = 10000

                try:
                    # 优先强制Location列为字符串，避免被误读成数值
                    self.data = pd.read_csv(file_path, dtype={'Location': 'str'}, **read_kwargs)
                except (ValueError, TypeError):
                    # 文件里没有Location列时，上面的dtype参数会报错，直接不指定dtype重读
                    self.data = pd.read_csv(file_path, **read_kwargs)

            except (UnicodeDecodeError, pd.errors.ParserError) as read_error:
                print(f"[WARNING] 按检测结果读取CSV失败: {read_error}，尝试备用方式重试")
                if progress_callback:
                    retry_msg = language_manager.get_text('read_retry', '使用备用方式重试读取...')
                    progress_callback(retry_msg)
                try:
                    # 最后兜底：交给pandas自行猜测编码和分隔符
                    self.data = pd.read_csv(file_path, sep=None, engine='python')
                except Exception as e2:
                    error_msg = f"读取失败: {str(e2)}. 请确认CSV文件编码或手动转换为UTF-8"
                    if progress_callback:
                        progress_callback(language_manager.get_text('read_failed', error_msg))
                    return False, error_msg

            # 应用与Excel一致的位置列后处理
            self._post_load_location_fix()

            # 数据类型优化（与Excel共用同一套逻辑）
            if progress_callback:
                opt_msg = language_manager.get_text('optimizing_data', '正在优化数据类型...')
                progress_callback(opt_msg)

            self.data = self._optimize_dtypes(self.data, progress_callback)
            self.file_path = file_path
            self.total_rows = len(self.data)

            # 大文件采样（与Excel逻辑一致）
            if self.total_rows > self.sample_size:
                if progress_callback:
                    sample_msg = language_manager.get_text(
                        'sampling_data', f'数据量过大，采样 {self.sample_size}/{self.total_rows} 行')
                    progress_callback(sample_msg)
                self.data = self.data.sample(n=self.sample_size, random_state=42).reset_index(drop=True)

            complete_msg = language_manager.get_text(
                'load_complete',
                f'Successfully loaded data， {self.total_rows} row，{len(self.data.columns)} col')
            if is_large_file:
                complete_msg += language_manager.get_text(
                    'csv_large_file_sampled', '（文件较大，仅读取前10000行样本）')
            if progress_callback:
                progress_callback(complete_msg)

            return True, complete_msg

        except Exception as e:
            error_msg = language_manager.get_text('load_error', f'load error: {str(e)}')
            if progress_callback:
                progress_callback(error_msg)
            return False, f"error: {str(e)}"

    def _get_excel_engine(self, file_path):
        """智能选择Excel读取引擎"""
        file_ext = os.path.splitext(file_path)[1].lower()
        available_engines = []

        try:
            import openpyxl
            available_engines.append('openpyxl')
        except ImportError:
            pass

        try:
            import xlrd
            available_engines.append('xlrd')
        except ImportError:
            pass

        if file_ext == '.xlsx':
            if 'openpyxl' in available_engines:
                return 'openpyxl'
            elif 'xlrd' in available_engines:
                return 'xlrd'
        elif file_ext == '.xls':
            if 'xlrd' in available_engines:
                return 'xlrd'
            elif 'openpyxl' in available_engines:
                return 'openpyxl'

        return None

    def _detect_location_columns_from_file(self, file_path, engine=None):
        """检测文件中的位置列并准备dtype字典 - 策略A专用"""
        try:
            # 不依赖引擎，直接尝试读取样本
            try:
                sample_df = pd.read_excel(file_path, nrows=3)
            except Exception:
                print("[WARNING] error")
                return {'Location': 'str'}  # 强制Location为字符串

            dtype_dict = {}

            # 强制指定Location列为字符串，不管检测结果如何
            for col in sample_df.columns:
                col_name = str(col).strip()

                if col_name == 'Location' or col_name.lower() == 'location':
                    dtype_dict[col] = 'str'
                    print(f"[FIX] Location '{col}' ")
                    break

            # 如果没找到Location列，可能列名有问题，强制添加
            if not dtype_dict:
                dtype_dict['Location'] = 'str'
                print(f"[FIX] NO FOUND Location")

            return dtype_dict

        except Exception as e:
            print(f"[WARNING] ERROR: {e}")
            return {'Location': 'str'}

    def _load_small_file(self, file_path, progress_callback=None):
        """加载小文件 - 策略A修复版"""
        if progress_callback:
            read_msg = language_manager.get_text('reading_file', 'reading_file')
            progress_callback(read_msg)

        # 策略A: 多种方法尝试正确读取Location列
        location_fix_success = False

        try:
            if progress_callback:
                progress_callback("正在尝试修复Location列读取...")

            # 方法1: 强制指定Location列为字符串
            print("[FIX-A1] 尝试强制Location列为字符串类型...")
            try:
                self.data = pd.read_excel(file_path, dtype={'Location': 'str'})

                if 'Location' in self.data.columns:
                    location_data = self.data['Location']
                    valid_count = location_data.notna().sum()

                    # 检查是否还是'nan'字符串
                    if valid_count > 0:
                        non_nan_count = (location_data != 'nan').sum()
                        if non_nan_count > 0:
                            print(f"[SUCCESS-A1] Location列修复成功! 有效数据: {non_nan_count}")
                            location_fix_success = True
                        else:
                            print(f"[INFO-A1] Location列读取为字符串，但都是'nan'，尝试下一方法")
                    else:
                        print(f"[INFO-A1] Location列仍为空，尝试下一方法")

                if location_fix_success:
                    print(f"[DEBUG-A1] Location列前5个值: {self.data['Location'].head().tolist()}")

            except Exception as e1:
                print(f"[WARNING-A1] dtype方法失败: {e1}")

            # 方法2: 如果方法1失败，使用object类型读取全部
            if not location_fix_success:
                print("[FIX-A2] 尝试object类型读取全部列...")
                try:
                    self.data = pd.read_excel(file_path, dtype=object)

                    if 'Location' in self.data.columns:
                        # 检查原始数据
                        raw_location = self.data['Location']
                        print(f"[DEBUG-A2] 原始Location类型: {raw_location.dtype}")
                        print(f"[DEBUG-A2] 原始Location前5个值: {raw_location.head().tolist()}")

                        # 转换为字符串并检查
                        self.data['Location'] = raw_location.astype('str')
                        location_data = self.data['Location']

                        # 检查有效数据（排除'nan'和空值）
                        valid_mask = (location_data.notna()) & (location_data != 'nan') & (location_data != '')
                        valid_count = valid_mask.sum()

                        if valid_count > 0:
                            print(f"[SUCCESS-A2] object类型读取成功! Location有效数据: {valid_count}")
                            print(f"[DEBUG-A2] 有效Location样本: {location_data[valid_mask].head().tolist()}")
                            location_fix_success = True
                        else:
                            print(f"[INFO-A2] object读取成功，但Location列数据无效")

                except Exception as e2:
                    print(f"[WARNING-A2] object类型读取失败: {e2}")

            # 方法3: 如果方法2失败，使用converters
            if not location_fix_success:
                print("[FIX-A3] 尝试使用converters强制转换...")
                try:
                    def location_converter(x):
                        if pd.isna(x):
                            return None
                        return str(x).strip()

                    self.data = pd.read_excel(file_path, converters={'Location': location_converter})

                    if 'Location' in self.data.columns:
                        location_data = self.data['Location']
                        valid_count = location_data.notna().sum()

                        if valid_count > 0:
                            print(f"[SUCCESS-A3] converter修复成功! Location有效数据: {valid_count}")
                            print(f"[DEBUG-A3] Location样本: {location_data.dropna().head().tolist()}")
                            location_fix_success = True

                except Exception as e3:
                    print(f"[WARNING-A3] converter方法失败: {e3}")

            # 方法4: 如果所有方法都失败，尝试不指定引擎的默认读取
            if not location_fix_success:
                print("[FIX-A4] 尝试默认读取方式...")
                try:
                    self.data = pd.read_excel(file_path)

                    if 'Location' in self.data.columns:
                        location_data = self.data['Location']
                        print(f"[DEBUG-A4] 默认读取Location类型: {location_data.dtype}")
                        print(f"[DEBUG-A4] 默认读取Location前5个值: {location_data.head().tolist()}")

                        # 如果是数值型，尝试查看原始Excel内容
                        if pd.api.types.is_numeric_dtype(location_data):
                            print("[WARNING-A4] Location列仍被读取为数值型，可能Excel文件中该列确实有问题")
                        else:
                            valid_count = location_data.notna().sum()
                            if valid_count > 0:
                                print(f"[SUCCESS-A4] 默认读取找到Location数据: {valid_count}")
                                location_fix_success = True

                except Exception as e4:
                    print(f"[ERROR-A4] 默认读取也失败: {e4}")
                    return False, f"所有读取方法都失败: {str(e4)}"

            # 最终检查Location列状态
            if 'Location' in self.data.columns:
                location_col = self.data['Location']
                total_count = len(location_col)
                valid_count = location_col.notna().sum()

                if pd.api.types.is_numeric_dtype(location_col):
                    non_nan_count = (~location_col.isna()).sum()
                else:
                    non_nan_count = ((location_col != 'nan') & (location_col.notna()) & (location_col != '')).sum()

                print(f"[FINAL] Location列最终状态:")
                print(f"[FINAL]   类型: {location_col.dtype}")
                print(f"[FINAL]   总数: {total_count}")
                print(f"[FINAL]   非空数: {valid_count}")
                print(f"[FINAL]   有效数据数: {non_nan_count}")
                print(f"[FINAL]   修复成功: {'是' if location_fix_success else '否'}")

                if location_fix_success:
                    print(f"[SUCCESS] Location列读取修复完成!")
                else:
                    print(f"[WARNING] Location列修复未完全成功，但文件已加载")

            else:
                print("[ERROR] 文件中没有找到Location列")

        except Exception as e:
            print(f"[ERROR] Location修复过程失败: {e}")
            return False, f"加载失败: {str(e)}"

        # 继续正常的数据处理流程
        try:
            # 数据类型优化
            if progress_callback:
                opt_msg = language_manager.get_text('optimizing_data', '正在优化数据类型...')
                progress_callback(opt_msg)

            self.data = self._optimize_dtypes(self.data, progress_callback)

            self.file_path = file_path
            self.total_rows = len(self.data)

            if progress_callback:
                complete_msg = language_manager.get_text('load_complete',
                                                         f'Successfully loaded data， {self.total_rows} row，{len(self.data.columns)} col')
                progress_callback(complete_msg)

            return True, f"Successfully loaded data， {self.total_rows} row，{len(self.data.columns)} col"

        except Exception as e:
            return False, f"ERROR: {str(e)}"

    def _post_load_location_fix(self):
        """读取后的位置列修复"""
        try:
            location_keywords = ['location', 'country', 'region', 'place', 'area']

            for col in self.data.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in location_keywords):

                    # 检查该列的数据状况
                    col_data = self.data[col]

                    # 如果是数值型且全为NaN，这可能是读取问题
                    if pd.api.types.is_numeric_dtype(col_data) and col_data.isna().all():
                        print(f"[FIX] 发现问题位置列 '{col}': 数值型且全为NaN")

                        # 尝试将该列转换为字符串类型
                        try:
                            self.data[col] = self.data[col].astype('str')
                            print(f"[FIX] 位置列 '{col}' 已转换为字符串类型")
                        except:
                            print(f"[WARNING] 位置列 '{col}' 转换失败")

                    # 如果是数值型但有数据，可能是位置编码
                    elif pd.api.types.is_numeric_dtype(col_data) and col_data.notna().sum() > 0:
                        unique_count = col_data.nunique()
                        print(f"[INFO] 位置列 '{col}' 是数值型，唯一值: {unique_count}")

                        # 如果唯一值数量合理，转换为字符串
                        if 2 <= unique_count <= len(self.data) * 0.3:
                            try:
                                self.data[col] = self.data[col].astype('str')
                                print(f"[FIX] 数值位置列 '{col}' 已转换为字符串")
                            except:
                                print(f"[WARNING] 数值位置列 '{col}' 转换失败")

        except Exception as e:
            print(f"[ERROR] 位置列后处理失败: {e}")

    def _load_medium_file(self, file_path, progress_callback=None):
        """加载中等大小文件 - 修复版"""
        if progress_callback:
            read_msg = language_manager.get_text('reading_medium_file', '正在读取中等大小文件...')
            progress_callback(read_msg)

        engine = self._get_excel_engine(file_path)

        try:
            if progress_callback:
                engine_text = engine or "default"
                engine_msg = language_manager.get_text('engine_selected', f'使用 {engine_text} 引擎读取文件')
                progress_callback(engine_msg)

            # 应用相同的位置列检测逻辑
            dtype_dict = self._detect_location_columns_from_file(file_path, engine)

            try:
                if dtype_dict and engine:
                    self.data = pd.read_excel(file_path, engine=engine, dtype=dtype_dict)
                elif dtype_dict:
                    self.data = pd.read_excel(file_path, dtype=dtype_dict)
                elif engine:
                    self.data = pd.read_excel(file_path, engine=engine)
                else:
                    self.data = pd.read_excel(file_path)
            except Exception as dtype_error:
                print(f"[WARNING] 带dtype读取失败: {dtype_error}")
                if engine:
                    self.data = pd.read_excel(file_path, engine=engine)
                else:
                    self.data = pd.read_excel(file_path)

        except Exception as e:
            if progress_callback:
                retry_msg = language_manager.get_text('read_retry', '使用备用方式重试读取...')
                progress_callback(retry_msg)
            try:
                self.data = pd.read_excel(file_path)
            except Exception as e2:
                if progress_callback:
                    error_msg = language_manager.get_text('read_failed', f'文件读取失败: {str(e2)}')
                    progress_callback(error_msg)
                return False, f"读取失败: {str(e2)}. 请确保安装了 openpyxl 或 xlrd 库"

        # 应用位置列后处理
        self._post_load_location_fix()

        # 数据类型优化
        if progress_callback:
            opt_msg = language_manager.get_text('optimizing_data', '正在优化数据类型...')
            progress_callback(opt_msg)

        self.data = self._optimize_dtypes(self.data, progress_callback)
        self.file_path = file_path
        self.total_rows = len(self.data)

        # 检查是否需要采样
        if self.total_rows > self.sample_size:
            if progress_callback:
                sample_msg = language_manager.get_text('sampling_data',
                                                      f'数据量过大，采样 {self.sample_size}/{self.total_rows} 行')
                progress_callback(sample_msg)
            self.data = self.data.sample(n=self.sample_size, random_state=42).reset_index(drop=True)

        if progress_callback:
            complete_msg = language_manager.get_text('load_complete',
                                                    f'Successfully loaded data， {self.total_rows} row {len(self.data)} row，{len(self.data.columns)} col')
            progress_callback(complete_msg)

        return True, f"Successfully loaded data， {self.total_rows} row（ {len(self.data)} row），{len(self.data.columns)} col"

    def _load_large_file(self, file_path, progress_callback=None):
        """加载超大文件 - 统一回调格式"""
        if progress_callback:
            large_msg = language_manager.get_text('reading_large_file', 'reading_large_file')
            progress_callback(large_msg)

        try:
            engine = self._get_excel_engine(file_path)

            if progress_callback:
                sample_msg = language_manager.get_text('reading_sample', 'reading_sample')
                progress_callback(sample_msg)

            if engine:
                sample_data = pd.read_excel(file_path, engine=engine, nrows=10000)
            else:
                sample_data = pd.read_excel(file_path, nrows=10000)

            if progress_callback:
                opt_msg = language_manager.get_text('optimizing_data', 'optimizing_data')
                progress_callback(opt_msg)

            sample_data = self._optimize_dtypes(sample_data, progress_callback)

            self.data = sample_data
            self.file_path = file_path
            self.total_rows = len(self.data)

            if progress_callback:
                complete_msg = language_manager.get_text('load_complete_sample',
                                                        f' {len(self.data)} row，{len(self.data.columns)} col')
                progress_callback(complete_msg)

            return True, f"{len(self.data)} row，{len(self.data.columns)} col"

        except Exception as e:
            if progress_callback:
                error_msg = language_manager.get_text('large_file_error', f'large_file_error: {str(e)}')
                progress_callback(error_msg)
            return False, f"large_file_error: {str(e)}."

    def _optimize_dtypes(self, df, progress_callback=None):
        """优化数据类型 - 保护Location列版本"""
        if progress_callback:
            convert_msg = language_manager.get_text('converting_numeric', 'converting_numeric')
            progress_callback(convert_msg)

        try:
            # 保护Location列，不要让它被转换为数值型
            location_col_data = None
            if 'Location' in df.columns:
                location_col_data = df['Location'].copy()
                print(f"[PROTECT] type: {location_col_data.dtype}")

            # 针对地球化学数据的数值列转换
            numeric_candidates = [
                'AGE', 'LATITUDE', 'LONGITUDE', 'Age_uncertainty',
                'SIO2', 'TIO2', 'AL2O3', 'FE2O3', 'FE2O3T', 'FEO', 'FEOT',
                'MNO', 'MGO', 'CAO', 'NA2O', 'K2O', 'P2O5', 'LOI',
                'LA', 'CE', 'PR', 'ND', 'SM', 'EU', 'GD', 'TB', 'DY',
                'HO', 'ER', 'TM', 'YB', 'LU', 'ZR', 'BA', 'TA', 'U',
                'Y', 'HF', 'PB', 'TH', 'RB', 'SR', 'NB', 'ThU',
                'lg_NbTh', 'lg_Th', 'Ritt'
            ]

            converted_count = 0
            total_candidates = len(
                [col for col in df.columns if col in numeric_candidates or self._is_likely_numeric_column(col)])

            for col in df.columns:
                # 跳过Location列，不要转换它
                if col == 'Location':
                    continue

                if col in numeric_candidates or self._is_likely_numeric_column(col):
                    try:
                        # 尝试转换为数值，处理可能的错误值
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        converted_count += 1

                        # 简化进度报告 - 减少回调频率
                        if progress_callback and converted_count % 10 == 0:
                            progress_msg = language_manager.get_text('conversion_progress',
                                                                     f'conversion_progress: {converted_count}/{total_candidates}')
                            progress_callback(progress_msg)
                    except:
                        continue

            # 恢复Location列数据
            if location_col_data is not None and 'Location' in df.columns:
                df['Location'] = location_col_data
                print(f"[RESTORE] type: {df['Location'].dtype}")

            if progress_callback:
                memory_msg = language_manager.get_text('memory_optimization', 'memory_optimization')
                progress_callback(memory_msg)

            # 对于已经是数值的列，进行内存优化（跳过Location）
            for col in df.select_dtypes(include=['int64']).columns:
                if col != 'Location':
                    df[col] = pd.to_numeric(df[col], downcast='integer')

            for col in df.select_dtypes(include=['float64']).columns:
                if col != 'Location':
                    df[col] = pd.to_numeric(df[col], downcast='float')

            # 对于字符串列，如果重复率高就转为category（但保持Location为字符串）
            for col in df.select_dtypes(include=['object']).columns:
                if col != 'Location' and df[col].nunique() / len(df) < 0.5:
                    df[col] = df[col].astype('category')

            if progress_callback:
                complete_msg = language_manager.get_text('optimization_complete',
                                                         f'optimization_complete {converted_count} 列')
                progress_callback(complete_msg)

        except Exception as e:
            if progress_callback:
                warning_msg = language_manager.get_text('optimization_warning', f'optimization_warning: {str(e)}')
                progress_callback(warning_msg)
            print(f"[WARNING] error: {e}")

        return df

    def _is_likely_numeric_column(self, col_name):
        """判断列名是否可能是数值列 - 精确匹配"""
        numeric_keywords = [
            'AGE', 'SIO2', 'TIO2', 'AL2O3', 'FE2O3', 'FEO', 'FEOT', 'FE2O3T',
            'MGO', 'CAO', 'NA2O', 'K2O', 'P2O5', 'LOI', 'MNO',
            'LATITUDE', 'LONGITUDE'
        ]
        col_upper = col_name.upper()
        # 精确匹配，避免 'ER' 匹配到 'REFERENCE' 这类误判
        return col_upper in numeric_keywords

    def get_columns(self):
        """获取数据列名"""
        if self.data is not None:
            return list(self.data.columns)
        return []

    def get_numeric_columns(self):
        """获取数值型列名"""
        if self.data is not None:
            return list(self.data.select_dtypes(include=[np.number]).columns)
        return []

    def get_data_info(self):
        """获取数据基本信息"""
        if self.data is not None:
            return {
                'rows': len(self.data),
                'columns': len(self.data.columns),
                'numeric_columns': len(self.get_numeric_columns()),
                'file_path': self.file_path,
                'memory_usage': self.data.memory_usage(deep=True).sum() / 1024 / 1024  # MB
            }
        return None