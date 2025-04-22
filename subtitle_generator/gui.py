"""
GUI Module

Contains the GUI components and application logic for the Subtitle Generator.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from subtitle_generator.processor import SubtitleProcessor
from subtitle_generator.whisper_patch import patch_whisper_audio_loading
from subtitle_generator.utils import (
    get_ffmpeg_path,
    setup_ffmpeg_environment,
    open_folder,
    ensure_directory_exists,
    get_supported_languages
)


class SubtitleGeneratorApp:
    """Main application class for the Subtitle Generator GUI."""
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root (tk.Tk): Root Tkinter window
        """
        self.root = root
        self.root.title("Subtitle Generator")
        self.root.geometry("750x600")
        self.root.resizable(True, True)
        
        # Initialize FFmpeg
        self.ffmpeg_path = get_ffmpeg_path()
        setup_ffmpeg_environment(self.ffmpeg_path)
        
        # Apply Whisper audio loading patch
        patch_whisper_audio_loading(self.ffmpeg_path, self.log)
        
        # Initialize processor
        self.processor = SubtitleProcessor(self.ffmpeg_path, self.log)
        
        # Initialize variables
        self.video_path = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.model_size = tk.StringVar(value="tiny")
        self.language = tk.StringVar(value="auto")
        self.status = tk.StringVar(value="Ready")
        self.progress = tk.DoubleVar(value=0)
        self.is_processing = False
        self.log_text = ""
        
        # Create UI
        self.create_ui()
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50")
        self.style.configure("TLabel", padding=6)
        
    def create_ui(self):
        """Create the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Video File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.video_path, width=50).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_video).grid(row=0, column=2, sticky=tk.E, pady=5)
        
        ttk.Label(input_frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=self.output_folder, width=50).grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=5)
        ttk.Button(input_frame, text="Browse", command=self.browse_output_folder).grid(row=1, column=2, sticky=tk.E, pady=5)
        
        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(settings_frame, text="Model Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
        model_combo = ttk.Combobox(settings_frame, textvariable=self.model_size, state="readonly")
        model_combo['values'] = ("tiny", "base", "small", "medium", "large")
        model_combo.grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(settings_frame, text="Smaller = Faster, Larger = More Accurate").grid(row=0, column=2, sticky=tk.W, pady=5, padx=10)
        
        ttk.Label(settings_frame, text="Language:").grid(row=1, column=0, sticky=tk.W, pady=5)
        language_combo = ttk.Combobox(settings_frame, textvariable=self.language, state="readonly")
        
        # Get language options
        languages = get_supported_languages()
        language_combo['values'] = [code for code, _ in languages]
        language_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Label(settings_frame, text="Auto = Detect Language").grid(row=1, column=2, sticky=tk.W, pady=5, padx=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Generate Subtitles", command=self.start_processing, style="TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Output Folder", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        
        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(progress_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        ttk.Label(progress_frame, textvariable=self.status).pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress, length=200, mode="determinate")
        self.progress_bar.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_area = tk.Text(log_frame, wrap=tk.WORD, height=10)
        self.log_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_area.config(yscrollcommand=scrollbar.set)
        self.log_area.config(state=tk.DISABLED)
        
        # Help section
        help_frame = ttk.Frame(main_frame)
        help_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(help_frame, text="Help", command=self.show_help).pack(side=tk.LEFT, padx=5)
        ttk.Button(help_frame, text="About", command=self.show_about).pack(side=tk.LEFT, padx=5)
    
    def log(self, message):
        """
        Add a message to the log area.
        
        Args:
            message (str): Message to log
        """
        self.log_text += f"{message}\n"
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.insert(tk.END, self.log_text)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def browse_video(self):
        """Open a file dialog to select a video file."""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv"), 
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.video_path.set(file_path)
            # Auto-set output folder to video location
            self.output_folder.set(os.path.dirname(file_path))
            self.log(f"Selected video: {file_path}")
    
    def browse_output_folder(self):
        """Open a dialog to select an output folder."""
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.output_folder.set(folder_path)
            self.log(f"Selected output folder: {folder_path}")
    
    def open_output_folder(self):
        """Open the output folder in the file explorer."""
        folder = self.output_folder.get()
        if open_folder(folder):
            self.log(f"Opening folder: {folder}")
        else:
            messagebox.showerror("Error", "Output folder doesn't exist")
    
    def show_help(self):
        """Show help information."""
        help_text = """
        How to use Subtitle Generator:
        
        1. Select a video file by clicking "Browse"
        2. Choose an output folder or use the default (same as video)
        3. Select a model size:
           - tiny: Fastest, less accurate
           - base: Good balance
           - small: Better quality but slower
           - medium: High quality but slower
           - large: Best quality but slowest
        4. Select language or leave as "auto" for automatic detection
        5. Click "Generate Subtitles" to start
        
        The application will:
        - Extract audio from your video
        - Transcribe the audio using Whisper AI
        - Generate SRT subtitle file
        
        Note: Processing large files can take several minutes.
        """
        messagebox.showinfo("Help", help_text)
    
    def show_about(self):
        """Show information about the application."""
        about_text = """
        Subtitle Generator v1.0
        
        This application generates subtitle files (SRT) for videos
        using OpenAI's Whisper speech recognition model.
        
        Features:
        - Automatic speech recognition
        - Multiple language support
        - Adjustable quality settings
        
        Powered by:
        - Whisper (OpenAI)
        - FFmpeg
        - Python
        """
        messagebox.showinfo("About", about_text)
    
    def start_processing(self):
        """Start the subtitle generation process."""
        if self.is_processing:
            messagebox.showwarning("Warning", "Already processing a video")
            return
        
        video_path = self.video_path.get()
        output_folder = self.output_folder.get()
        
        if not video_path:
            messagebox.showerror("Error", "Please select a video file")
            return
        
        if not os.path.exists(video_path):
            messagebox.showerror("Error", "Video file not found")
            return
        
        if not output_folder:
            # Default to video file's directory
            output_folder = os.path.dirname(video_path)
            self.output_folder.set(output_folder)
        
        if not ensure_directory_exists(output_folder):
            messagebox.showerror("Error", "Couldn't create output folder")
            return
        
        # Start processing in a separate thread
        self.is_processing = True
        threading.Thread(target=self.process_video_thread, daemon=True).start()
    
    def process_video_thread(self):
        """Process the video in a separate thread."""
        try:
            video_path = self.video_path.get()
            output_folder = self.output_folder.get()
            model_size = self.model_size.get()
            language = self.language.get() if self.language.get() != "auto" else None
            
            self.status.set("Extracting audio...")
            self.progress.set(10)
            
            # Process the video
            output_path = self.processor.process_video(
                video_path, 
                output_folder, 
                model_size, 
                language
            )
            
            self.status.set("Completed")
            self.progress.set(100)
            
            if not self.is_processing:  # Check if cancelled
                return
                
            messagebox.showinfo("Success", f"Subtitles generated successfully!\n\nSaved to: {output_path}")
            
        except Exception as e:
            self.status.set("Error")
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            self.is_processing = False
    
    def cancel_processing(self):
        """Cancel the current processing job."""
        if not self.is_processing:
            return
            
        if messagebox.askyesno("Cancel", "Cancel the current process?"):
            self.log("Cancelling process... (This may take a moment)")
            self.status.set("Cancelling...")
            self.is_processing = False 