"""
Outlier Removal Dialog - Simplified Version (Removed Application Range Options)
ui/outlier_removal_dialog.py
Fixed button layout and np undefined issues
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
from config.languages import language_manager


def matlab_compatible_percentile(data, percentile):
    """
    Fully compatible MATLAB percentile calculation

    Args:
        data: Data array
        percentile: Percentile (0-100)

    Returns:
        Percentile value
    """
    data_sorted = np.sort(data)
    n = len(data_sorted)

    # MATLAB quantile algorithm
    p = percentile / 100.0

    # MATLAB's index calculation method
    h = (n - 1) * p + 1  # MATLAB uses 1-based indexing
    h_floor = int(np.floor(h))
    h_ceil = int(np.ceil(h))

    # Convert to 0-based indexing
    idx_low = max(0, min(h_floor - 1, n - 1))
    idx_high = max(0, min(h_ceil - 1, n - 1))

    if idx_low == idx_high:
        return data_sorted[idx_low]
    else:
        # Linear interpolation
        weight = h - h_floor
        return data_sorted[idx_low] * (1 - weight) + data_sorted[idx_high] * weight


class OutlierRemovalDialog:
    """Outlier Removal Dialog - Simplified Version"""

    def __init__(self, parent, data, numeric_columns):
        self.parent = parent
        self.data = data
        self.numeric_columns = numeric_columns
        self.result = None

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Outlier Removal")
        self.window.geometry("750x550")  # Adjusted window size, removed application range section
        self.window.transient(parent)
        self.window.grab_set()
        self.window.configure(bg='white')

        # Center display
        self.center_window()

        # Initialize variables
        self.init_variables()

        # Create UI
        self.create_ui()

        # Bind events
        self.bind_events()

        # Initialize display
        self.on_column_changed()

    def center_window(self):
        """Center window display"""
        self.window.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (375)
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (275)
        self.window.geometry(f"750x550+{x}+{y}")

    def init_variables(self):
        """Initialize variables"""
        # Basic selection variables
        self.column_var = tk.StringVar()
        self.method_var = tk.StringVar(value="percentile")

        # Percentile method parameters
        self.lower_percentile_var = tk.DoubleVar(value=1)
        self.upper_percentile_var = tk.DoubleVar(value=99)

        # Standard deviation method parameters
        self.std_multiplier_var = tk.DoubleVar(value=2)

        # IQR method parameters
        self.iqr_multiplier_var = tk.DoubleVar(value=1.5)

        # Custom range parameters
        self.custom_lower_var = tk.StringVar()
        self.custom_upper_var = tk.StringVar()

        # Set default column
        if self.numeric_columns:
            self.column_var.set(self.numeric_columns[0])

    def create_ui(self):
        """Create user interface"""
        # Title
        title_frame = tk.Frame(self.window, bg='white', height=50)
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text="[Outlier] Outlier Removal",
            font=('Arial', 16, 'bold'),
            fg='#2563eb',
            bg='white'
        ).pack(side=tk.LEFT, pady=10)

        # Basic parameters area (only keep column selection)
        self.create_basic_params()

        # Detection method area
        self.create_detection_methods()

        # Preview area (with apply button)
        self.create_preview_with_apply()

    def create_basic_params(self):
        """Create basic parameters area - simplified version"""
        basic_frame = tk.LabelFrame(
            self.window,
            text="[1] Basic Parameters",
            font=('Arial', 11, 'bold'),
            bg='white',
            padx=10,
            pady=5
        )
        basic_frame.pack(fill=tk.X, padx=20, pady=5)

        # Column selection
        col_frame = tk.Frame(basic_frame, bg='white')
        col_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            col_frame,
            text="Select column for outlier removal:",
            font=('Arial', 10),
            bg='white'
        ).pack(side=tk.LEFT)

        self.column_combo = ttk.Combobox(
            col_frame,
            textvariable=self.column_var,
            values=self.numeric_columns,
            width=20,
            state="readonly"
        )
        self.column_combo.pack(side=tk.LEFT, padx=(10, 0))

        # Add instruction text
        info_frame = tk.Frame(basic_frame, bg='white')
        info_frame.pack(fill=tk.X, pady=(10, 5))

        info_label = tk.Label(
            info_frame,
            text="[Info] Will process current data in data manager for outlier removal",
            font=('Arial', 9),
            fg='#666666',
            bg='white'
        )
        info_label.pack(side=tk.LEFT)

    def create_detection_methods(self):
        """Create detection method area"""
        method_frame = tk.LabelFrame(
            self.window,
            text="[2] Detection Method",
            font=('Arial', 11, 'bold'),
            bg='white',
            padx=10,
            pady=5
        )
        method_frame.pack(fill=tk.X, padx=20, pady=5)

        # Percentile method
        perc_frame = tk.Frame(method_frame, bg='white')
        perc_frame.pack(fill=tk.X, pady=2)

        ttk.Radiobutton(
            perc_frame,
            text="Percentile Method",
            variable=self.method_var,
            value="percentile"
        ).pack(side=tk.LEFT)

        tk.Label(perc_frame, text="Lower Percentile:",
                font=('Arial', 9), bg='white').pack(side=tk.LEFT, padx=(20, 5))
        self.lower_percentile_entry = tk.Entry(perc_frame, textvariable=self.lower_percentile_var, width=6)
        self.lower_percentile_entry.pack(side=tk.LEFT)

        tk.Label(perc_frame, text="Upper Percentile:",
                font=('Arial', 9), bg='white').pack(side=tk.LEFT, padx=(10, 5))
        self.upper_percentile_entry = tk.Entry(perc_frame, textvariable=self.upper_percentile_var, width=6)
        self.upper_percentile_entry.pack(side=tk.LEFT)

        # Standard deviation method
        std_frame = tk.Frame(method_frame, bg='white')
        std_frame.pack(fill=tk.X, pady=2)

        ttk.Radiobutton(
            std_frame,
            text="Standard Deviation Method",
            variable=self.method_var,
            value="std_dev"
        ).pack(side=tk.LEFT)

        tk.Label(std_frame, text="Std Multiplier:",
                font=('Arial', 9), bg='white').pack(side=tk.LEFT, padx=(20, 5))
        self.std_multiplier_entry = tk.Entry(std_frame, textvariable=self.std_multiplier_var, width=6)
        self.std_multiplier_entry.pack(side=tk.LEFT)

        # IQR method
        iqr_frame = tk.Frame(method_frame, bg='white')
        iqr_frame.pack(fill=tk.X, pady=2)

        ttk.Radiobutton(
            iqr_frame,
            text="IQR Method",
            variable=self.method_var,
            value="iqr"
        ).pack(side=tk.LEFT)

        tk.Label(iqr_frame, text="IQR Multiplier:",
                font=('Arial', 9), bg='white').pack(side=tk.LEFT, padx=(20, 5))
        self.iqr_multiplier_entry = tk.Entry(iqr_frame, textvariable=self.iqr_multiplier_var, width=6)
        self.iqr_multiplier_entry.pack(side=tk.LEFT)

        # Custom range
        custom_frame = tk.Frame(method_frame, bg='white')
        custom_frame.pack(fill=tk.X, pady=2)

        ttk.Radiobutton(
            custom_frame,
            text="Custom Range",
            variable=self.method_var,
            value="custom"
        ).pack(side=tk.LEFT)

        tk.Label(custom_frame, text="Lower Bound:",
                font=('Arial', 9), bg='white').pack(side=tk.LEFT, padx=(20, 5))
        self.custom_lower_entry = tk.Entry(custom_frame, textvariable=self.custom_lower_var, width=8)
        self.custom_lower_entry.pack(side=tk.LEFT)

        tk.Label(custom_frame, text="Upper Bound:",
                font=('Arial', 9), bg='white').pack(side=tk.LEFT, padx=(10, 5))
        self.custom_upper_entry = tk.Entry(custom_frame, textvariable=self.custom_upper_var, width=8)
        self.custom_upper_entry.pack(side=tk.LEFT)

    def create_preview_with_apply(self):
        """Create preview area (with apply button)"""
        preview_frame = tk.LabelFrame(
            self.window,
            text="[3] Preview Results",
            font=('Arial', 11, 'bold'),
            bg='white',
            padx=10,
            pady=5
        )
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Button frame - preview and apply buttons side by side
        btn_frame = tk.Frame(preview_frame, bg='white')
        btn_frame.pack(fill=tk.X, pady=5)

        # Preview button
        self.preview_button = tk.Button(
            btn_frame,
            text="[Preview] Preview",
            command=self.preview_results,
            bg='#0891b2',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=5
        )
        self.preview_button.pack(side=tk.LEFT, padx=(0, 10))

        # Apply processing button - same style and size as preview button
        self.apply_button = tk.Button(
            btn_frame,
            text="[Apply] Apply Removal",
            command=self.apply_removal,
            bg='#dc3545',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=5
        )
        self.apply_button.pack(side=tk.LEFT)

        # Status label
        self.status_label = tk.Label(
            btn_frame,
            text="Click preview to view outlier detection results",
            font=('Arial', 9),
            fg='#666666',
            bg='white'
        )
        self.status_label.pack(side=tk.RIGHT, padx=(20, 0))

        # Preview text
        self.preview_text = tk.Text(
            preview_frame,
            height=12,
            font=('Consolas', 9),
            bg='#f8f9fa',
            wrap=tk.WORD,
            state=tk.DISABLED
        )

        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)

        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

    def bind_events(self):
        """Bind events"""
        self.column_combo.bind('<<ComboboxSelected>>', self.on_column_changed)
        self.method_var.trace('w', self.on_method_changed)

    def on_column_changed(self, event=None):
        """Column selection change event"""
        column = self.column_var.get()
        if column and column in self.data.columns:
            self.calculate_column_stats(column)
            self.update_custom_bounds_placeholder()

    def on_method_changed(self, *args):
        """Method change event"""
        method = self.method_var.get()
        self.update_parameter_states(method)

    def calculate_column_stats(self, column):
        """Calculate column statistics"""
        try:
            data_col = self.data[column].dropna()
            if len(data_col) == 0:
                return

            self.original_stats = {
                'count': len(data_col),
                'mean': data_col.mean(),
                'std': data_col.std(),
                'min': data_col.min(),
                'max': data_col.max(),
                'q25': data_col.quantile(0.25),
                'q50': data_col.quantile(0.50),
                'q75': data_col.quantile(0.75)
            }

            self.display_original_stats()

        except Exception as e:
            print(f"[ERROR] Failed to calculate column statistics: {e}")

    def display_original_stats(self):
        """Display original statistics"""
        if not hasattr(self, 'original_stats') or not self.original_stats:
            return

        stats_text = f"""
