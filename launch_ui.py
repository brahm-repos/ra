#!/usr/bin/env python3
"""
Simple launcher for the HR Analyst Agent UI
"""

import sys
import os

def main():
    """Launch the Gradio UI."""
    # Check required environment variables
    required_env_vars = [
        ("AZURE_OPENAI_ENDPOINT", "https://<your-resource-name>.openai.azure.com/"),
        ("AZURE_OPENAI_API_KEY", "<your-azure-openai-api-key>"),
        ("AZURE_OPENAI_REGION", "<your-azure-region>")
    ]
    missing_vars = [var for var, _ in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        print("\nERROR: The following required environment variables are not set:")
        for var, example in required_env_vars:
            if var in missing_vars:
                print(f"  {var}  (example: {example})")
        print("\nPlease set these variables and re-run the application.\n")
        sys.exit(1)

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