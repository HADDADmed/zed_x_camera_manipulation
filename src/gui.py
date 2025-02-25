import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import queue
import sys
import threading
import time
from datetime import timedelta
from PIL import Image, ImageTk
from pyzed.sl import RESOLUTION
from recorder.recording_controller import RecordingController
import os

class GuiLogger:
    """Custom logger that redirects output to Tkinter text widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.original_stdout = sys.stdout
        self.queue = queue.Queue()
        self.running = True

    def write(self, message):
        self.queue.put(message)
        
    def flush(self):
        pass

    def start_redirect(self):
        sys.stdout = self
        self.poll_queue()

    def stop_redirect(self):
        self.running = False
        sys.stdout = self.original_stdout

    def poll_queue(self):
        while not self.queue.empty():
            message = self.queue.get_nowait()
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
            self.text_widget.configure(state='disabled')
        if self.running:
            self.text_widget.after(100, self.poll_queue)

class RecordingGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ZED Camera Recorder - Professional Edition")
        self.geometry("1280x800")
        self.style = ttk.Style()
        self.configure_styles()
        
        self.recording_controller = None
        self.recording_thread = None
        self.is_recording = False
        self.start_time = None
        self.logger = None
        self.logo_image = None

        # Create GUI elements
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def configure_styles(self):
        self.style.configure('TButton', font=('Helvetica', 14), padding=10)
        self.style.configure('Title.TLabel', font=('Helvetica', 20, 'bold'))
        self.style.configure('Status.TLabel', font=('Helvetica', 12), foreground='gray')
        self.style.configure('Timer.TLabel', font=('Courier New', 24), foreground='#2c3e50')
        self.style.configure('Red.TButton', foreground='white', background='#e74c3c')
        self.style.map('Red.TButton',
                      foreground=[('active', 'white'), ('disabled', 'gray')],
                      background=[('active', '#c0392b'), ('disabled', '#95a5a6')])

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header with logo
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=10)
        
        try:
            script_directory = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(script_directory, "LOGO.png")
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((120, 120), Image.ANTIALIAS)
            self.logo_image = ImageTk.PhotoImage(logo_img)
            ttk.Label(header_frame, image=self.logo_image).pack(side=tk.LEFT)
        except Exception as e:
            print(f"Could not load logo: {str(e)}")

        ttk.Label(header_frame, text="ZED Camera Controller", style='Title.TLabel').pack(side=tk.LEFT, padx=20)

        # Control Panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=20)

        self.record_btn = ttk.Button(
            control_frame,
            text="⏺ START RECORDING",
            style='Red.TButton',
            command=self.toggle_recording
        )
        self.record_btn.pack(side=tk.LEFT, padx=20)

        # Status Indicator
        self.status_indicator = ttk.Label(control_frame, text="Ready", style='Status.TLabel')
        self.status_indicator.pack(side=tk.LEFT, padx=20)

        # Timer Display
        timer_frame = ttk.Frame(control_frame)
        timer_frame.pack(side=tk.RIGHT, padx=20)
        
        ttk.Label(timer_frame, text="Recording Time:", style='Status.TLabel').pack(anchor=tk.E)
        self.timer_label = ttk.Label(timer_frame, text="00:00:00", style='Timer.TLabel')
        self.timer_label.pack()

        # Log Display
        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            state='disabled',
            wrap=tk.WORD,
            font=('Consolas', 10),
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Initialize logger
        self.logger = GuiLogger(self.log_text)
        self.logger.start_redirect()

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Start recording in a separate thread"""
        self.is_recording = True
        self.record_btn.config(text="⏹ STOP RECORDING")
        self.status_indicator.config(text="Initializing cameras...", foreground='orange')
        self.record_btn.state(['disabled'])
        
        # Start recording thread
        self.recording_thread = threading.Thread(
            target=self.run_recording_controller,
            daemon=True
        )
        self.recording_thread.start()
        
        # Start initialization check
        self.check_initialization_status()

    def check_initialization_status(self):
        """Check if cameras have been initialized and update status accordingly"""
        if self.is_recording and self.recording_controller is None:
            self.after(100, self.check_initialization_status)
        else:
            self.status_indicator.config(text="Recording", foreground='green')
            self.start_time = time.time()
            self.update_timer()
            self.record_btn.state(['!disabled'])  # Re-enable the record button

    def stop_recording(self):
        """Stop recording and clean up resources"""
        self.is_recording = False
        self.record_btn.config(text="⏺ START RECORDING")
        self.status_indicator.config(text="Ready", foreground='gray')
        self.record_btn.state(['!disabled'])
        
        if self.recording_controller:
            self.recording_controller.stop_recording()
            self.recording_controller = None

    def run_recording_controller(self):
        """Thread target for running recording controller"""
        try:
            config = {
                "camera_resolution": RESOLUTION.HD1200,
                "camera_fps": 30,
                "gnss_port": "COM3",
                "gnss_baudrate": 9600
            }
            self.recording_controller = RecordingController(config=config)
            print("Starting recording session...")
            self.recording_controller.run()
            
        except Exception as e:
            messagebox.showerror("Error", f"Recording failed: {str(e)}")
            print(f"Recording error: {str(e)}")
        finally:
            self.stop_recording()

    def update_timer(self):
        """Update the elapsed time display"""
        if self.is_recording:
            elapsed = time.time() - self.start_time
            time_str = str(timedelta(seconds=int(elapsed))).split(".")[0]
            self.timer_label.config(text=time_str)
            self.after(1000, self.update_timer)

    def on_close(self):
        """Clean up when window is closed"""
        self.logger.stop_redirect()
        if self.recording_controller:
            self.recording_controller.stop_recording()
        self.destroy()

if __name__ == "__main__":
    app = RecordingGUI()
    app.mainloop()