import subprocess
import sys
import logging

def check_ffmpeg():
    """
    Check if FFmpeg is installed and available in the system path.
    Returns True if FFmpeg is available, False otherwise.
    """
    try:
        # Try to run ffmpeg -version to check if it's installed
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def verify_dependencies():
    """
    Verify all external dependencies required by the bot.
    Logs warnings for missing dependencies.
    """
    # Check FFmpeg (required for music playback)
    if not check_ffmpeg():
        logging.warning("FFmpeg is not installed or not in PATH. Music functionality will not work.")
        print("WARNING: FFmpeg is not installed or not in PATH. Music functionality will not work.")
        print("Please install FFmpeg: https://ffmpeg.org/download.html")
        
    # Add more dependency checks here as needed
    
if __name__ == "__main__":
    # Can be run directly to check dependencies
    verify_dependencies()
