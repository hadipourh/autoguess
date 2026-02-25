"""
MiniZinc binary downloader — fetches the latest MiniZinc release for the
current platform and installs it under ``~/.autoguess/minizinc/``.

Usage:
    autoguess --install-minizinc

Copyright (C) 2021 Hosein Hadipour
License: GPL-3.0-or-later
"""

import os
import platform
import shutil
import sys
import tarfile
import tempfile
import zipfile
from urllib.request import urlopen, Request
import json

from autoguess.config import AUTOGUESS_HOME

MINIZINC_INSTALL_DIR = os.path.join(AUTOGUESS_HOME, "minizinc")

# GitHub API endpoint for latest release
GITHUB_API_URL = "https://api.github.com/repos/MiniZinc/MiniZincIDE/releases/latest"


def _get_latest_release_info():
    """Fetch latest release metadata from GitHub."""
    req = Request(GITHUB_API_URL, headers={"Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _detect_platform():
    """
    Determine the correct MiniZinc asset name suffix for the current platform.

    Returns:
        tuple: (suffix, extract_format) where extract_format is 'tgz' or 'zip'
    """
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Linux":
        if machine in ("x86_64", "amd64"):
            return "bundle-linux-x86_64.tgz", "tgz"
        elif machine in ("aarch64", "arm64"):
            # MiniZinc does not ship pre-built Linux ARM64 binaries.
            # Signal the caller to try system package managers instead.
            return None, "system"
        else:
            raise RuntimeError(f"Unsupported Linux architecture: {machine}")

    elif system == "Darwin":
        # MiniZinc provides a single universal "bundled.dmg" for macOS
        return "bundled.dmg", "dmg"

    elif system == "Windows":
        return "bundled-setup-win64.exe", "exe"

    else:
        raise RuntimeError(f"Unsupported operating system: {system}")


def _find_asset_url(release_info, suffix):
    """Find the download URL for the matching asset."""
    for asset in release_info.get("assets", []):
        if asset["name"].endswith(suffix):
            return asset["browser_download_url"], asset["name"]
    # Try .tgz alternative for macOS if .dmg found
    raise RuntimeError(
        f"Could not find a MiniZinc release asset matching '*{suffix}'.\n"
        f"Available assets: {[a['name'] for a in release_info.get('assets', [])]}"
    )


def _download(url, dest_path):
    """Download a URL to a local file with progress indication."""
    print(f"Downloading {url} ...")
    req = Request(url)
    with urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 256  # 256 KB
        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded * 100 // total
                    print(f"\r  {downloaded // (1024*1024)} MB / {total // (1024*1024)} MB ({pct}%)", end="", flush=True)
    print()  # Newline after progress


def _extract_tgz(archive_path, dest_dir):
    """Extract a .tgz archive, stripping one level of directory nesting."""
    with tarfile.open(archive_path, "r:gz") as tf:
        # Determine the top-level directory name
        members = tf.getmembers()
        top_dirs = {m.name.split("/")[0] for m in members if "/" in m.name}
        strip_prefix = top_dirs.pop() + "/" if len(top_dirs) == 1 else ""

        for member in members:
            if strip_prefix and member.name.startswith(strip_prefix):
                member.name = member.name[len(strip_prefix):]
            if not member.name or member.name == ".":
                continue
            # Python 3.12+ emits a DeprecationWarning without filter=
            if sys.version_info >= (3, 12):
                tf.extract(member, dest_dir, filter='data')
            else:
                tf.extract(member, dest_dir)


def _extract_dmg_fallback(archive_path, dest_dir):
    """
    On macOS, mount .dmg and copy contents. Falls back to suggesting manual install.
    """
    # Try using hdiutil to mount DMG (macOS only)
    import subprocess
    mount_point = tempfile.mkdtemp(prefix="minizinc_mount_")
    try:
        subprocess.run(
            ["hdiutil", "attach", archive_path, "-mountpoint", mount_point, "-nobrowse", "-quiet"],
            check=True,
        )
        # Find the MiniZincIDE.app or bin directory inside
        for item in os.listdir(mount_point):
            src = os.path.join(mount_point, item)
            if item.endswith(".app"):
                # Copy the bundle contents
                resources = os.path.join(src, "Contents", "Resources")
                if os.path.isdir(resources):
                    shutil.copytree(resources, dest_dir, dirs_exist_ok=True)
                    break
        else:
            # Copy whatever is in the DMG
            shutil.copytree(mount_point, dest_dir, dirs_exist_ok=True)
    finally:
        subprocess.run(["hdiutil", "detach", mount_point, "-quiet"], check=False)
        shutil.rmtree(mount_point, ignore_errors=True)


def _install_via_system_package_manager():
    """Attempt to install MiniZinc IDE via snap on Linux ARM64.

    The snap package ``minizinc`` ships the full MiniZinc IDE bundle
    (with Gecode, Chuffed, etc.).  The apt package ``minizinc`` is a
    bare-bones build without bundled solvers, so we do NOT use it.
    """
    import subprocess as _sp

    # snap "minizinc" is the full IDE bundle with solver backends
    if shutil.which("snap"):
        print("Attempting: snap install minizinc --classic ...")
        rc = _sp.call(["snap", "install", "minizinc", "--classic"])
        if rc == 0 and shutil.which("minizinc"):
            print("\nMiniZinc IDE installed successfully via snap.")
            return True
        print("snap install failed or minizinc not found after install.\n")

    return False


def install_minizinc():
    """
    Download and install MiniZinc to ``~/.autoguess/minizinc/``.

    This function is invoked by ``autoguess --install-minizinc``.
    """
    print("=== MiniZinc Installer for Autoguess ===\n")

    # Detect platform
    try:
        suffix, fmt = _detect_platform()
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Platform: {platform.system()} {platform.machine()}")

    # On Linux ARM64, MiniZinc doesn't provide pre-built binaries.
    # Try system package managers instead.
    if fmt == "system":
        print("No pre-built MiniZinc IDE binary available for this platform.")
        print("Trying system package manager ...\n")
        if _install_via_system_package_manager():
            print("Autoguess will automatically detect it on next run.")
            return
        print(
            "ERROR: Could not install MiniZinc IDE automatically.\n"
            "Please install MiniZinc IDE manually:\n"
            "  - snap install minizinc --classic   (recommended — full IDE bundle)\n"
            "  - Or build from source: https://github.com/MiniZinc/MiniZincIDE\n"
            "\n"
            "NOTE: 'apt install minizinc' provides only a bare-bones build\n"
            "without bundled solvers and is NOT recommended.\n"
        )
        sys.exit(1)

    print(f"Looking for asset matching: *{suffix}")

    # Fetch release info
    print("Fetching latest MiniZinc release info from GitHub...")
    try:
        release_info = _get_latest_release_info()
    except Exception as e:
        print(f"Error fetching release info: {e}")
        sys.exit(1)

    tag = release_info.get("tag_name", "unknown")
    print(f"Latest release: {tag}")

    # For macOS, prefer .tgz over .dmg if available
    if fmt == "dmg":
        tgz_suffix = suffix.replace(".dmg", ".tgz")
        try:
            url, name = _find_asset_url(release_info, tgz_suffix)
            suffix = tgz_suffix
            fmt = "tgz"
            print(f"Found .tgz bundle for macOS: {name}")
        except RuntimeError:
            # Try the .dmg
            try:
                url, name = _find_asset_url(release_info, suffix)
            except RuntimeError as e:
                print(f"Error: {e}")
                sys.exit(1)
    else:
        try:
            url, name = _find_asset_url(release_info, suffix)
        except RuntimeError as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Download
    with tempfile.TemporaryDirectory(prefix="autoguess_mzn_") as tmpdir:
        archive_path = os.path.join(tmpdir, name)
        _download(url, archive_path)

        # Remove old installation
        if os.path.exists(MINIZINC_INSTALL_DIR):
            print(f"Removing previous installation at {MINIZINC_INSTALL_DIR}")
            shutil.rmtree(MINIZINC_INSTALL_DIR)

        os.makedirs(MINIZINC_INSTALL_DIR, exist_ok=True)

        # Extract
        print(f"Extracting to {MINIZINC_INSTALL_DIR} ...")
        if fmt == "tgz":
            _extract_tgz(archive_path, MINIZINC_INSTALL_DIR)
        elif fmt == "dmg":
            _extract_dmg_fallback(archive_path, MINIZINC_INSTALL_DIR)
        elif fmt == "exe":
            print(
                f"Windows installer downloaded to: {archive_path}\n"
                f"Please run the installer manually and ensure MiniZinc is on your PATH,\n"
                f"or extract it to: {MINIZINC_INSTALL_DIR}"
            )
            # Copy the installer so user can find it
            final_path = os.path.join(AUTOGUESS_HOME, name)
            shutil.copy2(archive_path, final_path)
            print(f"Installer saved to: {final_path}")
            return

    # Verify installation
    minizinc_bin = os.path.join(MINIZINC_INSTALL_DIR, "bin", "minizinc")
    if not os.path.isfile(minizinc_bin):
        # Try without bin/ subfolder
        minizinc_bin = os.path.join(MINIZINC_INSTALL_DIR, "minizinc")

    if os.path.isfile(minizinc_bin):
        os.chmod(minizinc_bin, 0o755)
        # Verify the binary actually runs (catches glibc version mismatches)
        import subprocess as _sp
        try:
            out = _sp.check_output([minizinc_bin, "--version"],
                                   stderr=_sp.STDOUT, timeout=10)
            print(f"\nMiniZinc installed successfully at: {minizinc_bin}")
            print(f"  Version: {out.decode().strip()}")
            print("Autoguess will automatically detect it on next run.")
        except (OSError, _sp.CalledProcessError, _sp.TimeoutExpired) as exc:
            err_msg = str(exc.output.decode().strip()) if hasattr(exc, 'output') and exc.output else str(exc)
            print(f"\nWARNING: MiniZinc binary was extracted but cannot run:")
            print(f"  {err_msg}")
            if "GLIBC" in err_msg:
                print(f"\nYour system glibc is too old for MiniZinc {tag}.")
                print("Removing incompatible installation ...")
                shutil.rmtree(MINIZINC_INSTALL_DIR, ignore_errors=True)
                print("\nTrying snap instead (bundles its own libraries) ...")
                if _install_via_system_package_manager():
                    print("Autoguess will automatically detect it on next run.")
                    return
                print(
                    "\nOptions to resolve this:\n"
                    "  1. sudo snap install minizinc --classic  (recommended)\n"
                    "  2. Upgrade your OS to get glibc >= 2.34\n"
                    "  3. Download an older MiniZinc release (e.g. 2.6.4) manually:\n"
                    "     https://github.com/MiniZinc/MiniZincIDE/releases\n"
                    "     Extract to: ~/.autoguess/minizinc/\n"
                )
                sys.exit(1)
            else:
                print("\nYou may need to install missing system libraries.")
                print(f"Try: ldd {minizinc_bin} | grep 'not found'")
    else:
        print(f"\nWARNING: Could not locate minizinc binary in {MINIZINC_INSTALL_DIR}")
        print("Contents:")
        for root, dirs, files in os.walk(MINIZINC_INSTALL_DIR):
            for f in files[:20]:
                print(f"  {os.path.join(root, f)}")
        print("\nYou may need to adjust the installation manually.")


if __name__ == "__main__":
    install_minizinc()
