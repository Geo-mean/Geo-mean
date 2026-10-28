"""
LOWESS integration - geochemistry/lowess_integration.py
Glue between the main window and the LOWESS modules, so main_window_i18n.py only needs
one menu entry.
"""

import threading
import time
import numpy as np
import pandas as pd

try:
    import statsmodels  # noqa: F401  LOWESS 依赖；未安装时菜单项不显示
    LOWESS_AVAILABLE = True
except ImportError:
    LOWESS_AVAILABLE = False

# --------------------------------------------------------------------- run
def run_lowess_analysis(main_window):
    """Entry point for the LOWESS button."""
    if getattr(main_window, '_lowess_running', False):
        main_window.show_warning_message('Warning', 'A LOWESS analysis is already running.')
        return
    try:
        is_valid, message = main_window.data_manager.validate_data_for_operation()
        if not is_valid:
            main_window.show_warning_message('Warning', message)
            return

        gdm = main_window.global_data_manager
        data = gdm.get_current_data()
        numeric_columns = gdm.get_numeric_columns()
        if data is None or len(numeric_columns) < 2:
            main_window.show_warning_message('Warning',
                                             'At least 2 numeric columns required for analysis')
            return

        from geochemistry.lowess_dialog import show_lowess_dialog
        params = show_lowess_dialog(main_window.root, data, numeric_columns)
        if not params:
            return

        _start(main_window, data, params)

    except Exception as e:
        import traceback
        traceback.print_exc()
        main_window.show_error_message('Error', f"LOWESS analysis failed: {e}")


def _select_points(data, params):
    x_col, y_col = params['x_column'], params['y_column']
    pts = pd.DataFrame({
        x_col: pd.to_numeric(data[x_col], errors='coerce'),
        y_col: pd.to_numeric(data[y_col], errors='coerce'),
    }).dropna()
    if params['min_x'] is not None:
        pts = pts[pts[x_col] >= params['min_x']]
    if params['max_x'] is not None:
        pts = pts[pts[x_col] <= params['max_x']]
    return pts.reset_index(drop=True)


def _start(main_window, data, params):
    from geochemistry.lowess_core import lowess_bootstrap

    points = _select_points(data, params)
    state = {'done': 0, 'total': params['n_boot'], 'result': None, 'error': None}

    def progress(i, n):
        state['done'] = i            # plain attribute write; read by the Tk polling loop

    def worker():
        try:
            state['result'] = lowess_bootstrap(
                points[params['x_column']], points[params['y_column']],
                frac=params['frac'], it=params['it'], n_boot=params['n_boot'],
                ci=params['ci_level'], seed=params['seed'], progress=progress,
                fast=params.get('fast', False))
        except Exception as e:
            state['error'] = str(e)

    main_window._lowess_running = True
    t_start = time.time()
    main_window.update_status("[LOWESS] Fitting…")
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    def poll():
        if thread.is_alive():
            if state['total'] > 0:
                main_window.update_status(
                    f"[LOWESS] Bootstrap {state['done']}/{state['total']}")
            main_window.root.after(200, poll)
            return
        main_window._lowess_running = False
        if state['error']:
            main_window.update_status("Ready")
            main_window.show_error_message('Error', f"LOWESS analysis failed: {state['error']}")
            return
        params['_elapsed'] = time.time() - t_start
        _finish(main_window, points, state['result'], params)

    main_window.root.after(200, poll)


def _finish(main_window, points, result, params):
    from geochemistry.lowess_chart import show_lowess_chart

    main_window.lowess_results = {'result': result, 'params': params}
    show_lowess_chart(main_window, points, result, params)
    main_window.update_status(
        f"[LOWESS] Complete: {params['x_column']} vs {params['y_column']}, "
        f"{len(points)} points, frac = {params['frac']:.2f}")
