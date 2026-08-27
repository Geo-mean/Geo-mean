"""
Excel Geochemical Data Analyzer - Main Entry File
Production Version v4.0 - English Only
"""

import sys
import os
import tkinter as tk

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)


def setup_matplotlib():
    """Setup matplotlib backend"""
    try:
        import matplotlib
        matplotlib.use('TkAgg', force=True)
        return True
    except Exception:
        return False


def main():
    """Main function"""
    try:
        # Setup matplotlib
        setup_matplotlib()

        # Skip language selection - force English
        try:
            from config.languages import language_manager
            # Force set to English
            language_manager.set_language("en_US")
            print("[INFO] Language set to English (forced)")
        except Exception as e:
            print(f"[WARNING] Failed to set language: {e}")

        # Create main window
        from ui.main_window_i18n import ModernExcelAnalyzerGUI

        root = tk.Tk()
        app = ModernExcelAnalyzerGUI(root)

        # Setup program exit handler
        def on_closing():
            try:
                if hasattr(app, 'chart_controller'):
                    app.chart_controller.close_all_charts()

                import matplotlib.pyplot as plt
                plt.close('all')

                root.quit()
                root.destroy()
            except Exception:
                root.quit()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Center window
        try:
            root.update_idletasks()
            width = root.winfo_width()
            height = root.winfo_height()
            x = (root.winfo_screenwidth() // 2) - (width // 2)
            y = (root.winfo_screenheight() // 2) - (height // 2)
            root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            pass

        print("[INFO] Program started successfully!")
        print("[INFO] Production Version v4.0 - English Only")

        # Start main loop
        root.mainloop()

    except Exception as e:
        print(f"[ERROR] Program startup failed: {str(e)}")
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Startup Error", f"Program startup failed:\n{str(e)}")
        except Exception:
            print(f"Startup failed: {str(e)}")

    finally:
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except:
            pass


if __name__ == "__main__":
    main()