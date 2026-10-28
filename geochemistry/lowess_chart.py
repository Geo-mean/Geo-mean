"""
LOWESS chart window - geochemistry/lowess_chart.py
Same window layout as ChartController (chart on the left, axis control panel on the right).
Draws the data points, the LOWESS curve and (optionally) its confidence band.
"""

import tkinter as tk

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from ui.chart_controller import apply_scientific_journal_style

CURVE_COLOR = '#A4262C'
BAND_COLOR = '#D9868A'
POINT_EDGE = '#B5B5B5'


def show_lowess_chart(main_window, points: pd.DataFrame, result: pd.DataFrame, params: dict):
    """
    points   DataFrame with columns [x_column, y_column] (valid points used in the fit)
    result   output of lowess_bootstrap()
    """
    x_col, y_col = params['x_column'], params['y_column']
    root = main_window.root

    win = tk.Toplevel(root)
    win.title(f"[Scientific] LOWESS - {x_col} vs {y_col}")
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    w, h = min(1350, int(sw * 0.9)), min(750, int(sh * 0.85))
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
    win.minsize(min(800, w), min(500, h))
    win.configure(bg='white')
    win.lift()
    win.attributes('-topmost', True)
    win.after(100, lambda: win.attributes('-topmost', False))
    if hasattr(main_window, 'chart_controller'):
        main_window.chart_controller.chart_windows.append(win)

    # ---- top bar: parameter summary
    top = tk.Frame(win, bg='white')
    top.pack(fill=tk.X, padx=10, pady=(10, 5))
    tk.Label(top, text=_summary_text(points, params), bg='white', fg='#666666',
             font=('Arial', 9)).pack(side=tk.RIGHT)

    body = tk.Frame(win, bg='white')
    body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    chart_box = tk.Frame(body, bg='white', relief=tk.RIDGE, bd=1)
    chart_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    control_box = tk.Frame(body, bg='#f8f9fa', width=330)
    control_box.pack(side=tk.RIGHT, fill=tk.Y)
    control_box.pack_propagate(False)

    # ---- figure (Figure instead of pyplot, so closed windows release memory)
    fig = Figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    apply_scientific_journal_style(fig, ax)
    draw_lowess(ax, points, result, params)

    label = getattr(main_window.chart_controller, '_get_axis_label', lambda c: c)
    ax.set_xlabel(label(x_col), fontsize=12, fontweight='bold')
    ax.set_ylabel(label(y_col), fontsize=12, fontweight='bold')
    ax.set_title(f"{x_col} vs {y_col} (LOWESS)", fontweight='bold', fontsize=14, pad=20)
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, chart_box)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    tb_frame = tk.Frame(chart_box)
    tb_frame.pack(fill=tk.X)
    NavigationToolbar2Tk(canvas, tb_frame).update()

    # ---- reuse existing axis length controller if present
    try:
        from interactive.axis_length_control import AxisLengthController
        try:
            from config.languages import language_manager
            text = language_manager.get_text
        except Exception:
            text = lambda key, default: default

        # header: title + show/hide button (same behaviour as ChartController)
        header = tk.Frame(control_box, bg='#f8f9fa', height=40)
        header.pack(fill=tk.X, padx=5, pady=5)
        header.pack_propagate(False)
        content = tk.Frame(control_box, bg='#f8f9fa')
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        title = tk.Label(header, text=f"[Control] {text('axis_length_control', '轴长度控制')}",
                         bg='#f8f9fa', font=('Arial', 12, 'bold'), fg='#1e40af')
        visible = tk.BooleanVar(value=True)

        def toggle():
            if visible.get():
                content.pack_forget()
                title.pack_forget()
                toggle_btn.config(text=f"< {text('show_control', '显示控制')}")
                control_box.config(width=100)
                visible.set(False)
            else:
                title.pack(side=tk.LEFT, padx=5, pady=5)
                content.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
                toggle_btn.config(text=f"> {text('hide_control', '隐藏控制')}")
                control_box.config(width=330)
                visible.set(True)

        toggle_btn = tk.Button(header, text=f"> {text('hide_control', '隐藏控制')}",
                               command=toggle, bg='#3b82f6', fg='white', relief='flat',
                               font=('Arial', 9), cursor='hand2')
        toggle_btn.pack(side=tk.RIGHT, padx=(0, 5), pady=5)
        title.pack(side=tk.LEFT, padx=5, pady=5)

        canvas.axis_controller = AxisLengthController(content, ax, canvas, points, x_col, y_col)
    except Exception as e:
        print(f"[WARNING] Axis controller unavailable for LOWESS chart: {e}")
        control_box.pack_forget()

    return win


def draw_lowess(ax, points, result, params):
    x_col, y_col = params['x_column'], params['y_column']

    ax.scatter(points[x_col], points[y_col], s=28, facecolors='none',
               edgecolors=POINT_EDGE, linewidths=0.8, zorder=1, label='Data')

    if params.get('n_boot', 0) > 0:
        if params.get('band_type') == '2sigma':
            lo = result['y_fit'] - 2 * result['boot_sd']
            hi = result['y_fit'] + 2 * result['boot_sd']
            band_label = 'LOWESS ±2σ'
        else:
            lo, hi = result['ci_low'], result['ci_high']
            band_label = f"{params.get('ci_level', 95)}% CI"
        ax.fill_between(result['x'], lo, hi, color=BAND_COLOR, alpha=0.35,
                        linewidth=0, zorder=2, label=band_label)

    ax.plot(result['x'], result['y_fit'], color=CURVE_COLOR, lw=2.5, zorder=3,
            label=f"LOWESS (frac={params['frac']:.2f})")

    ax.legend(loc='best', frameon=True, fontsize=9)


def _summary_text(points, params):
    parts = [f"n = {len(points)}", f"frac = {params['frac']:.2f}",
             "robust" if params['it'] > 0 else "non-robust"]
    if params.get('n_boot', 0) > 0:
        band = '±2σ' if params['band_type'] == '2sigma' else f"{params['ci_level']}% CI"
        method = 'quick' if params.get('fast') else 'precise'
        parts.append(f"bootstrap = {params['n_boot']} ({band}, {method})")
    if params.get('_elapsed') is not None:
        parts.append(f"time = {params['_elapsed']:.1f} s")
    return "  |  ".join(parts)