Data Statistics - {self.column_var.get()}
{'='*50}
Total Samples: {self.original_stats['count']}
Mean: {self.original_stats['mean']:.6f}
Standard Deviation: {self.original_stats['std']:.6f}
Minimum: {self.original_stats['min']:.6f}
Maximum: {self.original_stats['max']:.6f}

[Info] Will process current data in data manager
Select detection method and click preview to view outlier detection results
        """

        self.update_preview_text(stats_text)

    def update_custom_bounds_placeholder(self):
        """Update custom range placeholders"""
        if hasattr(self, 'original_stats') and self.original_stats:
            min_val = self.original_stats['min']
            max_val = self.original_stats['max']

            if not self.custom_lower_var.get():
                self.custom_lower_var.set(f"{min_val:.6f}")
            if not self.custom_upper_var.get():
                self.custom_upper_var.set(f"{max_val:.6f}")

    def update_parameter_states(self, method):
        """Update parameter input box states"""
        entries = [
            self.lower_percentile_entry,
            self.upper_percentile_entry,
            self.std_multiplier_entry,
            self.iqr_multiplier_entry,
            self.custom_lower_entry,
            self.custom_upper_entry
        ]

        for entry in entries:
            entry.configure(state='normal')

        if method == "percentile":
            self.std_multiplier_entry.configure(state='disabled')
            self.iqr_multiplier_entry.configure(state='disabled')
            self.custom_lower_entry.configure(state='disabled')
            self.custom_upper_entry.configure(state='disabled')
        elif method == "std_dev":
            self.lower_percentile_entry.configure(state='disabled')
            self.upper_percentile_entry.configure(state='disabled')
            self.iqr_multiplier_entry.configure(state='disabled')
            self.custom_lower_entry.configure(state='disabled')
            self.custom_upper_entry.configure(state='disabled')
        elif method == "iqr":
            self.lower_percentile_entry.configure(state='disabled')
            self.upper_percentile_entry.configure(state='disabled')
            self.std_multiplier_entry.configure(state='disabled')
            self.custom_lower_entry.configure(state='disabled')
            self.custom_upper_entry.configure(state='disabled')
        elif method == "custom":
            self.lower_percentile_entry.configure(state='disabled')
            self.upper_percentile_entry.configure(state='disabled')
            self.std_multiplier_entry.configure(state='disabled')

    def preview_results(self):
        """Preview outlier detection results - fixed version"""
        try:
            column = self.column_var.get()
            if not column:
                messagebox.showwarning(
                    "Preview Error",
                    "Please select a column first"
                )
                return

            if not self.validate_parameters():
                return

            # Get valid data - ensure correct data type
            data_col = self.data[column].dropna()
            if len(data_col) == 0:
                messagebox.showwarning(
                    "Preview Error",
                    "No valid data available"
                )
                return

            print(f"[PREVIEW-DEBUG] Starting outlier detection preview")
            print(f"[PREVIEW-DEBUG] Target column: {column}")
            print(f"[PREVIEW-DEBUG] Valid data count: {len(data_col)}")
            print(f"[PREVIEW-DEBUG] Data range: {data_col.min():.6f} - {data_col.max():.6f}")

            # Calculate thresholds - using fixed method
            method = self.method_var.get()
            print(f"[PREVIEW-DEBUG] Detection method: {method}")

            try:
                lower_bound, upper_bound = self.calculate_bounds(data_col, method)
                print(f"[PREVIEW-DEBUG] Calculated thresholds: {lower_bound:.6f} - {upper_bound:.6f}")
            except Exception as e:
                print(f"[PREVIEW-DEBUG] Error calculating thresholds: {e}")
                messagebox.showerror(
                    "Preview Error",
                    f"Failed to calculate thresholds: {str(e)}"
                )
                return

            # Detect outliers
            try:
                outliers_mask = (data_col < lower_bound) | (data_col > upper_bound)
                outliers = data_col[outliers_mask]
                remaining = data_col[~outliers_mask]

                print(f"[PREVIEW-DEBUG] Outlier count: {len(outliers)}")
                print(f"[PREVIEW-DEBUG] Remaining count: {len(remaining)}")

            except Exception as e:
                print(f"[PREVIEW-DEBUG] Error detecting outliers: {e}")
                messagebox.showerror(
                    "Preview Error",
                    f"Failed to detect outliers: {str(e)}"
                )
                return

            # Generate preview report
            try:
                preview_report = self.generate_preview_report(
                    column, method, data_col, outliers, remaining, lower_bound, upper_bound
                )

                print(f"[PREVIEW-DEBUG] Preview report generated successfully")

                self.update_preview_text(preview_report)

                # Update status label
                outlier_count = len(outliers)
                self.status_label.config(
                    text=f"Will remove {outlier_count} outliers, click [Apply] to apply processing",
                    fg='#28a745'
                )

                print(f"[PREVIEW-DEBUG] Preview completed, outlier count: {outlier_count}")

            except Exception as e:
                print(f"[PREVIEW-DEBUG] Error generating preview report: {e}")
                messagebox.showerror(
                    "Preview Error",
                    f"Failed to generate preview report: {str(e)}"
                )
                return

        except Exception as e:
            print(f"[PREVIEW-DEBUG] Overall preview error: {e}")
            import traceback
            traceback.print_exc()

            messagebox.showerror(
                "Preview Error",
                f"Preview failed: {str(e)}"
            )

            self.status_label.config(
                text="Preview failed, please check parameter settings",
                fg='#dc3545'
            )

    def validate_parameters(self):
        """Validate parameters - with debug info"""
        method = self.method_var.get()
        print(f"[VALIDATE-DEBUG] Validating parameters, method: {method}")

        try:
            if method == "percentile":
                lower = self.lower_percentile_var.get()
                upper = self.upper_percentile_var.get()
                print(f"[VALIDATE-DEBUG] Percentile parameters: {lower}% - {upper}%")

                if lower >= upper or lower < 0 or upper > 100:
                    print(f"[VALIDATE-DEBUG] Invalid percentile parameters")
                    messagebox.showerror(
                        "Invalid Parameters",
                        "Invalid percentile range (0-100 and lower < upper)"
                    )
                    return False

            elif method == "std_dev":
                multiplier = self.std_multiplier_var.get()
                print(f"[VALIDATE-DEBUG] Standard deviation multiplier: {multiplier}")

                if multiplier <= 0:
                    print(f"[VALIDATE-DEBUG] Invalid std multiplier")
                    messagebox.showerror(
                        "Invalid Parameters",
                        "Standard deviation multiplier must be greater than 0"
                    )
                    return False

            elif method == "iqr":
                multiplier = self.iqr_multiplier_var.get()
                print(f"[VALIDATE-DEBUG] IQR multiplier: {multiplier}")

                if multiplier <= 0:
                    print(f"[VALIDATE-DEBUG] Invalid IQR multiplier")
                    messagebox.showerror(
                        "Invalid Parameters",
                        "IQR multiplier must be greater than 0"
                    )
                    return False

            elif method == "custom":
                lower_str = self.custom_lower_var.get()
                upper_str = self.custom_upper_var.get()
                print(f"[VALIDATE-DEBUG] Custom range: '{lower_str}' - '{upper_str}'")

                if not lower_str or not upper_str:
                    print(f"[VALIDATE-DEBUG] Custom range is empty")
                    messagebox.showerror(
                        "Invalid Parameters",
                        "Custom method requires upper and lower bounds"
                    )
                    return False

                try:
                    lower = float(lower_str)
                    upper = float(upper_str)
                    print(f"[VALIDATE-DEBUG] Converted custom range: {lower} - {upper}")

                    if lower >= upper:
                        print(f"[VALIDATE-DEBUG] Custom range order error")
                        messagebox.showerror(
                            "Invalid Parameters",
                            "Lower bound must be less than upper bound"
                        )
                        return False
                except ValueError:
                    print(f"[VALIDATE-DEBUG] Custom range format error")
                    messagebox.showerror(
                        "Invalid Parameters",
                        "Please enter valid numeric values"
                    )
                    return False

            print(f"[VALIDATE-DEBUG] Parameter validation passed")
            return True

        except Exception as e:
            print(f"[VALIDATE-DEBUG] Error during parameter validation: {e}")
            messagebox.showerror(
                "Invalid Parameters",
                f"Parameter validation error: {str(e)}"
            )
            return False

    def calculate_bounds(self, data, method):
        """Calculate outlier thresholds - MATLAB compatible version"""
        try:
            print(f"[BOUNDS-DEBUG] Starting threshold calculation, method: {method}")
            print(f"[BOUNDS-DEBUG] Data type: {type(data)}")
            print(f"[BOUNDS-DEBUG] Data count: {len(data)}")

            # Ensure data is numpy array
            if hasattr(data, 'values'):
                data_array = data.values
            else:
                data_array = np.array(data)

            print(f"[BOUNDS-DEBUG] Converted data type: {type(data_array)}")

            if method == "percentile":
                lower_pct = self.lower_percentile_var.get()
                upper_pct = self.upper_percentile_var.get()
                print(f"[BOUNDS-DEBUG] Percentile parameters: {lower_pct}% - {upper_pct}%")

                # Use MATLAB fully compatible algorithm
                lower_bound = matlab_compatible_percentile(data_array, lower_pct)
                upper_bound = matlab_compatible_percentile(data_array, upper_pct)

                print(f"[BOUNDS-DEBUG] MATLAB compatible results: {lower_bound:.6f} - {upper_bound:.6f}")

                # Compare with other methods (for debugging)
                try:
                    # Try new version NumPy
                    np_lower_new = np.percentile(data_array, lower_pct, method='linear')
                    np_upper_new = np.percentile(data_array, upper_pct, method='linear')
                    print(f"[BOUNDS-DEBUG] NumPy new version results: {np_lower_new:.6f} - {np_upper_new:.6f}")
                except TypeError:
                    try:
                        # Fall back to old version
                        np_lower_old = np.percentile(data_array, lower_pct, interpolation='linear')
                        np_upper_old = np.percentile(data_array, upper_pct, interpolation='linear')
                        print(f"[BOUNDS-DEBUG] NumPy old version results: {np_lower_old:.6f} - {np_upper_old:.6f}")
                    except:
                        # Most basic NumPy
                        np_lower_basic = np.percentile(data_array, lower_pct)
                        np_upper_basic = np.percentile(data_array, upper_pct)
                        print(f"[BOUNDS-DEBUG] NumPy basic results: {np_lower_basic:.6f} - {np_upper_basic:.6f}")

            elif method == "std_dev":
                mean = np.mean(data_array)
                std = np.std(data_array)
                multiplier = self.std_multiplier_var.get()
                lower_bound = mean - multiplier * std
                upper_bound = mean + multiplier * std

                print(f"[BOUNDS-DEBUG] Std dev method: mean={mean:.6f}, std={std:.6f}, multiplier={multiplier}")
                print(f"[BOUNDS-DEBUG] Calculated results: {lower_bound:.6f} - {upper_bound:.6f}")

            elif method == "iqr":
                # Use MATLAB compatible Q1, Q3 calculation
                q1 = matlab_compatible_percentile(data_array, 25)
                q3 = matlab_compatible_percentile(data_array, 75)
                iqr = q3 - q1
                multiplier = self.iqr_multiplier_var.get()
                lower_bound = q1 - multiplier * iqr
                upper_bound = q3 + multiplier * iqr

                print(f"[BOUNDS-DEBUG] MATLAB compatible IQR: Q1={q1:.6f}, Q3={q3:.6f}, IQR={iqr:.6f}, multiplier={multiplier}")
                print(f"[BOUNDS-DEBUG] Calculated results: {lower_bound:.6f} - {upper_bound:.6f}")

            elif method == "custom":
                lower_bound = float(self.custom_lower_var.get())
                upper_bound = float(self.custom_upper_var.get())

                print(f"[BOUNDS-DEBUG] Custom range: {lower_bound:.6f} - {upper_bound:.6f}")

            else:
                raise ValueError(f"Unknown detection method: {method}")

            print(f"[BOUNDS-DEBUG] Threshold calculation successful")
            return lower_bound, upper_bound

        except Exception as e:
            print(f"[BOUNDS-DEBUG] Error calculating thresholds: {e}")
            import traceback
            traceback.print_exc()
            raise

    def generate_preview_report(self, column, method, original_data, outliers, remaining, lower_bound, upper_bound):
        """Generate preview report"""
        method_names = {
            'percentile': 'Percentile Method',
            'std_dev': 'Standard Deviation Method',
            'iqr': 'IQR Method',
            'custom': 'Custom Range'
        }

        outlier_count = len(outliers)
        remaining_count = len(remaining)
        removal_percentage = (outlier_count / len(original_data)) * 100

        report = f"""
