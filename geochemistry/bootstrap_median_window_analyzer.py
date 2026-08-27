"""
Bootstrap Median Window Analyzer
geochemistry/bootstrap_median_window_analyzer.py

Specialized for calculating bootstrap median statistics in moving windows
Reuses existing window generation and boundary processing logic, only modifies statistical calculations
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Callable


class BootstrapMedianWindowAnalyzer:
    """Bootstrap Median Window Analyzer"""

    def __init__(self, n_bootstrap: int = 10000):
        """
        Initialize analyzer

        Parameters:
            n_bootstrap: Number of bootstrap resamples, default 10000
        """
        self.n_bootstrap = n_bootstrap

    def analyze(self,
                data: pd.DataFrame,
                age_column: str,
                target_column: str,
                window_size: float,
                step_size: float,
                min_age: float,
                max_age: float,
                min_samples: int = 5,
                progress_callback: Optional[Callable] = None) -> Optional[pd.DataFrame]:
        """
        Execute Bootstrap median moving window analysis

        Parameters:
            data: Input data
            age_column: Age column name
            target_column: Target column name
            window_size: Window size
            step_size: Step size
            min_age: Minimum age
            max_age: Maximum age
            min_samples: Minimum sample size
            progress_callback: Progress callback function

        Returns:
            Result DataFrame, same format as moving window analysis
        """
        try:
            print(f"[BOOTSTRAP-MEDIAN-WINDOW] Starting analysis...")
            print(
                f"[BOOTSTRAP-MEDIAN-WINDOW] Parameters: window={window_size}, step={step_size}, range={min_age}-{max_age}")
            print(f"[BOOTSTRAP-MEDIAN-WINDOW] Min samples={min_samples}, Bootstrap iterations={self.n_bootstrap}")

            # 1. Data validation and cleaning
            clean_data, age_data, target_data, valid_mask = self._prepare_data(
                data, age_column, target_column
            )

            if progress_callback:
                progress_callback(f"[MEDIAN] Valid data: {valid_mask.sum()} rows")

            # 2. Generate moving windows
            windows = self._generate_windows(min_age, max_age, window_size, step_size)

            if progress_callback:
                progress_callback(f"[MEDIAN] Generated {len(windows)} windows")

            print(f"[BOOTSTRAP-MEDIAN-WINDOW] Generated {len(windows)} windows")

            # 3. Execute Bootstrap median analysis for each window
            results = self._analyze_windows(
                age_data, target_data, valid_mask,
                windows, age_column, target_column,
                min_samples, progress_callback
            )

            # 4. Validate results (Fix: proper DataFrame checking)
            if results is None:
                print("[WARNING] No results generated - results is None")
                return None

            if isinstance(results, list) and len(results) == 0:
                print("[WARNING] No results generated - empty list")
                return None

            if isinstance(results, pd.DataFrame) and results.empty:
                print("[WARNING] No results generated - empty DataFrame")
                return None

            # results is already a DataFrame from _analyze_windows
            results_df = results

            valid_count = results_df[f'{target_column}_median'].notna().sum()
            print(f"[SUCCESS] Bootstrap median analysis complete: {len(results_df)} windows, {valid_count} valid")

            if progress_callback:
                progress_callback(f"[MEDIAN] Analysis complete: {valid_count}/{len(results_df)} valid windows")

            return results_df

        except Exception as e:
            print(f"[ERROR] Bootstrap median analysis failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _prepare_data(self, data: pd.DataFrame, age_column: str, target_column: str):
        """Prepare and validate data"""
        # Check if columns exist
        if age_column not in data.columns:
            raise ValueError(f"Age column '{age_column}' does not exist")
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' does not exist")

        # Convert to numeric type
        age_data = pd.to_numeric(data[age_column], errors='coerce')
        target_data = pd.to_numeric(data[target_column], errors='coerce')

        # Check valid data
        valid_mask = age_data.notna() & target_data.notna()
        valid_count = valid_mask.sum()

        if valid_count < 10:
            raise ValueError(f"Too few valid data points: {valid_count} < 10")

        print(f"[INFO] Valid data pairs: {valid_count}")
        print(f"[INFO] Age range: {age_data[valid_mask].min():.1f} - {age_data[valid_mask].max():.1f}")
        print(f"[INFO] Target value range: {target_data[valid_mask].min():.6f} - {target_data[valid_mask].max():.6f}")

        return data, age_data, target_data, valid_mask

    def _generate_windows(self, min_age: float, max_age: float,
                          window_size: float, step_size: float):
        """
        Generate moving window list

        Returns:
            [(center1, lower1, upper1), (center2, lower2, upper2), ...]
        """
        windows = []
        current_center = min_age + window_size / 2

        while current_center + window_size / 2 <= max_age:
            window_low = current_center - window_size / 2
            window_high = current_center + window_size / 2
            windows.append((current_center, window_low, window_high))
            current_center += step_size

        return windows

    def _analyze_windows(self, age_data, target_data, valid_mask,
                         windows, age_column, target_column,
                         min_samples, progress_callback):
        """Execute Bootstrap median analysis for each window"""
        results = []
        valid_windows = 0
        skipped_windows = 0

        for i, (center, low, high) in enumerate(windows):
            try:
                # Get data within window
                window_mask = (age_data >= low) & (age_data <= high) & valid_mask
                window_values = target_data[window_mask].dropna().values

                # Check sample count
                if len(window_values) < min_samples:
                    # Insufficient samples, record NaN
                    results.append({
                        age_column: center,
                        f'{target_column}_median': np.nan,
                        f'{age_column}-{target_column}_median': f"{center}-NaN",
                        'std_error': np.nan,
                        'sample_count': len(window_values),
                        'window_low': low,
                        'window_high': high
                    })
                    skipped_windows += 1
                    continue

                # Execute Bootstrap median analysis
                bootstrap_medians = self._bootstrap_resample_median(window_values)

                # Calculate statistics
                median_mean = np.mean(bootstrap_medians)  # Mean of medians
                median_std = np.std(bootstrap_medians, ddof=0)  # Standard deviation
                std_error = 2 * median_std  # 2σ error

                # Save results
                results.append({
                    age_column: center,
                    f'{target_column}_median': median_mean,
                    f'{age_column}-{target_column}_median': f"{center}-{median_mean:.6f}",
                    'std_error': std_error,
                    'sample_count': len(window_values),
                    'window_low': low,
                    'window_high': high
                })

                valid_windows += 1

                # Progress callback
                if progress_callback and (i + 1) % 10 == 0:
                    progress_callback(
                        f"[MEDIAN] Processing window {i + 1}/{len(windows)} "
                        f"(center: {center:.0f}Ma, samples: {len(window_values)})"
                    )

            except Exception as e:
                print(f"[ERROR] Window {center} processing failed: {e}")
                continue

        print(f"[INFO] Valid windows: {valid_windows}/{len(windows)}")
        print(f"[INFO] Skipped windows: {skipped_windows} (insufficient samples)")

        # Ensure correct column order
        if results:
            results_df = pd.DataFrame(results)
            column_order = [
                age_column,
                f'{target_column}_median',
                f'{age_column}-{target_column}_median',
                'std_error',
                'sample_count',
                'window_low',
                'window_high'
            ]
            return results_df[column_order]

        return []

    def _bootstrap_resample_median(self, values: np.ndarray) -> np.ndarray:
        """
        Bootstrap resample to calculate median

        Parameters:
            values: Data within window

        Returns:
            bootstrap_medians: Array of medians from each resample
        """
        bootstrap_medians = []
        n_samples = len(values)

        # Set random seed (consistent with moving_window_integration)
        np.random.seed(42)

        for _ in range(self.n_bootstrap):
            # Sample with replacement
            sample_indices = np.random.randint(0, n_samples, size=n_samples)
            sample = values[sample_indices]

            # Calculate median (key: use median instead of mean)
            bootstrap_medians.append(np.median(sample))

        return np.array(bootstrap_medians)


# ===== Convenience Functions =====

def run_bootstrap_median_window_analysis(
        data: pd.DataFrame,
        params: Dict,
        progress_callback: Optional[Callable] = None
) -> Optional[pd.DataFrame]:
    """
    Run Bootstrap median moving window analysis (convenience function)

    Parameters:
        data: Input data
        params: Analysis parameters dictionary, must contain:
            - age_column: Age column name
            - target_column: Target column name
            - window_size: Window size
            - step_size: Step size
            - min_age: Minimum age
            - max_age: Maximum age
            - min_samples: Minimum sample size (optional, default 5)
            - n_bootstrap: Bootstrap iterations (optional, default 10000)
        progress_callback: Progress callback function

    Returns:
        Result DataFrame
    """
    # Extract parameters
    age_column = params['age_column']
    target_column = params['target_column']
    window_size = params['window_size']
    step_size = params['step_size']
    min_age = params['min_age']
    max_age = params['max_age']
    min_samples = params.get('min_samples', 5)
    n_bootstrap = params.get('n_bootstrap', 10000)

    # Create analyzer
    analyzer = BootstrapMedianWindowAnalyzer(n_bootstrap=n_bootstrap)

    # Execute analysis
    return analyzer.analyze(
        data=data,
        age_column=age_column,
        target_column=target_column,
        window_size=window_size,
        step_size=step_size,
        min_age=min_age,
        max_age=max_age,
        min_samples=min_samples,
        progress_callback=progress_callback
    )


# ===== Test Code =====

if __name__ == "__main__":
    print("=== Bootstrap Median Window Analyzer Test ===\n")

    # Generate test data
    np.random.seed(42)
    test_data = pd.DataFrame({
        'AGE': np.random.uniform(0, 1000, 200),
        'ThU': np.random.lognormal(0, 0.5, 200)
    })

    print(f"Test data: {len(test_data)} rows")

    # Test parameters
    test_params = {
        'age_column': 'AGE',
        'target_column': 'ThU',
        'window_size': 100,
        'step_size': 50,
        'min_age': 100,
        'max_age': 900,
        'min_samples': 5,
        'n_bootstrap': 1000  # Fewer iterations for testing
    }

    # Execute analysis
    result_df = run_bootstrap_median_window_analysis(test_data, test_params)

    if result_df is not None:
        print("\nResult DataFrame:")
        print(result_df.head(10))
        print(f"\nResult shape: {result_df.shape}")
        print(f"Column names: {list(result_df.columns)}")
        print(f"\nValid windows: {result_df['ThU_median'].notna().sum()}/{len(result_df)}")

    print("\n✅ Test complete")