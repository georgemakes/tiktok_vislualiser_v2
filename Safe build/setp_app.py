"""
This script creates proper Python module imports by copying all necessary files to the app directory.
Run this once before starting the Streamlit app to ensure all modules are correctly located.
"""

import os
import shutil
import sys


def ensure_files_in_app_directory():
    """Copy all necessary Python files to the app directory if they're not already there."""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the source files
    required_files = [
        'data_processor.py',
        'line_chart.py',
        'bar_chart.py',
        'heatmap.py',
        'tiktok_style.py',
        'app.py',
        'run_streamlit.py'
    ]

    # Check for files in current directory and parent directory
    for filename in required_files:
        # Skip if the file already exists in the current directory
        if os.path.exists(os.path.join(current_dir, filename)):
            print(f"✓ {filename} already exists in the app directory")
            continue

        # Check if file exists in parent directory
        parent_file = os.path.join(os.path.dirname(current_dir), filename)
        if os.path.exists(parent_file):
            # Copy from parent to current directory
            shutil.copy2(parent_file, os.path.join(current_dir, filename))
            print(f"✓ Copied {filename} from parent directory to app directory")
        else:
            print(f"✗ Warning: {filename} not found in either current or parent directory")

    print("\nSetup complete! You can now run the Streamlit app.")


if __name__ == "__main__":
    ensure_files_in_app_directory()