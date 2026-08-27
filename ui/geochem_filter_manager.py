# ui/geochem_filter_manager.py
"""
Simplified universal filter condition manager
Only retains the most basic filtering functionality, removes complex presets and special processing
"""

import pandas as pd
import numpy as np
from config.languages import language_manager


class GeochemFilterManager:
    """Simplified universal filter condition manager"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.active_filters = []
        self.filtered_data = None
        self.original_data = None

    def show_filter_dialog(self):
        """Show filter condition setting dialog"""
        try:
            # Validate data availability
            is_valid, message = self.main_window.data_manager.validate_data_for_operation()
            if not is_valid:
                self.main_window.show_warning_message(
                    "Warning",
                    message
                )
                return

            # Get numeric columns
            numeric_columns = self.main_window.data_processor.get_numeric_columns()
            if not numeric_columns:
                self.main_window.show_warning_message(
                    "Warning",
                    "No numeric columns available for filtering"
                )
                return

            # Show simplified filter dialog
            from ui.filter_window import SimpleFilterWindow

            filter_window = SimpleFilterWindow(self.main_window.root, numeric_columns)

            # Wait for dialog completion
            self.main_window.root.wait_window(filter_window.window)

            # Get result
            result = filter_window.result

            if result:
                self.apply_filters(result)

        except Exception as e:
            print(f"[ERROR] Failed to show filter dialog: {e}")
            self.main_window.show_error_message(
                "Error",
                f"Failed to show filter dialog: {str(e)}"
            )

    def apply_filters(self, filters):
        """Apply filter conditions - simplified version"""
        try:
            self.main_window.update_status("[Processing] Applying filter conditions...")

            # Get current data
            source_data = self._get_current_data()
            if source_data is None:
                self.main_window.show_error_message(
                    "Error",
                    'No data available for filtering, please load file first'
                )
                return

            # Save original data reference
            if self.original_data is None:
                self.original_data = self._get_original_data()

            # Apply filter conditions
            filtered_data = self._apply_simple_filters(source_data, filters)

            if filtered_data is not None:
                operation_name = f"Data Filtering ({len(filters)} conditions)"

                # Update data
                success = self._update_data_consistently(filtered_data, operation_name, filters)

                if success:
                    # Update local state
                    self.filtered_data = filtered_data
                    self.active_filters = filters.copy()

                    # Update interface
                    self._update_interface()

                    # Show filter results
                    self._show_simple_filter_results(filters, filtered_data, source_data)
                    self.main_window.update_status("[OK] Filter conditions applied successfully")
                else:
                    self.main_window.update_status("[Error] Data update failed")
            else:
                self.main_window.update_status("[Error] Filter conditions application failed")

        except Exception as e:
            print(f"[ERROR] Error during filtering: {e}")
            self.main_window.show_error_message(
                "Error",
                f"Error during filtering: {str(e)}"
            )

    def _apply_simple_filters(self, data, filters):
        """Improved filter condition application - supports NaN handling strategy, keeps method name unchanged"""
        try:
            if not filters:
                return data.copy()

            print("[IMPROVED-FILTER] Starting improved filtering - supports NaN strategy")

            filtered_data = data.copy()
            initial_rows = len(filtered_data)

            print(f"[IMPROVED-FILTER] Original data rows: {initial_rows}")
            print(f"[IMPROVED-FILTER] Number of filter conditions: {len(filters)}")

            # Apply filter conditions one by one
            for step, filter_info in enumerate(filters, 1):
                # Check filter condition format (backward compatible)
                if len(filter_info) == 4:
                    # New format: (column, condition, value, nan_policy)
                    column, condition, value, nan_policy = filter_info
                else:
                    # Old format: (column, condition, value) - default delete NaN
                    column, condition, value = filter_info
                    nan_policy = "delete_nan"

                print(f"[IMPROVED-FILTER] Step {step}: {column} {condition} {value} [NaN strategy: {nan_policy}]")

                if column not in filtered_data.columns:
                    print(f"[ERROR] Column does not exist: {column}")
                    continue

                # Ensure column is numeric
                filtered_data[column] = pd.to_numeric(filtered_data[column], errors='coerce')

                before_count = len(filtered_data)

                # Apply filtering based on NaN handling strategy
                if nan_policy == "keep_nan":
                    # Keep NaN strategy: only apply conditions to non-NaN values, preserve NaN values
                    print(f"[NaN-STRATEGY] Using keep NaN strategy")

                    if condition == ">=":
                        # Keep: value is NaN or value >= value
                        mask = (filtered_data[column].isna()) | (filtered_data[column] >= value)
                    elif condition == "<=":
                        # Keep: value is NaN or value <= value
                        mask = (filtered_data[column].isna()) | (filtered_data[column] <= value)
                    elif condition == ">":
                        # Keep: value is NaN or value > value
                        mask = (filtered_data[column].isna()) | (filtered_data[column] > value)
                    elif condition == "<":
                        # Keep: value is NaN or value < value
                        mask = (filtered_data[column].isna()) | (filtered_data[column] < value)
                    elif condition == "==":
                        # Keep: value is NaN or value == value
                        mask = (filtered_data[column].isna()) | (filtered_data[column] == value)
                    elif condition == "!=":
                        # Keep: value is NaN or value != value
                        mask = (filtered_data[column].isna()) | (filtered_data[column] != value)
                    else:
                        print(f"[WARNING] Unsupported condition: {condition}")
                        continue

                else:  # nan_policy == "delete_nan"
                    # Delete NaN strategy: NaN values are deleted, only keep non-NaN values that meet conditions
                    print(f"[NaN-STRATEGY] Using delete NaN strategy")

                    if condition == ">=":
                        # Keep: value is not NaN and value >= value
                        mask = (filtered_data[column].notna()) & (filtered_data[column] >= value)
                    elif condition == "<=":
                        # Keep: value is not NaN and value <= value
                        mask = (filtered_data[column].notna()) & (filtered_data[column] <= value)
                    elif condition == ">":
                        # Keep: value is not NaN and value > value
                        mask = (filtered_data[column].notna()) & (filtered_data[column] > value)
                    elif condition == "<":
                        # Keep: value is not NaN and value < value
                        mask = (filtered_data[column].notna()) & (filtered_data[column] < value)
                    elif condition == "==":
                        # Keep: value is not NaN and value == value
                        mask = (filtered_data[column].notna()) & (filtered_data[column] == value)
                    elif condition == "!=":
                        # Keep: value is not NaN and value != value
                        mask = (filtered_data[column].notna()) & (filtered_data[column] != value)
                    else:
                        print(f"[WARNING] Unsupported condition: {condition}")
                        continue

                # Apply filter mask
                filtered_data = filtered_data[mask].copy()

                after_count = len(filtered_data)
                removed_count = before_count - after_count

                nan_strategy_desc = "Keep NaN rows" if nan_policy == "keep_nan" else "Delete NaN rows"
                print(
                    f"[IMPROVED-FILTER] Row count change: {before_count} -> {after_count} (removed {removed_count} rows) [{nan_strategy_desc}]")

            # Reset index
            filtered_data.reset_index(drop=True, inplace=True)

            final_rows = len(filtered_data)
            total_removed = initial_rows - final_rows
            retention_rate = (final_rows / initial_rows * 100) if initial_rows > 0 else 0

            print(f"[SUCCESS] Improved filtering completed!")
            print(f"[SUCCESS] Original rows: {initial_rows}")
            print(f"[SUCCESS] Final rows: {final_rows}")
            print(f"[SUCCESS] Removed rows: {total_removed}")
            print(f"[SUCCESS] Retention rate: {retention_rate:.1f}%")

            # Show usage statistics for each strategy
            keep_nan_count = sum(1 for f in filters if (len(f) > 3 and f[3] == "keep_nan"))
            delete_nan_count = len(filters) - keep_nan_count
            print(f"[STRATEGY-SUMMARY] NaN strategy statistics:")
            print(f"[STRATEGY-SUMMARY]   Keep NaN strategy: {keep_nan_count} conditions")
            print(f"[STRATEGY-SUMMARY]   Delete NaN strategy: {delete_nan_count} conditions")

            return filtered_data

        except Exception as e:
            print(f"[ERROR] Error occurred during improved filtering: {str(e)}")
            import traceback
            print(f"[DEBUG] Complete error information: {traceback.format_exc()}")
            return None

    def _get_current_data(self):
        """Get current data"""
        if hasattr(self.main_window, 'global_data_manager'):
            return self.main_window.global_data_manager.get_current_data()
        elif hasattr(self.main_window, 'data') and self.main_window.data is not None:
            return self.main_window.data.copy()
        else:
            return self.main_window.data_processor.data.copy() if self.main_window.data_processor.data is not None else None

    def _get_original_data(self):
        """Get original data"""
        if hasattr(self.main_window, 'global_data_manager'):
            return self.main_window.global_data_manager.get_original_data()
        else:
            return self.main_window.data_processor.data.copy() if self.main_window.data_processor.data is not None else None

    def _update_data_consistently(self, filtered_data, operation_name, filters):
        """Update data consistently"""
        try:
            if hasattr(self.main_window, 'global_data_manager'):
                return self.main_window.global_data_manager.update_current_data(
                    filtered_data,
                    operation_name,
                    metadata={
                        'filter_count': len(filters),
                        'filters': filters.copy()
                    }
                )
            else:
                self.main_window.data = filtered_data
                self.main_window.data_processor.data = filtered_data
                return True
        except Exception as e:
            print(f"[ERROR] Data update failed: {e}")
            return False

    def _update_interface(self):
        """Update interface"""
        try:
            if hasattr(self.main_window, 'update_data_interface_preserve_selection'):
                self.main_window.update_data_interface_preserve_selection()
            else:
                self.main_window.data_manager.update_data_interface_after_load()
        except Exception as e:
            print(f"[WARNING] Interface update failed: {e}")

    def _show_simple_filter_results(self, filters, filtered_data, original_data):
        """Improved filter result display - supports NaN strategy display, keeps method name unchanged"""
        try:
            original_rows = len(original_data)
            filtered_rows = len(filtered_data)
            retention_rate = (filtered_rows / original_rows * 100) if original_rows > 0 else 0

            result_text = f"""Filtering completed!

