"""
TikTok Ad Report Analyzer

This script allows you to run the Streamlit application for analyzing TikTok ad reports.
"""

import os
import subprocess
import sys


def run_streamlit():
    streamlit_file = os.path.join("app.py")

    if os.path.exists(streamlit_file):
        try:
            subprocess.run([sys.executable, "-m", "streamlit", "run", streamlit_file], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running Streamlit: {e}")
        except FileNotFoundError:
            print("Streamlit not found. Please install it using 'pip install streamlit'")
    else:
        print(f"Streamlit file not found at {streamlit_file}")


if __name__ == "__main__":
    run_streamlit()