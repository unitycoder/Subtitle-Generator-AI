"""
Utils Module

Utility functions for the Subtitle Generator application.
"""

import os
import subprocess
import warnings
import imageio_ffmpeg

# Suppress specific warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
warnings.filterwarnings("ignore", message="You are using `torch.load` with `weights_only=False`")

def get_ffmpeg_path():
    """
    Get the path to the FFmpeg executable.
    
    Returns:
        str: Path to the FFmpeg executable
    """
    return imageio_ffmpeg.get_ffmpeg_exe()

def setup_ffmpeg_environment(ffmpeg_path):
    """
    Add FFmpeg to environment PATH.
    
    Args:
        ffmpeg_path (str): Path to the FFmpeg executable
    """
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    
def open_folder(folder_path):
    """
    Open the specified folder in the file explorer.
    
    Args:
        folder_path (str): Path to the folder to open
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not folder_path or not os.path.exists(folder_path):
        return False
        
    try:
        if os.name == 'nt':  # Windows
            os.startfile(folder_path)
        elif os.name == 'posix':  # macOS or Linux
            if os.path.exists('/usr/bin/open'):  # macOS
                subprocess.call(['open', folder_path])
            else:  # Linux
                subprocess.call(['xdg-open', folder_path])
        return True
    except Exception:
        return False
        
def ensure_directory_exists(directory_path):
    """
    Ensure the specified directory exists, creating it if necessary.
    
    Args:
        directory_path (str): Path to the directory
        
    Returns:
        bool: True if the directory exists or was created successfully, False otherwise
    """
    if not directory_path:
        return False
        
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return True
    except Exception:
        return False
        
def get_supported_languages():
    """
    Get a list of supported languages for the Whisper model.
    
    Returns:
        list: List of tuples containing (language code, language name)
    """
    return [
        ('auto', 'Auto-detect'),
        ('en', 'English'),
        ('zh', 'Chinese'),
        ('de', 'German'),
        ('es', 'Spanish'),
        ('ru', 'Russian'),
        ('ko', 'Korean'),
        ('fr', 'French'),
        ('ja', 'Japanese'),
        ('pt', 'Portuguese'),
        ('tr', 'Turkish'),
        ('pl', 'Polish'),
        ('ca', 'Catalan'),
        ('nl', 'Dutch'),
        ('ar', 'Arabic'),
        ('sv', 'Swedish'),
        ('it', 'Italian'),
        ('id', 'Indonesian'),
        ('hi', 'Hindi'),
        ('fi', 'Finnish'),
        ('vi', 'Vietnamese'),
        ('uk', 'Ukrainian'),
        ('he', 'Hebrew'),
        ('cs', 'Czech'),
        ('el', 'Greek'),
        ('ro', 'Romanian'),
        ('fa', 'Persian'),
        ('da', 'Danish'),
        ('hu', 'Hungarian'),
        ('no', 'Norwegian'),
        ('th', 'Thai'),
        ('ur', 'Urdu')
    ] 