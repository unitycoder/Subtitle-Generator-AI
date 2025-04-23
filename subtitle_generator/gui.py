"""
GUI Module

Contains the GUI components and application logic for the Subtitle Generator.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

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
        self.root.geometry("780x650")  # Slightly larger window
        self.root.resizable(True, True)
        
        # Set dark mode colors
        self.bg_color = "#1e1e1e"  # Dark background
        self.text_color = "#ffffff"  # White text
        self.accent_color = "#007acc"  # Blue accent
        self.secondary_bg = "#2d2d2d"  # Slightly lighter background
        self.highlight_color = "#3e3e3e"  # Highlight color
        self.header_bg = "#333333"  # Header background color
        
        # Configure root with dark background
        self.root.configure(bg=self.bg_color)

        # Set background image
        self.background_image = Image.open("background.png")
        self.background_photo = ImageTk.PhotoImage(self.background_image)
        self.background_label = tk.Label(self.root, image=self.background_photo)
        self.background_label.place(relwidth=1, relheight=1)

        # Main container frame over background
        self.container = tk.Frame(self.root, bg=self.bg_color)
        self.container.place(relwidth=1, relheight=1)

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
        
        # Configure dark mode style
        self.configure_styles()
    
    def create_ui(self):
        """Create the user interface."""
        # Create a main frame with proper padding
        main_frame = ttk.Frame(self.container, padding="20", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid layout for better alignment
        main_frame.columnconfigure(0, weight=1)
        
        # ---------- Input Section ----------
        # Create a custom header for input section
        input_header = ttk.Frame(main_frame, style="Header.TFrame")
        input_header.grid(row=0, column=0, sticky=tk.EW, pady=(0, 0))
        
        input_header_label = ttk.Label(input_header, text="INPUT", font=("Arial", 11, "bold"), style="Header.TLabel")
        input_header_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Input section frame
        input_frame = ttk.Frame(main_frame, style="Panel.TFrame", padding=15)
        input_frame.grid(row=1, column=0, sticky=tk.EW, pady=(0, 20))
        
        # Configure grid columns for input frame
        input_frame.columnconfigure(1, weight=1)
        
        # Video file row
        ttk.Label(input_frame, text="Video File:", width=12, anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=10)
        entry_video = ttk.Entry(input_frame, textvariable=self.video_path)
        entry_video.grid(row=0, column=1, sticky=tk.EW, padx=(5, 5), pady=10)
        ttk.Button(input_frame, text="Browse", width=10, command=self.browse_video).grid(row=0, column=2, sticky=tk.E, padx=(5, 0), pady=10)
        
        # Output folder row
        ttk.Label(input_frame, text="Output Folder:", width=12, anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=10)
        entry_output = ttk.Entry(input_frame, textvariable=self.output_folder)
        entry_output.grid(row=1, column=1, sticky=tk.EW, padx=(5, 5), pady=10)
        ttk.Button(input_frame, text="Browse", width=10, command=self.browse_output_folder).grid(row=1, column=2, sticky=tk.E, padx=(5, 0), pady=10)

        # ---------- Settings Section ----------
        # Create a custom header for settings section
        settings_header = ttk.Frame(main_frame, style="Header.TFrame")
        settings_header.grid(row=2, column=0, sticky=tk.EW, pady=(0, 0))
        
        settings_header_label = ttk.Label(settings_header, text="SETTINGS", font=("Arial", 11, "bold"), style="Header.TLabel")
        settings_header_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Settings section frame
        settings_frame = ttk.Frame(main_frame, style="Panel.TFrame", padding=15)
        settings_frame.grid(row=3, column=0, sticky=tk.EW, pady=(0, 20))
        
        # Configure grid columns for settings frame
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(2, weight=2)
        
        # Model size row
        ttk.Label(settings_frame, text="Model Size:", width=12, anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=10)
        model_combo = ttk.Combobox(settings_frame, textvariable=self.model_size, state="readonly", width=15)
        model_combo['values'] = ("tiny", "base", "small", "medium", "large")
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 5), pady=10)
        ttk.Label(settings_frame, text="Smaller = Faster, Larger = More Accurate").grid(row=0, column=2, sticky=tk.W, padx=(15, 0), pady=10)
        
        # Language row
        ttk.Label(settings_frame, text="Language:", width=12, anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=10)
        language_combo = ttk.Combobox(settings_frame, textvariable=self.language, state="readonly", width=15)
        languages = get_supported_languages()
        language_combo['values'] = [code for code, _ in languages]
        language_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 5), pady=10)
        ttk.Label(settings_frame, text="Auto = Detect Language").grid(row=1, column=2, sticky=tk.W, padx=(15, 0), pady=10)

        # Button section
        button_frame = ttk.Frame(main_frame, padding=5)
        button_frame.grid(row=4, column=0, sticky=tk.EW, pady=(0, 15))
        
        # Create a grid for evenly spaced buttons
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=2)  # Extra space at the end
        
        ttk.Button(button_frame, text="Generate Subtitles", command=self.start_processing, width=18).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel_processing, width=12).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Open Output Folder", command=self.open_output_folder, width=18).grid(row=0, column=2, padx=5)

        # ---------- Progress Section ----------
        # Create a custom header for progress
        status_header = ttk.Frame(main_frame, style="Header.TFrame")
        status_header.grid(row=5, column=0, sticky=tk.EW, pady=(0, 0))
        
        status_label = ttk.Label(status_header, text="STATUS", font=("Arial", 11, "bold"), style="Header.TLabel")
        status_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Progress section
        progress_frame = ttk.Frame(main_frame, style="Panel.TFrame", padding=10)
        progress_frame.grid(row=6, column=0, sticky=tk.EW, pady=(0, 20))
        progress_frame.columnconfigure(1, weight=1)
        
        ttk.Label(progress_frame, text="Status:", width=8, anchor=tk.W).grid(row=0, column=0, sticky=tk.W, padx=(5, 5), pady=5)
        ttk.Label(progress_frame, textvariable=self.status, width=15, anchor=tk.W).grid(row=0, column=1, sticky=tk.W, padx=(0, 10), pady=5)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress, length=200, mode="determinate", style="Horizontal.TProgressbar")
        self.progress_bar.grid(row=0, column=2, sticky=tk.EW, padx=(10, 5), pady=5)

        # ---------- Log Section ----------
        # Create a custom header for log
        log_header = ttk.Frame(main_frame, style="Header.TFrame")
        log_header.grid(row=7, column=0, sticky=tk.EW, pady=(0, 0))
        
        log_label = ttk.Label(log_header, text="LOG", font=("Arial", 11, "bold"), style="Header.TLabel")
        log_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Log section
        log_frame = ttk.Frame(main_frame, style="Panel.TFrame", padding=15)
        log_frame.grid(row=8, column=0, sticky=tk.NSEW, pady=(0, 15))
        
        # Make log frame expandable
        main_frame.rowconfigure(8, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log area with scrollbar
        self.log_area = tk.Text(log_frame, wrap=tk.WORD, height=10, bg=self.secondary_bg, fg=self.text_color, insertbackground=self.text_color)
        self.log_area.grid(row=0, column=0, sticky=tk.NSEW)
        
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_area.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.log_area.config(yscrollcommand=scrollbar.set)
        self.log_area.config(state=tk.DISABLED)

        # Help/About section
        help_frame = ttk.Frame(main_frame)
        help_frame.grid(row=9, column=0, sticky=tk.EW)
        
        help_frame.columnconfigure(0, weight=0)
        help_frame.columnconfigure(1, weight=0)
        help_frame.columnconfigure(2, weight=1)  # Extra space
        
        ttk.Button(help_frame, text="Help", command=self.show_help, width=10).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(help_frame, text="About", command=self.show_about, width=10).grid(row=0, column=1, padx=(5, 0))

    def configure_styles(self):
        # This method is added to clean up the __init__ method
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # Base styles
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TButton", padding=6, relief="flat", background=self.accent_color, foreground=self.text_color)
        self.style.map("TButton", background=[('active', self.highlight_color), ('pressed', self.accent_color)])
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color, padding=6)
        
        # Custom styles
        self.style.configure("Header.TFrame", background=self.header_bg)
        self.style.configure("Header.TLabel", background=self.header_bg, foreground=self.text_color, font=('Arial', 11, 'bold'))
        self.style.configure("Panel.TFrame", background=self.secondary_bg, borderwidth=1, relief="solid")
        
        self.style.configure("TLabelframe", background=self.secondary_bg, foreground=self.text_color, borderwidth=1)
        self.style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.text_color, font=('Arial', 10, 'bold'))
        self.style.configure("TEntry", fieldbackground=self.secondary_bg, foreground=self.text_color, insertcolor=self.text_color)
        self.style.configure("TCombobox", background=self.secondary_bg, fieldbackground=self.secondary_bg, foreground=self.text_color)
        self.style.map("TCombobox", fieldbackground=[('readonly', self.secondary_bg)])
        self.style.configure("Horizontal.TProgressbar", background=self.accent_color, troughcolor=self.secondary_bg)

    def log(self, message):
        self.log_text += f"{message}\n"
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.insert(tk.END, self.log_text)
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def browse_video(self):
        file_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv"), ("All Files", "*.*")])
        if file_path:
            self.video_path.set(file_path)
            self.output_folder.set(os.path.dirname(file_path))
            self.log(f"Selected video: {file_path}")

    def browse_output_folder(self):
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.output_folder.set(folder_path)
            self.log(f"Selected output folder: {folder_path}")

    def open_output_folder(self):
        folder = self.output_folder.get()
        if open_folder(folder):
            self.log(f"Opening folder: {folder}")
        else:
            self.show_error("Error", "Output folder doesn't exist")

    def show_help(self):
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Help")
        help_dialog.geometry("500x400")
        help_dialog.configure(bg=self.bg_color)
        help_dialog.transient(self.root)
        help_dialog.grab_set()
        
        # Add help content
        frame = ttk.Frame(help_dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(frame, text="Subtitle Generator Help", font=("Arial", 14, "bold"))
        title.pack(pady=(0, 10))
        
        help_text = tk.Text(frame, wrap=tk.WORD, bg=self.secondary_bg, fg=self.text_color, height=15)
        help_text.pack(fill=tk.BOTH, expand=True)
        help_text.insert(tk.END, """