Outlier Detection - {column}
{'='*60}

Method: {method_names.get(method, method)}
Threshold Range: [{lower_bound:.6f}, {upper_bound:.6f}]

Detection Results:
{'-'*40}
Total Samples: {len(original_data)}
Outlier Count: {outlier_count} ({removal_percentage:.2f}%)
Remaining Samples: {remaining_count} ({100-removal_percentage:.2f}%)

Original Statistics:
{'-'*40}
Mean: {original_data.mean():.6f}
Standard Deviation: {original_data.std():.6f}
Minimum: {original_data.min():.6f}
Maximum: {original_data.max():.6f}

After Removal Statistics:
{'-'*40}"""

        if remaining_count > 0:
            report += f"""
Mean: {remaining.mean():.6f}
Standard Deviation: {remaining.std():.6f}
Minimum: {remaining.min():.6f}
Maximum: {remaining.max():.6f}"""
        else:
            report += f"""
No remaining data"""

        if outlier_count > 0 and outlier_count <= 10:
            report += f"""

Outlier Values:
{'-'*40}"""
            for i, val in enumerate(outliers.values):
                report += f"\n{i+1}: {val:.6f}"
        elif outlier_count > 10:
            report += f"""

Outlier Sample (First 10):
{'-'*40}"""
            for i, val in enumerate(outliers.values[:10]):
                report += f"\n{i+1}: {val:.6f}"
            report += f"\n... and {outlier_count-10} more outliers"

        report += f"""

