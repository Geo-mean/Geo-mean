"""
LOWESS Analysis Dialog - geochemistry/lowess_dialog.py
Layout and sizing follow ui/moving_window_dialog.py (SimpleMovingWindowDialog).
"""

import math
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class LowessDialog:
    """LOWESS parameter dialog"""

    def __init__(self, parent, data: pd.DataFrame, numeric_columns: List[str],
                 data_notice: Optional[str] = None,
                 title: str = "LOWESS Analysis"):
        self.parent = parent
        self.data = data
        self.numeric_columns = numeric_columns
        self.data_notice = data_notice          # e.g. warning that data has been gridded
        self.window_title = title
        self.result = None

        self._suggest_thread = None
        self._suggest_result = None

        self.dialog = tk.Toplevel(parent)
        self.setup_window()
        self.init_variables()
        self.create_ui()

    # ------------------------------------------------------------------ window
    def setup_window(self):
        self.dialog.title(self.window_title)
        self.dialog.resizable(True, True)
        self.dialog.grab_set()

        screen_w = self.dialog.winfo_screenwidth()
        screen_h = self.dialog.winfo_screenheight()
        desired_w, desired_h = 650, 760
        max_h = max(int(screen_h * 0.85), 400)
        max_w = max(int(screen_w * 0.9), 500)
        width = min(desired_w, max_w)
        height = min(desired_h, max_h)

        self.dialog.geometry(f"{width}x{height}")
        self.dialog.minsize(min(500, width), min(400, height))
        self.center_window(width, height)
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def center_window(self, width=None, height=None):
        self.dialog.update_idletasks()
        width = width or self.dialog.winfo_width()
        height = height or self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")

    def init_variables(self):
        self.x_column_var = tk.StringVar()
        self.y_column_var = tk.StringVar()
        self.min_x_var = tk.StringVar(value="")
        self.max_x_var = tk.StringVar(value="")
        self.frac_var = tk.DoubleVar(value=0.30)
        self.frac_text_var = tk.StringVar(value="0.30")
        self.robust_var = tk.BooleanVar(value=True)
        self.compute_ci_var = tk.BooleanVar(value=True)
        self.n_boot_var = tk.StringVar(value="500")
        self.ci_level_var = tk.StringVar(value="95")
        self.band_type_var = tk.StringVar(value="percentile")
        self.seed_var = tk.StringVar(value="42")
        self.method_var = tk.StringVar(value="quick")

        self.data_info_var = tk.StringVar(value="")
        self.points_per_fit_var = tk.StringVar(value="")
        self.suggest_info_var = tk.StringVar(value="")

    # ---------------------------------------------------------------------- UI
    def create_ui(self):
        # Buttons first (side=BOTTOM) so the scroll area cannot push them out of view
        self.create_buttons(self.dialog)
        main_frame = self.create_scrollable_area(self.dialog)

        if self.data_notice:
            tk.Label(main_frame, text=self.data_notice, bg='#fef3c7', fg='#92400e',
                     font=('Arial', 9), justify=tk.LEFT, anchor='w',
                     wraplength=540, padx=10, pady=8).pack(fill=tk.X, pady=(0, 15))

        self.create_column_selection(main_frame)
        self.create_x_range_section(main_frame)
        self.create_smoothing_section(main_frame)
        self.create_uncertainty_section(main_frame)

        self.auto_select_columns()
        self.on_columns_changed()

    def create_scrollable_area(self, parent):
        container = tk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        inner_frame = tk.Frame(canvas, padx=25, pady=25)

        inner_frame.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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

    def _section(self, parent, text):
        frame = tk.LabelFrame(parent, text=text, font=('Arial', 10, 'bold'))
        frame.pack(fill=tk.X, pady=(0, 15))
        return frame

    def _hint(self, parent, text=None, textvariable=None):
        tk.Label(parent, text=text, textvariable=textvariable, font=('Arial', 8),
                 fg='#666666', justify=tk.LEFT, anchor='w',
                 wraplength=520).pack(fill=tk.X, padx=10, pady=(0, 6))

    def create_column_selection(self, parent):
        frame = self._section(parent, "Column Selection")
        for label, var in (("X Column:", self.x_column_var), ("Y Column:", self.y_column_var)):
            row = tk.Frame(frame)
            row.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(row, text=label, width=12, anchor='w').pack(side=tk.LEFT)
            combo = ttk.Combobox(row, textvariable=var, values=self.numeric_columns,
                                 state="readonly", width=20)
            combo.pack(side=tk.LEFT, padx=10)
            combo.bind('<<ComboboxSelected>>', lambda e: self.on_columns_changed())
        self._hint(frame, textvariable=self.data_info_var)

    def create_x_range_section(self, parent):
        frame = self._section(parent, "X Range (optional)")
        row = tk.Frame(frame)
        row.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(row, text="Min:").pack(side=tk.LEFT)
        tk.Entry(row, textvariable=self.min_x_var, width=10).pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="Max:").pack(side=tk.LEFT, padx=(15, 0))
        tk.Entry(row, textvariable=self.max_x_var, width=10).pack(side=tk.LEFT, padx=5)
        self._hint(frame, "Leave blank to use the full range of the data.")
        for var in (self.min_x_var, self.max_x_var):
            var.trace_add("write", lambda *a: self.update_data_info())

    def create_smoothing_section(self, parent):
        frame = self._section(parent, "Smoothing")

        row = tk.Frame(frame)
        row.pack(fill=tk.X, padx=10, pady=(10, 2))
        tk.Label(row, text="Span (frac):", width=12, anchor='w').pack(side=tk.LEFT)
        entry = tk.Entry(row, textvariable=self.frac_text_var, width=8)
        entry.pack(side=tk.LEFT, padx=10)
        entry.bind("<Return>", self.on_frac_entry)
        entry.bind("<FocusOut>", self.on_frac_entry)
        tk.Label(row, text="(0 – 1)", fg='#666666').pack(side=tk.LEFT)
        self.suggest_btn = tk.Button(row, text="Suggest", command=self.on_suggest_frac,
                                     bg='#6c757d', fg='white', width=8)
        self.suggest_btn.pack(side=tk.LEFT, padx=5)

        self._hint(frame, textvariable=self.points_per_fit_var)
        self._hint(frame, textvariable=self.suggest_info_var)
        self.frac_text_var.trace_add("write", lambda *a: self.on_frac_typed())

        tk.Checkbutton(frame, text="Robust fitting (down-weight outliers, 3 iterations)",
                       variable=self.robust_var).pack(anchor=tk.W, padx=10, pady=(4, 8))

    def create_uncertainty_section(self, parent):
        frame = self._section(parent, "Uncertainty (bootstrap)")

        tk.Checkbutton(frame, text="Compute confidence band", variable=self.compute_ci_var,
                       command=self.on_toggle_ci).pack(anchor=tk.W, padx=10, pady=(8, 4))

        self.ci_widgets = []
        row = tk.Frame(frame)
        row.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(row, text="Iterations:", width=12, anchor='w').pack(side=tk.LEFT)
        e = tk.Entry(row, textvariable=self.n_boot_var, width=8)
        e.pack(side=tk.LEFT, padx=10)
        tk.Label(row, text="Confidence:").pack(side=tk.LEFT, padx=(15, 0))
        c = ttk.Combobox(row, textvariable=self.ci_level_var, values=["90", "95", "99"],
                         state="readonly", width=5)
        c.pack(side=tk.LEFT, padx=5)
        tk.Label(row, text="%").pack(side=tk.LEFT)
        self.ci_widgets += [e, c]

        row = tk.Frame(frame)
        row.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(row, text="Band type:", width=12, anchor='w').pack(side=tk.LEFT)
        for text, value in (("Percentile interval", "percentile"), ("±2σ", "2sigma")):
            rb = tk.Radiobutton(row, text=text, variable=self.band_type_var, value=value)
            rb.pack(side=tk.LEFT, padx=(10, 0))
            self.ci_widgets.append(rb)

        row = tk.Frame(frame)
        row.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(row, text="Random seed:", width=12, anchor='w').pack(side=tk.LEFT)
        e = tk.Entry(row, textvariable=self.seed_var, width=8)
        e.pack(side=tk.LEFT, padx=10)
        self.ci_widgets.append(e)

        row = tk.Frame(frame)
        row.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(row, text="Calculation:", width=12, anchor='w').pack(side=tk.LEFT)
        for text, value in (("Quick", "quick"), ("Precise", "precise")):
            rb = tk.Radiobutton(row, text=text, variable=self.method_var, value=value)
            rb.pack(side=tk.LEFT, padx=(10, 0))
            self.ci_widgets.append(rb)

        self._hint(frame, "Quick: several times faster bootstrap using an approximation; the LOWESS curve "
                          "itself is always computed exactly and the band differs only slightly. "
                          "Precise: exact fit in every bootstrap run, recommended for final figures.")
        self._hint(frame, "500 iterations are enough while exploring; use 1000 for final figures. "
                          "A fixed seed makes the band reproducible.")

    # ----------------------------------------------------------------- events
    def auto_select_columns(self):
        for candidate in ['AGE', 'AGES', 'YEAR', 'YEARS', 'MA', 'TIME']:
            matches = [c for c in self.numeric_columns if candidate in c.upper()]
            if matches:
                self.x_column_var.set(matches[0])
                break
        for candidate in ['THU', 'TH_U', 'TH/U', 'SIO2']:
            matches = [c for c in self.numeric_columns
                       if candidate in c.upper().replace('/', '_').replace(' ', '_')]
            if matches:
                self.y_column_var.set(matches[0])
                break

    def on_columns_changed(self):
        self.update_data_info()
        self.suggest_info_var.set("")

    def _valid_xy(self):
        """Valid (x, y) pairs for the current column / range selection."""
        x_col, y_col = self.x_column_var.get(), self.y_column_var.get()
        if not x_col or not y_col or x_col == y_col:
            return None, None
        x = np.asarray(pd.to_numeric(self.data[x_col], errors='coerce'), dtype=float)
        y = np.asarray(pd.to_numeric(self.data[y_col], errors='coerce'), dtype=float)
        mask = np.isfinite(x) & np.isfinite(y)
        try:
            if self.min_x_var.get().strip():
                mask &= x >= float(self.min_x_var.get())
            if self.max_x_var.get().strip():
                mask &= x <= float(self.max_x_var.get())
        except ValueError:
            pass
        return x[mask], y[mask]

    def update_data_info(self):
        x, y = self._valid_xy()
        if x is None:
            self.data_info_var.set("")
            self.points_per_fit_var.set("")
            return
        if len(x) == 0:
            self.data_info_var.set("No valid data points for this selection.")
        else:
            self.data_info_var.set(f"Valid points: {len(x)}   |   X range: "
                                   f"{x.min():g} – {x.max():g}")
        self.update_points_per_fit()

    def update_points_per_fit(self):
        x, _ = self._valid_xy()
        if x is None or len(x) == 0:
            self.points_per_fit_var.set("")
            return
        k = math.ceil(self.frac_var.get() * len(x))
        self.points_per_fit_var.set(
            f"Each local fit uses the nearest ≈{k} points (frac × valid points). "
            f"Larger values give a smoother curve.")

    def on_frac_typed(self):
        """Update the point count while typing; ignore incomplete input like '0.'"""
        try:
            value = float(self.frac_text_var.get())
        except ValueError:
            return
        if 0 < value <= 1:
            self.frac_var.set(value)
            self.update_points_per_fit()

    def on_frac_entry(self, event=None):
        try:
            value = float(self.frac_text_var.get())
            if not 0 < value <= 1:
                raise ValueError
            self.frac_var.set(value)
        except ValueError:
            self.frac_text_var.set(f"{self.frac_var.get():.2f}")
        self.update_points_per_fit()

    def on_toggle_ci(self):
        state = tk.NORMAL if self.compute_ci_var.get() else tk.DISABLED
        for w in self.ci_widgets:
            try:
                w.configure(state='readonly' if (state == tk.NORMAL and isinstance(w, ttk.Combobox))
                            else state)
            except tk.TclError:
                pass

    # ------------------------------------------------- frac suggestion (thread)
    def on_suggest_frac(self):
        x, y = self._valid_xy()
        if x is None or len(x) < 20:
            messagebox.showwarning("Suggest", "At least 20 valid points are needed for "
                                              "cross-validation.", parent=self.dialog)
            return
        from geochemistry.lowess_core import suggest_frac

        it = 3 if self.robust_var.get() else 0
        self.suggest_btn.configure(state=tk.DISABLED, text="Running…")
        self.suggest_info_var.set("Running 5-fold cross-validation…")
        self._suggest_result = None

        def worker():
            try:
                self._suggest_result = ("ok", suggest_frac(x, y, it=it))
            except Exception as e:
                self._suggest_result = ("error", str(e))

        self._suggest_thread = threading.Thread(target=worker, daemon=True)
        self._suggest_thread.start()
        self.dialog.after(150, self._poll_suggest)

    def _poll_suggest(self):
        if not self.dialog.winfo_exists():
            return
        if self._suggest_thread is not None and self._suggest_thread.is_alive():
            self.dialog.after(150, self._poll_suggest)
            return
        self.suggest_btn.configure(state=tk.NORMAL, text="Suggest")
        status, payload = self._suggest_result or ("error", "No result")
        if status == "error":
            self.suggest_info_var.set(f"Suggestion failed: {payload}")
            return
        best, table = payload
        self.frac_var.set(best)
        self.frac_text_var.set(f"{best:.2f}")
        self.update_points_per_fit()
        spread = table['cv_mae'].max() / table['cv_mae'].min() - 1
        note = (" Errors differ by less than 5% across candidates, so check the curve "
                "shape visually." if spread < 0.05 else "")
        self.suggest_info_var.set(f"Cross-validation suggests frac = {best:.2f}.{note}")

    # ------------------------------------------------------------- buttons
    def create_buttons(self, parent):
        button_frame = tk.Frame(parent, padx=25, pady=15)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        tk.Button(button_frame, text="Cancel", command=self.on_cancel, width=12,
                  bg='#6c757d', fg='white').pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Start Analysis", command=self.on_confirm, width=12,
                  bg='#007bff', fg='white', font=('Arial', 10, 'bold')
                  ).pack(side=tk.RIGHT, padx=5)

    def validate_parameters(self) -> Tuple[bool, str]:
        x_col, y_col = self.x_column_var.get(), self.y_column_var.get()
        if not x_col:
            return False, 'Please select an X column'
        if not y_col:
            return False, 'Please select a Y column'
        if x_col == y_col:
            return False, 'X column and Y column cannot be the same'
        try:
            min_x = self.min_x_var.get().strip()
            max_x = self.max_x_var.get().strip()
            if min_x and max_x and float(min_x) >= float(max_x):
                return False, 'Minimum X must be less than maximum X'
            frac = float(self.frac_text_var.get())
            if not 0 < frac <= 1:
                return False, 'Span (frac) must be between 0 and 1'
            if self.compute_ci_var.get():
                n_boot = int(self.n_boot_var.get())
                if not 50 <= n_boot <= 10000:
                    return False, 'Bootstrap iterations should be between 50 and 10000'
            if self.seed_var.get().strip():
                int(self.seed_var.get())
        except ValueError:
            return False, 'Please enter valid numeric values'

        x, _ = self._valid_xy()
        if x is None or len(x) < 10:
            return False, 'At least 10 valid data points are required'
        if math.ceil(frac * len(x)) < 5:
            return False, (f'Span too small: each local fit would use fewer than 5 points. '
                           f'Increase frac to at least {5 / len(x):.2f}.')
        return True, 'Parameter validation passed'

    def get_parameters(self) -> Dict:
        min_x = self.min_x_var.get().strip()
        max_x = self.max_x_var.get().strip()
        seed = self.seed_var.get().strip()
        return {
            'x_column': self.x_column_var.get(),
            'y_column': self.y_column_var.get(),
            'min_x': float(min_x) if min_x else None,
            'max_x': float(max_x) if max_x else None,
            'frac': float(self.frac_text_var.get()),
            'it': 3 if self.robust_var.get() else 0,
            'compute_ci': self.compute_ci_var.get(),
            'n_boot': int(self.n_boot_var.get()) if self.compute_ci_var.get() else 0,
            'ci_level': int(self.ci_level_var.get()),
            'band_type': self.band_type_var.get(),
            'seed': int(seed) if seed else None,
            'fast': self.method_var.get() == 'quick',
        }

    def on_confirm(self):
        is_valid, message = self.validate_parameters()
        if not is_valid:
            messagebox.showerror('Parameter Error', message, parent=self.dialog)
            return
        self.result = self.get_parameters()
        self.dialog.destroy()

    def on_cancel(self):
        self.result = None
        self.dialog.destroy()


def show_lowess_dialog(parent, data, numeric_columns, data_notice=None) -> Optional[Dict]:
    """Show the LOWESS dialog and return parameters, or None if cancelled."""
    try:
        dialog = LowessDialog(parent, data, numeric_columns, data_notice)
        parent.wait_window(dialog.dialog)
        return dialog.result
    except Exception as e:
        print(f"[ERROR] Failed to show LOWESS dialog: {e}")
        messagebox.showerror("Error", f"Failed to show dialog: {str(e)}")
        return None