Applied filter conditions (with NaN handling strategy):"""

            for i, filter_info in enumerate(filters, 1):
                if len(filter_info) == 4:
                    column, condition, value, nan_policy = filter_info
                    nan_desc = "Keep NaN rows" if nan_policy == "keep_nan" else "Delete NaN rows"
                    result_text += f"\n  {i}. {column} {condition} {value} ({nan_desc})"
                else:
                    column, condition, value = filter_info
                    result_text += f"\n  {i}. {column} {condition} {value} (Delete NaN rows)"

            # Statistics of NaN strategy usage
            keep_nan_count = sum(1 for f in filters if (len(f) > 3 and f[3] == "keep_nan"))
            delete_nan_count = len(filters) - keep_nan_count

            result_text += f"""

NaN handling strategy statistics:
• Keep NaN strategy: {keep_nan_count} conditions
• Delete NaN strategy: {delete_nan_count} conditions

Filter results:
• Original data: {original_rows:,} rows
• After filtering: {filtered_rows:,} rows  
• Retention rate: {retention_rate:.1f}%
• Removed: {original_rows - filtered_rows:,} rows

Data is ready for further analysis."""

            self.main_window.show_info_message("Filter Success", result_text)

        except Exception as e:
            print(f"[ERROR] Failed to display filter results: {e}")
            self.main_window.show_info_message(
                "Filter Success",
                f"Applied {len(filters)} filter conditions\nOriginal data: {len(original_data)} rows\nFiltered data: {len(filtered_data)} rows"
            )

    def clear_filters(self):
        """Clear all filter conditions"""
        try:
            if self.original_data is not None:
                # Reset to original data
                if hasattr(self.main_window, 'global_data_manager'):
                    success = self.main_window.global_data_manager.reset_to_original()
                else:
                    self.main_window.data_processor.data = self.original_data.copy()
                    self.main_window.data = self.original_data.copy()
                    success = True

                if success:
                    # Clear filter state
                    self.filtered_data = None
                    self.active_filters = []

                    # Update interface
                    self._update_interface()

                    self.main_window.update_status("[OK] Filter conditions cleared")
                    self.main_window.show_info_message("Success", "Restored to original data state")
                else:
                    self.main_window.show_error_message("Error", "Failed to reset to original data")
            else:
                self.main_window.show_info_message("Info", "No filter conditions to clear currently")

        except Exception as e:
            print(f"[ERROR] Error clearing filter conditions: {e}")
            self.main_window.show_error_message("Error", f"Error clearing filter conditions: {str(e)}")

    def get_filter_status(self):
        """Get current filter status"""
        if not self.active_filters:
            return "No filter conditions set"

        status = f"Set {len(self.active_filters)} filter conditions"

        if hasattr(self, 'filtered_data') and self.filtered_data is not None:
            valid_rows = len(self.filtered_data)
            status += f" (Remaining data: {valid_rows} rows)"

        return status

    def has_active_filters(self):
        """Check if there are active filter conditions"""
        return hasattr(self, 'active_filters') and len(self.active_filters) > 0

    def get_filtered_data(self):
        """Get filtered data"""
        try:
            if hasattr(self.main_window, 'global_data_manager'):
                return self.main_window.global_data_manager.get_current_data()
            else:
                if hasattr(self, 'filtered_data') and self.filtered_data is not None:
                    return self.filtered_data
                return None
        except Exception as e:
            print(f"[ERROR] Failed to get filtered data: {e}")
            return None