[Info] Current data in data manager will be processed
Note: This is only a preview result, click "Apply Processing" to actually execute outlier removal
        """

        return report

    def update_preview_text(self, text):
        """Update preview text"""
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, text)
        self.preview_text.config(state=tk.DISABLED)

    def apply_removal(self):
        """Apply outlier removal"""
        try:
            column = self.column_var.get()
            if not column:
                messagebox.showwarning(
                    "Warning",
                    "Please select a column first"
                )
                return

            # Validate parameters
            if not self.validate_parameters():
                return

            # Confirmation dialog
            method = self.method_var.get()
            method_names = {
                'percentile': 'Percentile Method',
                'std_dev': 'Standard Deviation Method',
                'iqr': 'IQR Method',
                'custom': 'Custom Range'
            }

            confirm_message = f"Confirm Outlier Removal?\n\n" \
                              f"Target Column: {column}\n" \
                              f"Method: {method_names.get(method, method)}\n" \
                              f"Processing Range: Current data in data manager\n\n" \
                              f"This operation will remove detected outliers and cannot be undone"

            if not self.show_custom_confirm_dialog("Confirm", confirm_message):
                return

            # Build result parameters - remove apply_to parameter
            self.result = {
                'column': column,
                'method': method,
                'parameters': self.get_method_parameters()
            }

            # Close dialog
            self.window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Apply outlier removal failed: {str(e)}"
            )

    def show_custom_confirm_dialog(self, title, message):
        """Show custom confirmation dialog - system style"""
        dialog = tk.Toplevel(self.window)
        dialog.title(title)
        dialog.geometry("420x220")  # Increased height
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.configure(bg='#f0f0f0')

        # Center display
        x = self.window.winfo_rootx() + 50
        y = self.window.winfo_rooty() + 50
        dialog.geometry(f"420x220+{x}+{y}")

        result = [False]

        # Main content frame
        content_frame = tk.Frame(dialog, bg='#f0f0f0', padx=20, pady=15)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Top section - icon and text
        top_frame = tk.Frame(content_frame, bg='#f0f0f0')
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Question icon
        icon_frame = tk.Frame(top_frame, bg='#f0f0f0', width=50)
        icon_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        icon_frame.pack_propagate(False)

        icon_label = tk.Label(icon_frame, text="?", font=('Arial', 24, 'bold'),
                              fg='white', bg='#0078d4', width=2, height=1,
                              relief=tk.FLAT)
        icon_label.pack(pady=(5, 0))

        # Text area
        text_frame = tk.Frame(top_frame, bg='#f0f0f0')
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Message text - adjust wraplength and font size
        msg_label = tk.Label(text_frame, text=message, bg='#f0f0f0',
                             justify=tk.LEFT, wraplength=320,
                             font=('Arial', 10))  # Slightly larger font
        msg_label.pack(anchor='w', pady=(5, 0))

        # Button frame
        btn_frame = tk.Frame(content_frame, bg='#f0f0f0')
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        def on_yes():
            result[0] = True
            dialog.destroy()

        def on_no():
            result[0] = False
            dialog.destroy()

        def on_close():
            result[0] = False
            dialog.destroy()

        # Button style
        button_style = {
            'font': ('Arial', 10),
            'width': 10,  # Increased button width
            'height': 1,
            'relief': tk.RAISED,
            'borderwidth': 1,
            'cursor': 'hand2'
        }

        # Buttons
        no_btn = tk.Button(btn_frame, text="No", command=on_no,
                           bg='#e1e1e1', fg='black', **button_style)
        no_btn.pack(side=tk.RIGHT, padx=(10, 0))

        yes_btn = tk.Button(btn_frame, text="Yes", command=on_yes,
                            bg='#e1e1e1', fg='black', **button_style)
        yes_btn.pack(side=tk.RIGHT)

        # Set close event
        dialog.protocol("WM_DELETE_WINDOW", on_close)

        # Set focus
        yes_btn.focus_set()
        dialog.bind('<Return>', lambda e: on_yes())
        dialog.bind('<Escape>', lambda e: on_no())

        dialog.wait_window()
        return result[0]

    def get_method_parameters(self):
        """Get method parameters"""
        method = self.method_var.get()

        if method == "percentile":
            return {
                'lower_percentile': self.lower_percentile_var.get(),
                'upper_percentile': self.upper_percentile_var.get()
            }
        elif method == "std_dev":
            return {
                'std_multiplier': self.std_multiplier_var.get()
            }
        elif method == "iqr":
            return {
                'iqr_multiplier': self.iqr_multiplier_var.get()
            }
        elif method == "custom":
            return {
                'lower_bound': float(self.custom_lower_var.get()),
                'upper_bound': float(self.custom_upper_var.get())
            }

        return {}

    def show(self):
        """Show dialog and return result"""
        self.window.focus_set()
        self.window.wait_window()
        return self.result


def show_outlier_removal_dialog(parent, data, numeric_columns):
    """Convenience function to show outlier removal dialog"""
    try:
        dialog = OutlierRemovalDialog(parent, data, numeric_columns)
        return dialog.show()
    except Exception as e:
        print(f"[ERROR] Failed to show outlier removal dialog: {e}")
        messagebox.showerror(
            "Error",
            f"Dialog error: {str(e)}"
        )
        return None