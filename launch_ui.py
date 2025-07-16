#!/usr/bin/env python3
"""
Simple launcher for the HR Analyst Agent UI
"""

import sys
import os

def main():
    """Launch the Gradio UI."""
    try:
        # Check if gradio is installed
        try:
            import gradio
        except ImportError:
            print("Gradio is not installed. Installing required packages...")
            os.system("pip install gradio markdown")
        
        # Import and launch the UI
        from gradio_ui import main as launch_ui
        launch_ui()
        
    except Exception as e:
        print(f"Error launching UI: {e}")
        print("Please make sure all dependencies are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main() 