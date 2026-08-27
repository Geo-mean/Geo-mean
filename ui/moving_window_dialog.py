"""
Simple Moving Window Analysis Dialog - English Version
Removed all complex features, keeping only core parameter settings
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Tuple


class SimpleMovingWindowDialog:
    """Simple Moving Window Analysis Dialog"""

    def __init__(self, parent, numeric_columns: List[str], title: str = "Moving Window Analysis"):
        self.parent = parent
        self.numeric_columns = numeric_columns
        self.result = None
        self.window_title = title

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.setup_window()

        # Initialize variables
        self.init_variables()

        # Create interface
        self.create_ui()

    def setup_window(self):
        """Setup window properties"""
        self.dialog.title(self.window_title)
        self.dialog.resizable(True, True)
        self.dialog.grab_set()

        # Compute a size that fits within the current screen instead of a
        # hardcoded 650x700 that can overflow small/laptop screens.
        screen_w = self.dialog.winfo_screenwidth()
        screen_h = self.dialog.winfo_screenheight()

        desired_w, desired_h = 650, 700
        # Leave room for the taskbar/window chrome (~90px is a safe margin).
        max_h = max(int(screen_h * 0.85), 400)
        max_w = max(int(screen_w * 0.9), 500)

        width = min(desired_w, max_w)
        height = min(desired_h, max_h)

        self.dialog.geometry(f"{width}x{height}")
        # Minimum size should never exceed what we just computed, otherwise
        # the user still can't shrink the window on a small screen.
        self.dialog.minsize(min(500, width), min(400, height))

        # Center window
        self.center_window(width, height)

    def center_window(self, width=None, height=None):
        """Center the window"""
        self.dialog.update_idletasks()
        width = width or self.dialog.winfo_width()
        height = height or self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def init_variables(self):
        """Initialize variables"""
        self.age_column_var = tk.StringVar()
        self.target_column_var = tk.StringVar()
        self.min_age_var = tk.StringVar(value="")
        self.max_age_var = tk.StringVar(value="")
        self.window_size_var = tk.StringVar(value="")
        self.step_size_var = tk.StringVar(value="")
        self.boundary_mode_var = tk.StringVar(value="exclusive")
        self.analysis_method_var = tk.StringVar(value="quick")
        self.min_samples_var = tk.StringVar(value="5")

    def create_ui(self):
        """Create user interface"""
        # IMPORTANT: pack the button bar FIRST (side=BOTTOM) so it claims
        # its space at the bottom of the window. Only after that do we pack
        # the scrollable area (side=TOP, expand=True) to fill whatever
        # space remains. If this were reversed, the expanding scroll area
        # would consume the entire window and push the buttons out of view.
        self.create_buttons(self.dialog)

        # Scrollable area for the parameter sections, so content is never
        # cut off on small screens.
        main_frame = self.create_scrollable_area(self.dialog)

        # 1. Column selection
        self.create_column_selection(main_frame)

        # 2. Age range settings
        self.create_age_range_section(main_frame)

        # 3. Window parameters
        self.create_window_parameters(main_frame)

        # 4. Boundary mode selection
        self.create_boundary_mode(main_frame)

        # 5. Minimum sample size settings
        self.create_min_samples_section(main_frame)

        # 6. Analysis method selection
        self.create_analysis_method(main_frame)

        # Auto-select columns
        self.auto_select_columns()

    def create_scrollable_area(self, parent):
        """Create a vertically scrollable content area and return the
        inner frame that widgets should be packed into."""
        container = tk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner_frame = tk.Frame(canvas, padx=25, pady=25)

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
        # Button-4/5). Bound only to this dialog's canvas.
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

    def create_column_selection(self, parent):
        """Create column selection area"""
        frame = tk.LabelFrame(parent, text="Column Selection", font=('Arial', 10, 'bold'))
        frame.pack(fill=tk.X, pady=(0, 15))

        # Age column
        age_frame = tk.Frame(frame)
        age_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(age_frame, text="X Column:", width=12, anchor='w').pack(side=tk.LEFT)
        age_combo = ttk.Combobox(
            age_frame,
            textvariable=self.age_column_var,
            values=self.numeric_columns,
            state="readonly",
            width=20
        )
        age_combo.pack(side=tk.LEFT, padx=10)

        # Target column
        target_frame = tk.Frame(frame)
        target_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(target_frame, text="Y Column:", width=12, anchor='w').pack(side=tk.LEFT)
        target_combo = ttk.Combobox(
            target_frame,
            textvariable=self.target_column_var,
            values=self.numeric_columns,
            state="readonly",
            width=20
        )
        target_combo.pack(side=tk.LEFT, padx=10)

    def create_age_range_section(self, parent):
        """Create age range settings area"""
        frame = tk.LabelFrame(parent, text="Window Range", font=('Arial', 10, 'bold'))
        frame.pack(fill=tk.X, pady=(0, 15))

        range_frame = tk.Frame(frame)
        range_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(range_frame, text="Minimum:", width=10, anchor='w').pack(side=tk.LEFT)
        tk.Entry(range_frame, textvariable=self.min_age_var, width=10).pack(side=tk.LEFT, padx=5)

        tk.Label(range_frame, text="Maximum:", width=10, anchor='w').pack(side=tk.LEFT, padx=(20, 0))
        tk.Entry(range_frame, textvariable=self.max_age_var, width=10).pack(side=tk.LEFT, padx=5)

    def create_window_parameters(self, parent):
        """Create window parameters area"""
        frame = tk.LabelFrame(parent, text="Window Parameters", font=('Arial', 10, 'bold'))
        frame.pack(fill=tk.X, pady=(0, 15))

        # Window size
        size_frame = tk.Frame(frame)
        size_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(size_frame, text="Window Size:", width=12, anchor='w').pack(side=tk.LEFT)
        tk.Entry(size_frame, textvariable=self.window_size_var, width=10).pack(side=tk.LEFT, padx=10)

        # Step size
        step_frame = tk.Frame(frame)
        step_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(step_frame, text="Step Size:", width=12, anchor='w').pack(side=tk.LEFT)
        tk.Entry(step_frame, textvariable=self.step_size_var, width=10).pack(side=tk.LEFT, padx=10)

    def create_boundary_mode(self, parent):
        """Create boundary mode selection area"""
        frame = tk.LabelFrame(parent, text="Boundary Processing Mode", font=('Arial', 10, 'bold'))
        frame.pack(fill=tk.X, pady=(0, 15))

        mode_frame = tk.Frame(frame)
        mode_frame.pack(fill=tk.X, padx=10, pady=10)

        modes = [
            ("exclusive", "Exclusive Mode"),
            ("inclusive", "Inclusive Mode"),
            ("left_priority", "Left Priority"),
            ("right_priority", "Right Priority"),
            ("weighted_overlap", "Weighted Overlap")
        ]

        tk.Label(mode_frame, text="Mode:", width=12, anchor='w').pack(side=tk.LEFT)
        mode_combo = ttk.Combobox(
            mode_frame,
            textvariable=self.boundary_mode_var,
            values=[f"{desc}" for value, desc in modes],
            state="readonly",
            width=15
        )
        mode_combo.pack(side=tk.LEFT, padx=10)
        mode_combo.set("Exclusive Mode")

        # Bind mode change event
        mode_combo.bind('<<ComboboxSelected>>', self.on_mode_change)

    def create_min_samples_section(self, parent):
        """Create minimum sample size settings area"""
        frame = tk.LabelFrame(parent, text="Sample Size Requirements", font=('Arial', 10, 'bold'))
        frame.pack(fill=tk.X, pady=(0, 15))

        content_frame = tk.Frame(frame)
        content_frame.pack(fill=tk.X, padx=15, pady=15)

        # Minimum sample size setting
        samples_frame = tk.Frame(content_frame)
        samples_frame.pack(fill=tk.X, pady=5)

        tk.Label(samples_frame, text="Min Samples:", width=12, anchor='w').pack(side=tk.LEFT)

        # Sample size input box
        samples_entry = tk.Entry(samples_frame, textvariable=self.min_samples_var, width=8)
        samples_entry.pack(side=tk.LEFT, padx=10)

        # Help label
        help_label = tk.Label(
            samples_frame,
            text="(Windows with fewer samples will be skipped)",
            font=('Arial', 8),
            fg='#666666'
        )
        help_label.pack(side=tk.LEFT, padx=10)

    def create_analysis_method(self, parent):
        """Create analysis method selection area"""
        frame = tk.LabelFrame(parent, text="Analysis Method", font=('Arial', 10, 'bold'))
        frame.pack(fill=tk.X, pady=(0, 20))

        method_frame = tk.Frame(frame)
        method_frame.pack(fill=tk.X, padx=15, pady=15)

        # Radio buttons
        tk.Radiobutton(
            method_frame,
            text="Quick Analysis (Simple Statistics)",
            variable=self.analysis_method_var,
            value="quick",
            font=('Arial', 9)
        ).pack(anchor=tk.W, pady=3)

        tk.Radiobutton(
            method_frame,
            text="Bootstrap Analysis (High Precision Statistics)",
            variable=self.analysis_method_var,
            value="bootstrap",
            font=('Arial', 9)
        ).pack(anchor=tk.W, pady=3)

    def create_buttons(self, parent):
        """Create bottom buttons, pinned to the bottom of the window"""
        button_frame = tk.Frame(parent, padx=25, pady=15)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=self.on_cancel,
            width=12,
            bg='#6c757d',
            fg='white'
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

        # Start analysis button
        confirm_btn = tk.Button(
            button_frame,
            text="Start Analysis",
            command=self.on_confirm,
            width=12,
            bg='#007bff',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        confirm_btn.pack(side=tk.RIGHT, padx=5)

    def auto_select_columns(self):
        """Auto-select appropriate columns"""
        # Age column candidates
        age_candidates = ['AGE', 'AGES', 'YEAR', 'YEARS', 'MA', 'TIME']
        for candidate in age_candidates:
            matches = [col for col in self.numeric_columns if candidate in col.upper()]
            if matches:
                self.age_column_var.set(matches[0])
                break

        # Target column candidates
        target_candidates = ['THU', 'TH_U', 'TH/U', 'SIO2']
        for candidate in target_candidates:
            matches = [col for col in self.numeric_columns
                      if candidate in col.upper().replace('/', '_').replace(' ', '_')]
            if matches:
                self.target_column_var.set(matches[0])
                break

    def on_mode_change(self, event=None):
        """Handle boundary mode change"""
        # Map display text back to internal values
        mode_mapping = {
            "Exclusive Mode": "exclusive",
            "Inclusive Mode": "inclusive",
            "Left Priority": "left_priority",
            "Right Priority": "right_priority",
            "Weighted Overlap": "weighted_overlap"
        }

        selected_display = event.widget.get()
        actual_value = mode_mapping.get(selected_display, "exclusive")
        self.boundary_mode_var.set(actual_value)

    def validate_parameters(self) -> Tuple[bool, str]:
        """Validate parameters"""
        if not self.age_column_var.get():
            return False, 'Please select an age column'

        if not self.target_column_var.get():
            return False, 'Please select a target column'

        if self.age_column_var.get() == self.target_column_var.get():
            return False, 'Age column and target column cannot be the same'

        try:
            min_age = float(self.min_age_var.get())
            max_age = float(self.max_age_var.get())
            window_size = float(self.window_size_var.get())
            step_size = float(self.step_size_var.get())
            min_samples = int(self.min_samples_var.get())

            if min_age >= max_age:
                return False, 'Minimum age must be less than maximum age'

            if window_size <= 0:
                return False, 'Window size must be greater than 0'

            if step_size <= 0:
                return False, 'Step size must be greater than 0'

            if window_size >= (max_age - min_age):
                return False, 'Window size cannot be greater than or equal to age range'

            if min_samples <= 0:
                return False, 'Minimum sample size must be greater than 0'

            if min_samples > 100:
                return False, 'Minimum sample size should not exceed 100'

        except ValueError:
            return False, 'Please enter valid numeric values'

        return True, 'Parameter validation passed'

    def get_parameters(self) -> Dict:
        """Get analysis parameters"""
        params = {
            'age_column': self.age_column_var.get(),
            'target_column': self.target_column_var.get(),
            'min_age': float(self.min_age_var.get()),
            'max_age': float(self.max_age_var.get()),
            'window_size': float(self.window_size_var.get()),
            'step_size': float(self.step_size_var.get()),
            'boundary_mode': self.boundary_mode_var.get(),
            'analysis_method': self.analysis_method_var.get(),
            'min_samples': int(self.min_samples_var.get()),
            'estimated_windows': int((float(self.max_age_var.get()) - float(self.min_age_var.get())) / float(self.step_size_var.get())) + 1,

            # Boundary processing parameters - simplified
            'enable_boundary_comparison': False,
            'highlight_boundary_points': True,
            'export_boundary_info': True,

            # Disable complex features
            'enable_geochem_filter': False,
            'enable_outlier_removal': False,
        }

        return params

    def on_confirm(self):
        """Confirm button event"""
        is_valid, message = self.validate_parameters()

        if not is_valid:
            messagebox.showerror('Parameter Error', message)
            return

        # Additional check: give sample size recommendations based on analysis method
        min_samples = int(self.min_samples_var.get())
        analysis_method = self.analysis_method_var.get()

        warning_messages = []

        if analysis_method == "quick" and min_samples > 10:
            warning_messages.append("High minimum sample size may be unnecessary for quick analysis")

        if analysis_method == "bootstrap" and min_samples < 5:
            warning_messages.append("Bootstrap analysis recommends at least 5 samples for statistical reliability")

        # If there are warnings, ask user whether to continue
        if warning_messages:
            warning_text = "Parameter Recommendations:\n\n" + "\n".join(f"• {msg}" for msg in warning_messages)
            warning_text += "\n\nContinue with current settings?"

            if not messagebox.askyesno('Parameter Recommendations', warning_text):
                return

        self.result = self.get_parameters()
        self.dialog.destroy()

    def on_cancel(self):
        """Cancel button event"""
        self.result = None
        self.dialog.destroy()

    def get_result(self):
        """Get dialog result"""
        return self.result


# Export function - maintain original function name for compatibility
def show_enhanced_moving_window_dialog(parent, numeric_columns: List[str], title: str = "Moving Window Analysis") -> Optional[Dict]:
    """Show simple moving window analysis dialog"""
    try:
        dialog = SimpleMovingWindowDialog(parent, numeric_columns, title=title)
        parent.wait_window(dialog.dialog)
        return dialog.get_result()
    except Exception as e:
        print(f"[ERROR] Failed to show moving window dialog: {e}")
        messagebox.showerror("Error", f"Failed to show dialog: {str(e)}")
        return None


# Test code
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    test_columns = ['AGE', 'SiO2', 'ThU', 'Lg_NbTh', 'Lg_Th', 'LOI', 'TiO2', 'Al2O3']

    result = show_enhanced_moving_window_dialog(root, test_columns)

    if result:
        print("Analysis parameters:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        print(f"\nSpecial note - minimum samples: {result.get('min_samples', 'Not set')}")
    else:
        print("User cancelled analysis")

    root.destroy()