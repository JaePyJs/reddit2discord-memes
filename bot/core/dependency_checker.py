import importlib
import logging
import sys
import subprocess
import shutil

def verify_dependencies():
    """Verify that all required dependencies are installed"""
    required_modules = [
        "discord",
        "discord.ext",
        "dotenv",
        "PIL",
        "spotipy",
        "yt_dlp",
        "requests"
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logging.error(f"Missing required modules: {', '.join(missing_modules)}")
        logging.error("Please install the missing modules using pip install -r requirements.txt")
        sys.exit(1)
    
    # Check for FFmpeg
    if not shutil.which("ffmpeg"):
        logging.error("FFmpeg is not installed or not in PATH. It is required for audio playback.")
        logging.error("Please install FFmpeg and make sure it's in your PATH.")
        sys.exit(1)
    
    logging.info("All dependencies verified")
