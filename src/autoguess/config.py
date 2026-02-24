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


def ensure_minizinc_driver():
    """
    Make sure the ``minizinc`` Python package knows where our MiniZinc binary
    lives.  If ``minizinc.default_driver`` is *None* (i.e. MiniZinc was not
    found on the system PATH), we point it at the binary discovered by
    ``find_minizinc_path()`` (which checks ``~/.autoguess/minizinc/`` among
    other locations).

    Call this once before any code that touches ``minizinc.default_driver``.
    """
    try:
        import minizinc
    except ImportError:
        return  # minizinc package not installed -- nothing to do

    if minizinc.default_driver is not None:
        return  # already initialised -- nothing to do

    mzn_path = find_minizinc_path()
    if mzn_path is None:
        return  # not installed anywhere we know of

    from pathlib import Path
    try:
        drv = minizinc.Driver(Path(mzn_path))
        minizinc.default_driver = drv
    except Exception:
        pass  # incompatible version or other issue -- leave driver as None


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

# Prepend the managed MiniZinc bin directory to PATH so that
# ``import minizinc`` finds it during its __init__ and does not
# emit a "MiniZinc was not found" RuntimeWarning.
if MINIZINC_PATH is not None:
    _mzn_bin_dir = os.path.dirname(MINIZINC_PATH)
    if _mzn_bin_dir not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = _mzn_bin_dir + os.pathsep + os.environ.get("PATH", "")
    # Bundled solver binaries (e.g. fzn-cp-sat / OR-Tools) link against
    # shared libraries shipped inside the MiniZinc bundle's lib/ directory.
    # We do NOT set LD_LIBRARY_PATH globally here because it would pollute
    # the environment for other subprocesses (e.g. Graphviz's dot).  Instead
    # we export the path so gdcp.py can set it only around the solve() call.
    _mzn_lib_dir = os.path.join(os.path.dirname(_mzn_bin_dir), "lib")
    MINIZINC_LIB_DIR = _mzn_lib_dir if os.path.isdir(_mzn_lib_dir) else None
else:
    MINIZINC_LIB_DIR = None
