# Path to Sagemath executable
import os
import platform
import subprocess

def find_sage_path():
    """
    Automatically detect SageMath installation path
    """
    # Common paths to check based on operating system
    common_paths = []
    
    system = platform.system()
    if system == "Darwin":  # macOS
        common_paths = [
            '/usr/local/bin/sage',  # Intel Mac with Homebrew
            '/opt/homebrew/bin/sage',  # Apple Silicon Mac with Homebrew
            '/Applications/SageMath.app/Contents/MacOS/sage',  # Cask installation
            '/Applications/SageMath/sage',  # Alternative installation
        ]
    elif system == "Linux":
        common_paths = [
            '/usr/bin/sage',  # System package installation
            '/usr/local/bin/sage',  # Manual installation
            '/opt/sage/sage',  # Alternative installation
        ]
    elif system == "Windows":
        common_paths = [
            'C:\\Program Files\\SageMath\\sage.exe',
            'C:\\SageMath\\sage.exe',
        ]
    
    # First try to find sage in PATH
    try:
        result = subprocess.run(['which', 'sage'], capture_output=True, text=True, check=True)
        sage_path = result.stdout.strip()
        if os.path.isfile(sage_path):
            return sage_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # If not in PATH, check common installation paths
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    # If still not found, return default based on system
    if system == "Darwin":
        return '/usr/local/bin/sage'
    elif system == "Linux":
        return '/usr/bin/sage'
    else:
        return 'sage'  # Hope it's in PATH

# Automatically detect SageMath path
PATH_SAGE = find_sage_path()
TEMP_DIR = 'temp'
