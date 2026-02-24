"""
Configuration and path detection for autoguess.

Copyright (C) 2021 Hosein Hadipour
License: GPL-3.0-or-later
"""

import os
import platform
import subprocess
import shutil


# ---------------------------------------------------------------------------
# Autoguess home directory (for MiniZinc downloads, temp files, etc.)
# ---------------------------------------------------------------------------
AUTOGUESS_HOME = os.path.join(os.path.expanduser("~"), ".autoguess")


# ---------------------------------------------------------------------------
# Temporary directory for intermediate files
# ---------------------------------------------------------------------------
TEMP_DIR = os.environ.get("AUTOGUESS_TEMP_DIR", os.path.join(AUTOGUESS_HOME, "temp"))


# ---------------------------------------------------------------------------
# MiniZinc binary detection
# ---------------------------------------------------------------------------
def find_minizinc_path():
    """
    Locate the MiniZinc binary.

    Search order:
    1. MINIZINC_PATH environment variable
    2. ~/.autoguess/minizinc/ (our runtime downloader location)
    3. System PATH (via ``shutil.which``)
    """
    # 1. Environment override
    env_path = os.environ.get("MINIZINC_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # 2. Our managed installation
    managed_dir = os.path.join(AUTOGUESS_HOME, "minizinc")
    system = platform.system()
    if system == "Darwin":
        managed_bin = os.path.join(managed_dir, "bin", "minizinc")
    elif system == "Linux":
        managed_bin = os.path.join(managed_dir, "bin", "minizinc")
    else:
        managed_bin = os.path.join(managed_dir, "minizinc.exe")

    if os.path.isfile(managed_bin):
        return managed_bin

    # 3. System PATH
    system_bin = shutil.which("minizinc")
    if system_bin:
        return system_bin

    return None


# ---------------------------------------------------------------------------
# SageMath detection (fallback for systems without passagemath)
# ---------------------------------------------------------------------------
def find_sage_path():
    """
    Detect system SageMath installation.

    This is only needed as a fallback when ``passagemath`` is not installed
    in the current Python environment.  With passagemath the sage modules
    are available directly — no subprocess is needed.
    """
    common_paths = []
    system = platform.system()

    if system == "Darwin":
        common_paths = [
            "/usr/local/bin/sage",
            "/opt/homebrew/bin/sage",
            "/Applications/SageMath.app/Contents/MacOS/sage",
            "/Applications/SageMath/sage",
        ]
    elif system == "Linux":
        common_paths = [
            "/usr/bin/sage",
            "/usr/local/bin/sage",
            "/opt/sage/sage",
        ]
    elif system == "Windows":
        common_paths = [
            r"C:\Program Files\SageMath\sage.exe",
            r"C:\SageMath\sage.exe",
        ]

    # Try PATH first
    sage_in_path = shutil.which("sage")
    if sage_in_path:
        return sage_in_path

    for path in common_paths:
        if os.path.isfile(path):
            return path

    return None


def sage_is_available():
    """Return True if SageMath can be imported (e.g. via passagemath)."""
    try:
        from sage.all import BooleanPolynomialRing  # noqa: F401
        return True
    except ImportError:
        return False


# Eagerly resolve these at import time
PATH_SAGE = find_sage_path()
MINIZINC_PATH = find_minizinc_path()
SAGE_IMPORTABLE = sage_is_available()