How to use the Subtitle Generator:

1. Click 'Browse' to select a video file
2. Choose an output folder (defaults to video's folder)
3. Select a model size (larger = more accurate, smaller = faster)
4. Select a language (or leave as 'auto' for auto-detection)
5. Click 'Generate Subtitles' to start processing
6. Wait for processing to complete
7. Subtitles will be saved in the output folder

Note: This application requires an internet connection to download the Whisper model (first time only).
        """)
        help_text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(frame, text="Close", command=help_dialog.destroy).pack(pady=10)

    def show_about(self):
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("About")
        about_dialog.geometry("400x300")
        about_dialog.configure(bg=self.bg_color)
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        
        frame = ttk.Frame(about_dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(frame, text="Subtitle Generator", font=("Arial", 16, "bold"))
        title.pack(pady=(0, 5))
        
        version = ttk.Label(frame, text="Version 1.0.0")
        version.pack(pady=(0, 15))
        
        description = tk.Text(frame, wrap=tk.WORD, bg=self.secondary_bg, fg=self.text_color, height=8)
        description.pack(fill=tk.BOTH, expand=True)
        description.insert(tk.END, """
An application for automatically generating subtitles for video files using OpenAI's Whisper speech recognition model.

Created by InboraStudio.

This software is open source and free to use under the MIT License.
        """)
        description.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(frame, text="Close", command=about_dialog.destroy).pack(pady=10)

    def show_error(self, title, message):
        """Show an error message box with dark theme."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Error icon (can be replaced with an actual image if available)
        error_label = ttk.Label(frame, text="⚠", font=("Arial", 24))
        error_label.pack(pady=(0, 10))
        
        # Message
        msg_label = ttk.Label(frame, text=message, wraplength=350)
        msg_label.pack(pady=10)
        
        # OK button
        ttk.Button(frame, text="OK", command=dialog.destroy).pack(pady=10)
        
        # Make dialog modal
        dialog.focus_set()
        dialog.wait_window()

    def show_info(self, title, message):
        """Show an information message box with dark theme."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Info icon (can be replaced with an actual image if available)
        info_label = ttk.Label(frame, text="ℹ", font=("Arial", 24))
        info_label.pack(pady=(0, 10))
        
        # Message
        msg_label = ttk.Label(frame, text=message, wraplength=350)
        msg_label.pack(pady=10)
        
        # OK button
        ttk.Button(frame, text="OK", command=dialog.destroy).pack(pady=10)
        
        # Make dialog modal
        dialog.focus_set()
        dialog.wait_window()
    
    def show_confirm(self, title, message):
        """Show a confirmation dialog with dark theme."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        result = tk.BooleanVar(value=False)
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Question icon (can be replaced with an actual image if available)
        question_label = ttk.Label(frame, text="?", font=("Arial", 24))
        question_label.pack(pady=(0, 10))
        
        # Message
        msg_label = ttk.Label(frame, text=message, wraplength=350)
        msg_label.pack(pady=10)
        
        # Buttons frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        def on_yes():
            result.set(True)
            dialog.destroy()
            
        def on_no():
            result.set(False)
            dialog.destroy()
        
        # Yes/No buttons
        ttk.Button(button_frame, text="Yes", command=on_yes).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="No", command=on_no).pack(side=tk.LEFT, padx=10)
        
        # Make dialog modal
        dialog.focus_set()
        dialog.wait_window()
        
        return result.get()

    def start_processing(self):
        if self.is_processing:
            self.show_info("Warning", "Already processing a video")
            return
        video_path = self.video_path.get()
        output_folder = self.output_folder.get()
        if not video_path or not os.path.exists(video_path):
            self.show_error("Error", "Please select a valid video file")
            return
        if not output_folder:
            output_folder = os.path.dirname(video_path)
            self.output_folder.set(output_folder)
        if not ensure_directory_exists(output_folder):
            self.show_error("Error", "Couldn't create output folder")
            return
        self.is_processing = True
        threading.Thread(target=self.process_video_thread, daemon=True).start()

    def process_video_thread(self):
        try:
            output_path = self.processor.process_video(
                self.video_path.get(),
                self.output_folder.get(),
                self.model_size.get(),
                self.language.get() if self.language.get() != "auto" else None
            )
            self.status.set("Completed")
            self.progress.set(100)
            if not self.is_processing:
                return
            self.show_info("Success", f"Subtitles generated successfully!\n\nSaved to: {output_path}")
        except Exception as e:
            self.status.set("Error")
            self.log(f"Error: {str(e)}")
            self.show_error("Error", f"An error occurred: {str(e)}")
        finally:
            self.is_processing = False

    def cancel_processing(self):
        if self.is_processing and self.show_confirm("Cancel", "Cancel the current process?"):
            self.log("Cancelling process... (This may take a moment)")
            self.status.set("Cancelling...")
            self.is_processing = False
