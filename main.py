#!/usr/bin/env python3
"""
Subtitle Generator

Main entry point for the Subtitle Generator application.
"""

import os
import sys
import tkinter as tk

# Add the parent directory to sys.path if running as script
if __name__ == "__main__" and __package__ is None:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)

# Import the GUI module
from subtitle_generator.gui import SubtitleGeneratorApp


def main():
    """
    Main function to start the Subtitle Generator application.
    """
    # Create the root window
    root = tk.Tk()
    
    # Set icon (if available)
    try:
        if os.path.exists("icon.ico"):
            root.iconbitmap("icon.ico")
    except Exception:
        pass
    
    # Create the application
    app = SubtitleGeneratorApp(root)
    
    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        import tkinter.messagebox as messagebox
        
        # Show error message
        error_message = f"An unexpected error occurred:\n\n{str(e)}\n\n"
        error_message += "This could be due to missing dependencies or system configuration."
        error_message += "\n\nPlease check the README file for installation instructions."
        
        # Print traceback to console
        traceback.print_exc()
        
        # Show message box
        try:
            messagebox.showerror("Error", error_message)
        except:
            print(error_message)
        
        sys.exit(1) 