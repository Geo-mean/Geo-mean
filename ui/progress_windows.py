"""
Progress Window Module - English Version
Responsible for displaying loading and analysis progress
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time


class ModernProgressWindow:
    """Modern Progress Window - Fixed version, removed default initialization text"""

    def __init__(self, parent, title=None):
        self.parent = parent
        self.cancelled = False
        self.title = title or 'Loading File...'

        self.create_window()
        self.create_widgets()

    def create_window(self):
        """Create window"""
        self.root = tk.Toplevel(self.parent)
        self.root.title(self.title)
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        # Center window
        self.center_window()

        # Set window properties
        self.root.transient(self.parent)
        self.root.grab_set()

        # Disable close button
        self.root.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def center_window(self):
        """Center window"""
        self.root.update_idletasks()
        width = 500
        height = 300
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """Create interface components"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text=self.title,
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='#2563eb'
        )
        title_label.pack(pady=(0, 20))

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='indeterminate'
        )
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.start(10)  # Start animation

        # Status label - Fixed: completely hide status text
        self.status_var = tk.StringVar()
        self.status_var.set("")  # Set to empty string, show no text

        self.status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            font=('Arial', 10),
            bg='white',
            fg='#666666',
            wraplength=400,
            height=0  # Set height to 0, completely hide
        )
        # Don't show status label
        # self.status_label.pack(pady=(0, 20))  # Comment out this line

        # Cancel button
        self.cancel_button = tk.Button(
            main_frame,
            text='Cancel',
            command=self.on_cancel,
            bg='#dc2626',
            fg='white',
            font=('Arial', 10),
            padx=20,
            pady=5,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.cancel_button.pack()

    def update_status(self, message):
        """Update status message - Fixed: don't show any text"""
        try:
            if not self.cancelled:
                # Don't update status text, keep empty
                # self.status_var.set(message)  # Comment out this line
                self.root.update_idletasks()
        except:
            pass

    def update_progress(self, message_or_value):
        """Update progress - Fixed: only update progress bar, don't show text"""
        try:
            if not self.cancelled:
                # Only update progress value, don't show any text
                if isinstance(message_or_value, (int, float)):
                    self.progress_var.set(message_or_value)
                # Ignore string messages, don't show any text

                self.root.update_idletasks()
        except:
            pass

    def on_cancel(self):
        """Cancel operation"""
        try:
            result = messagebox.askyesno(
                'Confirm Cancel',
                'Are you sure you want to cancel file loading?'
            )
            if result:
                self.cancelled = True
                self.close()
        except:
            self.cancelled = True
            self.close()

    def close(self):
        """Close window"""
        try:
            self.progress_bar.stop()
            self.root.destroy()
        except:
            pass


class ModernAnalysisProgressWindow:
    """Modern Analysis Progress Window - Full multilingual support"""

    def __init__(self, parent, total_windows):
        self.parent = parent
        self.total_windows = total_windows
        self.cancelled = False
        self.current_window = 0
        self.valid_windows = 0

        self.create_window()
        self.create_widgets()

    def create_window(self):
        """Create window"""
        self.root = tk.Toplevel(self.parent)
        self.root.title('Moving Window Analysis Progress')
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        # Center window
        self.center_window()

        # Set window properties
        self.root.transient(self.parent)
        self.root.grab_set()

        # Disable close button
        self.root.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def center_window(self):
        """Center window"""
        self.root.update_idletasks()
        width = 600
        height = 450
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """Create interface components"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text='Moving Window Analysis in Progress',
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='#2563eb'
        )
        title_label.pack(pady=(0, 20))

        # Progress info frame
        info_frame = tk.Frame(main_frame, bg='white')
        info_frame.pack(fill=tk.X, pady=(0, 20))

        # Total progress
        self.total_progress_var = tk.DoubleVar()
        self.total_progress_bar = ttk.Progressbar(
            info_frame,
            variable=self.total_progress_var,
            maximum=100,
            length=500
        )
        self.total_progress_bar.pack(pady=(0, 10))

        # Progress label
        self.progress_label_var = tk.StringVar()
        self.progress_label_var.set(f"Progress: 0/{self.total_windows} Windows")

        progress_label = tk.Label(
            info_frame,
            textvariable=self.progress_label_var,
            font=('Arial', 12),
            bg='white',
            fg='#333333'
        )
        progress_label.pack(pady=(0, 10))

        # Current status frame
        status_frame = tk.LabelFrame(
            main_frame,
            text='Current Processing Status',
            font=('Arial', 12, 'bold'),
            bg='white'
        )
        status_frame.pack(fill=tk.X, pady=(0, 20))

        # Current window info - Fixed: use friendlier initial status
        self.current_window_var = tk.StringVar()
        self.current_window_var.set("Preparing to start analysis...")

        current_window_label = tk.Label(
            status_frame,
            textvariable=self.current_window_var,
            font=('Arial', 10),
            bg='white',
            fg='#666666',
            wraplength=500,
            justify=tk.LEFT
        )
        current_window_label.pack(padx=10, pady=10)

        # Statistics info frame
        stats_frame = tk.LabelFrame(
            main_frame,
            text='Bootstrap Statistics',
            font=('Arial', 12, 'bold'),
            bg='white'
        )
        stats_frame.pack(fill=tk.X, pady=(0, 20))

        # Statistics label
        self.stats_var = tk.StringVar()
        self.stats_var.set(f"""Total Windows: {self.total_windows}
Valid Windows: 0
Bootstrap Sampling: 10,000 resamples per valid window""")

        stats_label = tk.Label(
            stats_frame,
            textvariable=self.stats_var,
            font=('Arial', 10),
            bg='white',
            fg='#333333',
            justify=tk.LEFT
        )
        stats_label.pack(padx=10, pady=10, anchor=tk.W)

        # Button frame
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(fill=tk.X)

        # Cancel button
        self.cancel_button = tk.Button(
            button_frame,
            text='Cancel Analysis',
            command=self.on_cancel,
            bg='#dc2626',
            fg='white',
            font=('Arial', 10),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        self.cancel_button.pack(side=tk.RIGHT)

    def update_progress(self, window_center, sample_count, mean_value, success, message=None):
        """Update analysis progress - English support"""
        try:
            if self.cancelled:
                return

            self.current_window += 1
            if success:
                self.valid_windows += 1

            # Update progress bar
            progress_percent = (self.current_window / self.total_windows) * 100
            self.total_progress_var.set(progress_percent)

            # Update progress label
            self.progress_label_var.set(
                f"Progress: {self.current_window}/{self.total_windows} Windows "
                f"({progress_percent:.1f}%)"
            )

            # Update current window info
            if success:
                status_text = (
                    f"✓ Window Center: {window_center:.1f} Ma\n"
                    f"Sample Count: {sample_count} samples\n"
                    f"Calculated Mean: {mean_value:.6f}\n"
                    f"Performing 10,000 Bootstrap resamples"
                )
            else:
                insufficient_msg = 'Insufficient Samples' if sample_count < 5 else 'Processing Failed'
                status_text = (
                    f"⚠ Window Center: {window_center:.1f} Ma\n"
                    f"Sample Count: {sample_count} samples\n"
                    f"Status: {insufficient_msg}"
                )

            if message:
                status_text += f"\nNote: {message}"

            self.current_window_var.set(status_text)

            # Update statistics info
            success_rate = (self.valid_windows / self.current_window * 100) if self.current_window > 0 else 0
            self.stats_var.set(
                f"Total Windows: {self.total_windows}\n"
                f"Processed: {self.current_window}\n"
                f"Valid Windows: {self.valid_windows}\n"
                f"Success Rate: {success_rate:.1f}%\n"
                f"Bootstrap Sampling: 10,000 resamples per valid window"
            )

            # Update interface
            self.root.update_idletasks()

        except Exception as e:
            print(f"[ERROR] Failed to update analysis progress: {e}")

    def on_cancel(self):
        """Cancel analysis"""
        try:
            result = messagebox.askyesno(
                'Confirm Cancel',
                'Are you sure you want to cancel the moving window analysis?\n\nCurrent progress will be lost.'
            )
            if result:
                self.cancelled = True
                self.close()
        except:
            self.cancelled = True
            self.close()

    def close(self):
        """Close window"""
        try:
            self.root.destroy()
        except:
            pass


class SimpleProgressDialog:
    """Simple Progress Dialog (Backup) - English Support"""

    def __init__(self, parent, title=None, message=None):
        self.parent = parent
        self.cancelled = False

        title = title or 'Processing...'
        message = message or 'Please wait...'

        self.root = tk.Toplevel(parent)
        self.root.title(title)
        self.root.geometry("400x150")
        self.root.resizable(False, False)

        # Center window
        self.center_window()

        # Set window properties
        self.root.transient(parent)
        self.root.grab_set()

        # Create interface
        self.create_simple_widgets(message)

    def center_window(self):
        """Center window"""
        self.root.update_idletasks()
        width = 400
        height = 150
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_simple_widgets(self, message):
        """Create simple interface components"""
        main_frame = tk.Frame(self.root, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Message label
        msg_label = tk.Label(
            main_frame,
            text=message,
            font=('Arial', 12),
            bg='white',
            fg='#333333'
        )
        msg_label.pack(pady=(0, 20))

        # Simple progress bar
        progress_bar = ttk.Progressbar(
            main_frame,
            mode='indeterminate',
            length=300
        )
        progress_bar.pack(pady=(0, 20))
        progress_bar.start(10)

        # Cancel button
        cancel_button = tk.Button(
            main_frame,
            text='Cancel',
            command=self.on_cancel,
            bg='#dc2626',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor='hand2'
        )
        cancel_button.pack()

    def on_cancel(self):
        """Cancel operation"""
        self.cancelled = True
        self.close()

    def close(self):
        """Close window"""
        try:
            self.root.destroy()
        except:
            pass


class LargeDatasetDialog:
    """Large Dataset Processing Dialog - English Support"""

    def __init__(self, parent, row_count):
        self.parent = parent
        self.result = None
        self.row_count = row_count

        self.create_dialog()

    def create_dialog(self):
        """Create dialog"""
        self.root = tk.Toplevel(self.parent)
        self.root.title('Large Dataset Processing')
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        # Center window
        self.center_window()

        # Set window properties
        self.root.transient(self.parent)
        self.root.grab_set()

        # Create interface
        self.create_widgets()

    def center_window(self):
        """Center window"""
        self.root.update_idletasks()
        width = 500
        height = 300
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        """Create interface components"""
        main_frame = tk.Frame(self.root, bg='white', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Icon and title
        title_frame = tk.Frame(main_frame, bg='white')
        title_frame.pack(fill=tk.X, pady=(0, 20))

        # Warning icon (using text instead)
        icon_label = tk.Label(
            title_frame,
            text="⚠",
            font=('Arial', 24),
            bg='white',
            fg='#f59e0b'
        )
        icon_label.pack(side=tk.LEFT, padx=(0, 10))

        # Title
        title_label = tk.Label(
            title_frame,
            text='Large Dataset Detected',
            font=('Arial', 16, 'bold'),
            bg='white',
            fg='#333333'
        )
        title_label.pack(side=tk.LEFT)

        # Information text
        info_text = f"""This dataset is quite large ({self.row_count:,} data points), which may affect performance.

Recommendations:
• Click "Yes": Sample 5,000 data points (Recommended, better performance)
• Click "No": Use all data (May be slower)
• Click "Cancel": Cancel loading"""

        info_label = tk.Label(
            main_frame,
            text=info_text,
            font=('Arial', 11),
            bg='white',
            fg='#666666',
            justify=tk.LEFT,
            wraplength=450
        )
        info_label.pack(pady=(0, 30), anchor=tk.W)

        # Button frame
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(fill=tk.X)

        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text='Cancel',
            command=self.on_cancel,
            bg='#6b7280',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # No button (all data)
        no_btn = tk.Button(
            button_frame,
            text='No (N)',
            command=self.on_no,
            bg='#f59e0b',
            fg='white',
            font=('Arial', 10),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        no_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Yes button (sample)
        yes_btn = tk.Button(
            button_frame,
            text='Yes (Y)',
            command=self.on_yes,
            bg='#10b981',
            fg='white',
            font=('Arial', 10, 'bold'),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor='hand2'
        )
        yes_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Bind keyboard shortcuts
        self.root.bind('<Return>', lambda e: self.on_yes())
        self.root.bind('<Escape>', lambda e: self.on_cancel())
        self.root.bind('<KeyPress-y>', lambda e: self.on_yes())
        self.root.bind('<KeyPress-Y>', lambda e: self.on_yes())
        self.root.bind('<KeyPress-n>', lambda e: self.on_no())
        self.root.bind('<KeyPress-N>', lambda e: self.on_no())

        # Set focus
        self.root.focus_set()

    def on_yes(self):
        """Choose sampling"""
        self.result = 'sample'
        self.close()

    def on_no(self):
        """Choose all data"""
        self.result = 'full'
        self.close()

    def on_cancel(self):
        """Cancel"""
        self.result = 'cancel'
        self.close()

    def close(self):
        """Close dialog"""
        try:
            self.root.destroy()
        except:
            pass

    def show(self):
        """Show dialog and return result"""
        self.root.focus_set()
        self.root.wait_window()
        return self.result


def show_large_dataset_dialog(parent, row_count):
    """Convenience function to show large dataset processing dialog"""
    dialog = LargeDatasetDialog(parent, row_count)
    return dialog.show()