"""
Enhanced Geographic Aggregation Dialog - Supporting Coordinate and Location Aggregation, Removing Preview Function Version
Complete replacement for your ui/geo_aggregation_dialog.py file
"""

import tkinter as tk
import threading
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import math


class EnhancedGeoAggregationDialog:
    """Enhanced Geographic Aggregation Dialog - Supporting Coordinate and Location Aggregation"""

    def __init__(self, parent, data, all_columns, numeric_columns):
        self.parent = parent
        self.data = data
        self.all_columns = all_columns
        self.numeric_columns = numeric_columns
        self.result = None

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Geographic Gridding")
        self.window.transient(parent)
        self.window.grab_set()
        self.window.resizable(True, True)

        # Compute a size that fits within the current screen instead of a
        # hardcoded 900x750, which overflows small/laptop screens.
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()

        desired_w, desired_h = 900, 750
        max_h = max(int(screen_h * 0.85), 400)
        max_w = max(int(screen_w * 0.9), 500)

        self._win_w = min(desired_w, max_w)
        self._win_h = min(desired_h, max_h)

        # Minimum size should never exceed what we just computed, otherwise
        # the user still can't shrink the window on a small screen.
        self.window.minsize(min(600, self._win_w), min(450, self._win_h))

        # Center display
        self._center_window()
        self._setup_ui()
        self._auto_detect_columns()

    def _center_window(self):
        """Center window"""
        self.window.update_idletasks()
        x = self.parent.winfo_rootx() + 20
        y = self.parent.winfo_rooty() + 10
        self.window.geometry(f"{self._win_w}x{self._win_h}+{x}+{y}")

    def _setup_ui(self):
        """Setup interface"""
        # IMPORTANT: pack the button bar FIRST (side=BOTTOM) so it claims
        # its space before the scrollable content area expands to fill the
        # rest. If reversed, the expanding scroll area would push the
        # buttons out of view on small screens.
        self._create_buttons(self.window)

        # Scrollable content area, so nothing gets cut off on small screens
        main_frame = self._create_scrollable_area(self.window)

        # Aggregation mode selection
        self._create_aggregation_mode_selection(main_frame)

        # Column selection
        self._create_column_selection(main_frame)

        # Aggregation options
        self._create_aggregation_options(main_frame)

        # Initially show coordinate mode
        self._on_mode_change()

    def _create_scrollable_area(self, parent):
        """Create a vertically scrollable content area and return the
        inner frame that widgets should be packed into."""
        container = tk.Frame(parent, bg='white')
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner_frame = tk.Frame(canvas, bg='white', padx=20, pady=15)

        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Make the inner frame track the canvas width so content doesn't
        # get clipped horizontally either.
        def _sync_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", _sync_width)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel support (Windows/Mac use <MouseWheel>, Linux uses
        # Button-4/5). Bound only while the pointer is over this canvas.
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_linux(event):
            canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

        canvas.bind("<Enter>", lambda e: (
            canvas.bind_all("<MouseWheel>", _on_mousewheel),
            canvas.bind_all("<Button-4>", _on_mousewheel_linux),
            canvas.bind_all("<Button-5>", _on_mousewheel_linux),
        ))
        canvas.bind("<Leave>", lambda e: (
            canvas.unbind_all("<MouseWheel>"),
            canvas.unbind_all("<Button-4>"),
            canvas.unbind_all("<Button-5>"),
        ))

        return inner_frame

    def _create_aggregation_mode_selection(self, parent):
        """Create aggregation mode selection"""
        mode_frame = tk.LabelFrame(
            parent,
            text="Gridding Mode",
            font=('Arial', 11, 'bold'),
            bg='white',
            fg='#2E86C1',
            padx=12,
            pady=8
        )
        mode_frame.pack(fill=tk.X, pady=(0, 15))

        self.aggregation_mode = tk.StringVar(value="coordinate")

        # Create horizontal layout
        radio_frame = tk.Frame(mode_frame, bg='white')
        radio_frame.pack(fill=tk.X)

        # Coordinate aggregation mode
        coord_radio = tk.Radiobutton(
            radio_frame,
            text="Coordinate Gridding",
            variable=self.aggregation_mode,
            value="coordinate",
            font=('Arial', 10),
            bg='white',
            fg='#2C3E50',
            command=self._on_mode_change
        )
        coord_radio.pack(side=tk.LEFT, padx=(0, 30))

        # Location aggregation mode
        location_radio = tk.Radiobutton(
            radio_frame,
            text="Region Gridding",
            variable=self.aggregation_mode,
            value="location",
            font=('Arial', 10),
            bg='white',
            fg='#2C3E50',
            command=self._on_mode_change
        )
        location_radio.pack(side=tk.LEFT)

    def _create_column_selection(self, parent):
        """Create column selection"""
        self.selection_frame = tk.LabelFrame(
            parent,
            text="Select Data Columns",
            font=('Arial', 12, 'bold'),
            bg='white',
            fg='#2E86C1',
            padx=12,
            pady=10
        )
        self.selection_frame.pack(fill=tk.X, pady=(0, 15))

        # Column selection for coordinate aggregation
        self.coord_selection_frame = tk.Frame(self.selection_frame, bg='white')
        self.coord_selection_frame.pack(fill=tk.X)

        # Latitude column
        tk.Label(self.coord_selection_frame, text="Latitude Column:", font=('Arial', 11), bg='white').grid(
            row=0, column=0, sticky='w', pady=5, padx=(0, 10))
        self.lat_var = tk.StringVar()
        self.lat_combo = ttk.Combobox(self.coord_selection_frame, textvariable=self.lat_var,
                                     values=self.numeric_columns, state="readonly", width=25, font=('Arial', 10))
        self.lat_combo.grid(row=0, column=1, pady=5, sticky='ew')

        # Longitude column
        tk.Label(self.coord_selection_frame, text="Longitude Column:", font=('Arial', 11), bg='white').grid(
            row=1, column=0, sticky='w', pady=5, padx=(0, 10))
        self.lon_var = tk.StringVar()
        self.lon_combo = ttk.Combobox(self.coord_selection_frame, textvariable=self.lon_var,
                                     values=self.numeric_columns, state="readonly", width=25, font=('Arial', 10))
        self.lon_combo.grid(row=1, column=1, pady=5, sticky='ew')

        # Column selection for Location aggregation
        self.location_selection_frame = tk.Frame(self.selection_frame, bg='white')

        # Location column
        tk.Label(self.location_selection_frame, text="Location Column:", font=('Arial', 11), bg='white').grid(
            row=0, column=0, sticky='w', pady=5, padx=(0, 10))
        self.location_var = tk.StringVar()
        self.location_combo = ttk.Combobox(self.location_selection_frame, textvariable=self.location_var,
                                          values=self.all_columns, state="readonly", width=25, font=('Arial', 10))
        self.location_combo.grid(row=0, column=1, pady=5, sticky='ew')

        # Age column (shared by both modes)
        age_frame = tk.Frame(self.selection_frame, bg='white')
        age_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Label(age_frame, text="Age Column:", font=('Arial', 11), bg='white').grid(
            row=0, column=0, sticky='w', pady=5, padx=(0, 10))
        self.age_var = tk.StringVar()
        self.age_combo = ttk.Combobox(age_frame, textvariable=self.age_var,
                                     values=self.numeric_columns, state="readonly", width=25, font=('Arial', 10))
        self.age_combo.grid(row=0, column=1, pady=5, sticky='ew')

        # Configure column weights
        self.coord_selection_frame.columnconfigure(1, weight=1)
        self.location_selection_frame.columnconfigure(1, weight=1)
        age_frame.columnconfigure(1, weight=1)

    def _create_aggregation_options(self, parent):
        """Create aggregation options"""
        self.agg_frame = tk.LabelFrame(
            parent,
            text="Gridding Parameter Settings",
            font=('Arial', 12, 'bold'),
            bg='white',
            fg='#2E86C1',
            padx=12,
            pady=10
        )
        self.agg_frame.pack(fill=tk.X, pady=(0, 15))

        # === Coordinate aggregation settings ===
        self.coord_agg_frame = tk.Frame(self.agg_frame, bg='white')
        self.coord_agg_frame.pack(fill=tk.X)

        # Lat/Lon precision settings
        coord_precision_frame = tk.Frame(self.coord_agg_frame, bg='white')
        coord_precision_frame.pack(fill=tk.X, pady=(0, 15))

        coord_label = tk.Label(coord_precision_frame, text="Lat/Lon Gridding Precision:",
                              font=('Arial', 11, 'bold'), bg='white', fg='#34495E')
        coord_label.pack(anchor='w', pady=(0, 8))

        self.coord_agg_var = tk.StringVar(value="1.0")

        # Preset options
        preset_frame = tk.Frame(coord_precision_frame, bg='white')
        preset_frame.pack(fill=tk.X, padx=15)

        coord_presets = [
            ("1.0", "1° precision (recommended)"),
            ("0.5", "0.5° precision"),
            ("0.1", "0.1° precision"),
            ("custom", "Custom precision")
        ]

        for i, (value, text) in enumerate(coord_presets):
            row = i // 2
            column = i % 2
            tk.Radiobutton(preset_frame, text=text, variable=self.coord_agg_var, value=value,
                          font=('Arial', 10), bg='white', fg='#2C3E50',
                          command=self._on_coord_preset_change).grid(
                row=row, column=column, sticky='w', pady=3, padx=(0, 25))

        # Custom precision input
        custom_coord_frame = tk.Frame(coord_precision_frame, bg='white')
        custom_coord_frame.pack(fill=tk.X, padx=15, pady=(8, 0))

        tk.Label(custom_coord_frame, text="Custom precision (degrees):",
                font=('Arial', 10), bg='white').pack(side=tk.LEFT)

        self.coord_precision_var = tk.DoubleVar(value=1.0)
        self.coord_precision_entry = tk.Entry(custom_coord_frame, textvariable=self.coord_precision_var,
                                             width=12, font=('Arial', 10))
        self.coord_precision_entry.pack(side=tk.LEFT, padx=(8, 15))

        tk.Label(custom_coord_frame, text="Example: 1.0 = 1° grid",
                font=('Arial', 9), bg='white', fg='#666').pack(side=tk.LEFT)

        # === Location aggregation settings ===
        self.location_agg_frame = tk.Frame(self.agg_frame, bg='white')

        location_info_frame = tk.Frame(self.location_agg_frame, bg='white')
        location_info_frame.pack(fill=tk.X, pady=(0, 15))

        location_label = tk.Label(location_info_frame, text="Location Gridding Settings:",
                                 font=('Arial', 11, 'bold'), bg='white', fg='#34495E')
        location_label.pack(anchor='w', pady=(0, 5))

        location_desc = tk.Label(location_info_frame,
                                text="Grid data points with the same Location value, taking average of chemical elements",
                                font=('Arial', 9), bg='white', fg='#666666')
        location_desc.pack(anchor='w', padx=15)

        # === Age aggregation settings (shared by both modes) ===
        self.age_agg_frame = tk.Frame(self.agg_frame, bg='white')
        self.age_agg_frame.pack(fill=tk.X, pady=(15, 0))

        age_label = tk.Label(self.age_agg_frame, text="Age Gridding Settings:",
                            font=('Arial', 11, 'bold'), bg='white', fg='#34495E')
        age_label.pack(anchor='w', pady=(0, 8))

        self.age_agg_var = tk.StringVar(value="10.0")

        # Age preset options
        age_preset_frame = tk.Frame(self.age_agg_frame, bg='white')
        age_preset_frame.pack(fill=tk.X, padx=15)

        age_presets = [
            ("1.0", "1Ma precision"),
            ("5.0", "5Ma precision"),
            ("10.0", "10Ma precision (recommended)"),
            ("custom", "Custom precision")
        ]

        for i, (value, text) in enumerate(age_presets):
            row = i // 2
            column = i % 2
            tk.Radiobutton(age_preset_frame, text=text, variable=self.age_agg_var, value=value,
                          font=('Arial', 10), bg='white', fg='#2C3E50',
                          command=self._on_age_preset_change).grid(
                row=row, column=column, sticky='w', pady=3, padx=(0, 25))

        # Custom age precision input
        custom_age_frame = tk.Frame(self.age_agg_frame, bg='white')
        custom_age_frame.pack(fill=tk.X, padx=15, pady=(8, 0))

        tk.Label(custom_age_frame, text="Custom precision (Ma):",
                font=('Arial', 10), bg='white').pack(side=tk.LEFT)

        self.age_precision_var = tk.DoubleVar(value=10.0)
        self.age_precision_entry = tk.Entry(custom_age_frame, textvariable=self.age_precision_var,
                                           width=12, font=('Arial', 10))
        self.age_precision_entry.pack(side=tk.LEFT, padx=(8, 15))

        tk.Label(custom_age_frame, text="Example: 10 = 10Ma grouping",
                font=('Arial', 9), bg='white', fg='#666').pack(side=tk.LEFT)

        # Age aggregation strategy
        strategy_frame = tk.Frame(self.age_agg_frame, bg='white')
        strategy_frame.pack(fill=tk.X, padx=15, pady=(10, 0))

        tk.Label(strategy_frame, text="Age Gridding Strategy:",
                font=('Arial', 10, 'bold'), bg='white').pack(side=tk.LEFT)

        self.age_strategy_var = tk.StringVar(value="round_nearest")

        strategies = [
            ("round_up", "Round up"),
            ("round_nearest", "Round to nearest")
        ]

        for value, text in strategies:
            tk.Radiobutton(strategy_frame, text=text, variable=self.age_strategy_var, value=value,
                          font=('Arial', 9), bg='white', fg='#2C3E50').pack(side=tk.LEFT, padx=(15, 0))

    def _create_buttons(self, parent):
        """Create buttons, pinned to the bottom of the window"""
        button_frame = tk.Frame(parent, bg='white', padx=20, pady=10)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Start aggregation button
        start_btn = tk.Button(
            button_frame,
            text="Start Gridding",
            command=self._on_start_click,
            bg='#27AE60',
            fg='white',
            padx=35,
            pady=12,
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            cursor='hand2'
        )
        start_btn.pack(side=tk.LEFT)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel_click,
            bg='#E74C3C',
            fg='white',
            padx=35,
            pady=12,
            font=('Arial', 12),
            relief=tk.FLAT,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.RIGHT)

    def _on_mode_change(self):
        """Aggregation mode change event"""
        mode = self.aggregation_mode.get()

        if mode == "coordinate":
            # Show coordinate aggregation related components
            self.coord_selection_frame.pack(fill=tk.X)
            self.location_selection_frame.pack_forget()
            self.coord_agg_frame.pack(fill=tk.X)
            self.location_agg_frame.pack_forget()

            # Update selection frame title
            self.selection_frame.config(text="Select Data Columns - Coordinate Gridding Mode")
            self.agg_frame.config(text="Gridding Parameter Settings - Coordinate Gridding")

        else:  # location
            # Show Location aggregation related components
            self.coord_selection_frame.pack_forget()
            self.location_selection_frame.pack(fill=tk.X)
            self.coord_agg_frame.pack_forget()
            self.location_agg_frame.pack(fill=tk.X)

            # Update selection frame title
            self.selection_frame.config(text="Select Data Columns - Region Gridding Mode")
            self.agg_frame.config(text="Gridding Parameter Settings - Region Gridding")

        # Age aggregation settings always displayed
        self.age_agg_frame.pack(fill=tk.X, pady=(15, 0))

    def _on_coord_preset_change(self):
        """Lat/lon preset option change"""
        preset_values = {
            "1.0": 1.0,
            "0.5": 0.5,
            "0.1": 0.1,
            "custom": self.coord_precision_var.get()
        }

        selected = self.coord_agg_var.get()
        if selected in preset_values:
            if selected != "custom":
                self.coord_precision_var.set(preset_values[selected])

    def _on_age_preset_change(self):
        """Age preset option change"""
        preset_values = {
            "1.0": 1.0,
            "5.0": 5.0,
            "10.0": 10.0,
            "custom": self.age_precision_var.get()
        }

        selected = self.age_agg_var.get()
        if selected in preset_values:
            if selected != "custom":
                self.age_precision_var.set(preset_values[selected])

    def _auto_detect_columns(self):
        """Auto detect columns"""
        print(f"[DEBUG] Starting auto column detection, available numeric columns: {self.numeric_columns}")

        # Detect latitude column
        lat_keywords = ['lat', 'latitude', 'latitude', 'y']
        for col in self.numeric_columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in lat_keywords):
                print(f"[DEBUG] Detected latitude column: {col}")
                self.lat_var.set(col)
                break

        # Detect longitude column
        lon_keywords = ['lon', 'lng', 'longitude', 'longitude', 'x']
        for col in self.numeric_columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in lon_keywords):
                print(f"[DEBUG] Detected longitude column: {col}")
                self.lon_var.set(col)
                break

        # Detect Location column
        location_keywords = ['location', 'place', 'site', 'area', 'region', 'location', 'position', 'area']
        for col in self.all_columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in location_keywords):
                print(f"[DEBUG] Detected Location column: {col}")
                self.location_var.set(col)
                break

        # Detect age column
        age_keywords = ['age', 'ages', 'time', 'ma', 'age', 'year', 'years']
        for col in self.numeric_columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in age_keywords):
                print(f"[DEBUG] Detected age column: {col}")
                self.age_var.set(col)
                break

    def _get_current_precision(self):
        """Get current precision settings"""
        try:
            if self.coord_agg_var.get() == "custom":
                coord_precision = self.coord_precision_var.get()
            else:
                coord_precision = float(self.coord_agg_var.get())

            if self.age_agg_var.get() == "custom":
                age_precision = self.age_precision_var.get()
            else:
                age_precision = float(self.age_agg_var.get())

            return coord_precision, age_precision
        except:
            return 1.0, 10.0

    def _validate_inputs(self):
        """Validate inputs"""
        mode = self.aggregation_mode.get()

        if not self.age_var.get():
            messagebox.showerror("Error", "Please select age column")
            return False

        if mode == "coordinate":
            if not self.lat_var.get():
                messagebox.showerror("Error", "Coordinate Gridding mode: Please select latitude column")
                return False
            if not self.lon_var.get():
                messagebox.showerror("Error", "Coordinate Gridding mode: Please select longitude column")
                return False

            # Check coordinate columns cannot be the same
            columns = [self.lat_var.get(), self.lon_var.get(), self.age_var.get()]
            if len(set(columns)) != 3:
                messagebox.showerror("Error", "Latitude, longitude, and age columns cannot be the same")
                return False

            # Validate coordinate precision values
            try:
                coord_precision, age_precision = self._get_current_precision()
                if coord_precision <= 0 or age_precision <= 0:
                    messagebox.showerror("Error", "Precision values must be greater than 0")
                    return False
            except:
                messagebox.showerror("Error", "Please enter valid numeric values")
                return False

        else:  # location mode
            if not self.location_var.get():
                messagebox.showerror("Error", "Region Gridding mode: Please select Location column")
                return False

            # Check Location column and age column cannot be the same
            if self.location_var.get() == self.age_var.get():
                messagebox.showerror("Error", "Location column and age column cannot be the same")
                return False

            # Validate age precision values
            try:
                age_precision = self.age_precision_var.get()
                if age_precision <= 0:
                    messagebox.showerror("Error", "Age precision must be greater than 0")
                    return False
            except:
                messagebox.showerror("Error", "Please enter valid age precision numeric value")
                return False

        return True

    def _collect_parameters(self):
        """Collect aggregation parameters"""
        mode = self.aggregation_mode.get()

        base_params = {
            'aggregation_mode': mode,
            'age_column': self.age_var.get(),
            'age_precision': self.age_precision_var.get(),
            'age_strategy': self.age_strategy_var.get(),
            'age_preset': self.age_agg_var.get()
        }

        if mode == "coordinate":
            coord_precision, _ = self._get_current_precision()
            base_params.update({
                'latitude_column': self.lat_var.get(),
                'longitude_column': self.lon_var.get(),
                'coord_precision': coord_precision,
                'coord_preset': self.coord_agg_var.get()
            })
        else:  # location mode
            base_params.update({
                'location_column': self.location_var.get()
            })

        return base_params

    def _on_start_click(self):
        """Start aggregation button click"""
        if not self._validate_inputs():
            return

        params = self._collect_parameters()
        self._execute_aggregation(params)

    def _execute_aggregation(self, params):
        """Execute aggregation - 后台线程版本"""
        try:
            progress_window = self._create_progress_window(params)

            def background_work():
                try:
                    # 在后台线程执行聚合计算
                    result = self._perform_aggregation(params)

                    # 在主线程处理结果
                    def handle_completion():
                        try:
                            progress_window.destroy()

                            if result:
                                stats = result['statistics']
                                agg_data = result['aggregated_data']
                                mode = params['aggregation_mode']

                                mode_desc = "Coordinate aggregation" if mode == "coordinate" else "Region aggregation"

                                messagebox.showinfo(
                                    "Aggregation Complete",
                                    f"{mode_desc} complete!\n\n"
                                    f"Original data points: {stats['original_count']:,}\n"
                                    f"Aggregated data points: {stats['aggregated_count']:,}\n"
                                    f"Data compression ratio: {stats['compression_ratio']:.1%}\n"
                                    f"Output columns: {len(agg_data.columns)}\n\n"
                                    f"Age precision: {params['age_precision']}Ma\n"
                                    f"Aggregation successful, data updated to main window"
                                )

                                self.result = result
                                self.window.destroy()
                            else:
                                messagebox.showerror("Error", "Error occurred during aggregation process")

                        except Exception as e:
                            messagebox.showerror("Error", f"Processing result failed: {str(e)}")

                    # 调度到主线程执行
                    self.window.after(0, handle_completion)

                except Exception as e:
                    # 错误处理也要在主线程执行
                    def show_error():
                        progress_window.destroy()
                        messagebox.showerror("Error", f"Aggregation failed: {str(e)}")

                    self.window.after(0, show_error)

            # 启动后台线程
            import threading
            thread = threading.Thread(target=background_work, daemon=True)
            thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start aggregation: {str(e)}")

    def _perform_aggregation(self, params):
        """Execute actual aggregation calculation"""
        try:
            from core.geo_data_processor import EnhancedGeoDataProcessor
            processor = EnhancedGeoDataProcessor()

            mode = params['aggregation_mode']
            if mode == "coordinate":
                return processor.perform_custom_aggregation(self.data, params)
            else:  # location mode
                return processor.perform_location_aggregation(self.data, params)
        except Exception as e:
            print(f"[ERROR] Aggregation calculation failed: {e}")
            raise

    def _create_progress_window(self, params):
        """Create progress window"""
        progress_window = tk.Toplevel(self.window)
        progress_window.title("Processing...")
        progress_window.geometry("400x160")
        progress_window.transient(self.window)
        progress_window.grab_set()

        # Center
        x = self.window.winfo_rootx() + 100
        y = self.window.winfo_rooty() + 200
        progress_window.geometry(f"400x160+{x}+{y}")

        mode = params['aggregation_mode']
        mode_desc = "coordinate aggregation" if mode == "coordinate" else "region aggregation"

        tk.Label(progress_window, text=f"Performing {mode_desc}, please wait...",
                font=('Arial', 11)).pack(expand=True, pady=15)

        if mode == "coordinate":
            detail_text = f"Lat/Lon: {params['coord_precision']}° | Age: {params['age_precision']}Ma"
        else:
            detail_text = f"Location column: {params['location_column']} | Age: {params['age_precision']}Ma"

        tk.Label(progress_window,
                text=detail_text,
                font=('Arial', 9), fg='#666666').pack(pady=(0, 15))

        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start()

        progress_window.update()
        return progress_window

    def _on_cancel_click(self):
        """Cancel button click"""
        self.result = None
        self.window.destroy()


def show_simple_geo_aggregation_dialog(parent, data, all_columns, numeric_columns):
    """
    Show enhanced geographic aggregation dialog - Supporting coordinate and location aggregation
    """
    try:
        dialog = EnhancedGeoAggregationDialog(parent, data, all_columns, numeric_columns)
        parent.wait_window(dialog.window)
        return dialog.result
    except Exception as e:
        print(f"[ERROR] Failed to show geographic aggregation dialog: {e}")
        return None