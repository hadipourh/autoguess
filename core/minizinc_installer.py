"""
MiniZinc binary downloader — fetches the latest MiniZinc release for the
current platform and installs it under ``~/.autoguess/minizinc/``.

Usage (root CLI):
    python3 autoguess.py --install-minizinc

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

from config import AUTOGUESS_HOME

MINIZINC_INSTALL_DIR = os.path.join(AUTOGUESS_HOME, "minizinc")

# GitHub API endpoints
GITHUB_API_URL = "https://api.github.com/repos/MiniZinc/MiniZincIDE/releases/latest"
GITHUB_RELEASES_URL = "https://api.github.com/repos/MiniZinc/MiniZincIDE/releases"


def _get_latest_release_info():
    """Fetch latest release metadata from GitHub."""
    req = Request(GITHUB_API_URL, headers={"Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_releases_list(per_page=30):
    """Fetch a list of recent releases from GitHub."""
    url = f"{GITHUB_RELEASES_URL}?per_page={per_page}"
    req = Request(url, headers={"Accept": "application/vnd.github+json"})
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
    print()


def _extract_tgz(archive_path, dest_dir):
    """Extract a .tgz archive, stripping one level of directory nesting."""
    with tarfile.open(archive_path, "r:gz") as tf:
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
    """On macOS, mount .dmg and copy contents."""
    import subprocess
    mount_point = tempfile.mkdtemp(prefix="minizinc_mount_")
    try:
        subprocess.run(
            ["hdiutil", "attach", archive_path, "-mountpoint", mount_point, "-nobrowse", "-quiet"],
            check=True,
        )
        for item in os.listdir(mount_point):
            src = os.path.join(mount_point, item)
            if item.endswith(".app"):
                resources = os.path.join(src, "Contents", "Resources")
                if os.path.isdir(resources):
                    shutil.copytree(resources, dest_dir, dirs_exist_ok=True)
                    break
        else:
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


def _try_install_release(release_info, suffix, fmt):
    """Download, extract, and verify one MiniZinc release.

    Returns ``(True, version_string)`` on success.
    Returns ``(False, "glibc")`` when the system glibc is too old.
    Returns ``(False, error_message)`` for other failures.
    """
    import subprocess as _sp

    tag = release_info.get("tag_name", "unknown")

    # On macOS prefer .tgz over .dmg when available
    actual_suffix, actual_fmt = suffix, fmt
    if fmt == "dmg":
        tgz_suffix = suffix.replace(".dmg", ".tgz")
        try:
            _find_asset_url(release_info, tgz_suffix)
            actual_suffix, actual_fmt = tgz_suffix, "tgz"
        except RuntimeError:
            pass

    try:
        url, name = _find_asset_url(release_info, actual_suffix)
    except RuntimeError as e:
        return False, str(e)

    with tempfile.TemporaryDirectory(prefix="autoguess_mzn_") as tmpdir:
        archive_path = os.path.join(tmpdir, name)
        _download(url, archive_path)

        if os.path.exists(MINIZINC_INSTALL_DIR):
            shutil.rmtree(MINIZINC_INSTALL_DIR)
        os.makedirs(MINIZINC_INSTALL_DIR, exist_ok=True)

        print(f"Extracting to {MINIZINC_INSTALL_DIR} ...")
        if actual_fmt == "tgz":
            _extract_tgz(archive_path, MINIZINC_INSTALL_DIR)
        elif actual_fmt == "dmg":
            _extract_dmg_fallback(archive_path, MINIZINC_INSTALL_DIR)

    # Locate binary
    minizinc_bin = os.path.join(MINIZINC_INSTALL_DIR, "bin", "minizinc")
    if not os.path.isfile(minizinc_bin):
        minizinc_bin = os.path.join(MINIZINC_INSTALL_DIR, "minizinc")

    if not os.path.isfile(minizinc_bin):
        return False, "binary not found after extraction"

    os.chmod(minizinc_bin, 0o755)

    try:
        out = _sp.check_output(
            [minizinc_bin, "--version"], stderr=_sp.STDOUT, timeout=10
        )
        return True, out.decode().strip()
    except (OSError, _sp.CalledProcessError, _sp.TimeoutExpired) as exc:
        err_msg = (
            exc.output.decode().strip()
            if hasattr(exc, "output") and exc.output
            else str(exc)
        )
        shutil.rmtree(MINIZINC_INSTALL_DIR, ignore_errors=True)
        if "GLIBC" in err_msg:
            return False, "glibc"
        return False, err_msg


def install_minizinc():
    """
    Download and install MiniZinc to ``~/.autoguess/minizinc/``.

    This function is invoked by ``python3 autoguess.py --install-minizinc``.
    """
    print("=== MiniZinc Installer for Autoguess ===\n")

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

    # Fetch latest release
    print("Fetching latest MiniZinc release info from GitHub...")
    try:
        release_info = _get_latest_release_info()
    except Exception as e:
        print(f"Error fetching release info: {e}")
        sys.exit(1)

    tag = release_info.get("tag_name", "unknown")
    print(f"Latest release: {tag}")

    # Windows: just download the installer and let the user run it
    if fmt == "exe":
        try:
            url, name = _find_asset_url(release_info, suffix)
        except RuntimeError as e:
            print(f"Error: {e}")
            sys.exit(1)
        with tempfile.TemporaryDirectory(prefix="autoguess_mzn_") as tmpdir:
            archive_path = os.path.join(tmpdir, name)
            _download(url, archive_path)
            final_path = os.path.join(AUTOGUESS_HOME, name)
            os.makedirs(AUTOGUESS_HOME, exist_ok=True)
            shutil.copy2(archive_path, final_path)
        print(
            f"\nWindows installer saved to: {final_path}\n"
            f"Please run the installer manually and ensure MiniZinc is on your PATH,\n"
            f"or extract it to: {MINIZINC_INSTALL_DIR}"
        )
        return

    # ---- Try latest release first -----------------------------------------
    ok, detail = _try_install_release(release_info, suffix, fmt)
    if ok:
        print(f"\nMiniZinc installed successfully!")
        print(f"  Version: {detail}")
        print("Autoguess will automatically detect it on next run.")
        return

    if detail != "glibc":
        print(f"\nMiniZinc binary failed to run: {detail}")
        sys.exit(1)

    # ---- glibc too old — try older releases automatically -----------------
    print(f"\nYour system glibc is too old for MiniZinc {tag}.")
    print("Searching for an older compatible release ...\n")

    import re as _re
    try:
        all_releases = _get_releases_list(per_page=30)
    except Exception:
        all_releases = []

    # Pick one release per minor-version line, skip the series we tried
    seen_minor = set()
    m0 = _re.match(r"(\d+\.\d+)", tag)
    if m0:
        seen_minor.add(m0.group(1))
    candidates = []
    for rel in all_releases:
        rtag = rel.get("tag_name", "")
        if rtag == tag or rel.get("prerelease") or rel.get("draft"):
            continue
        m = _re.match(r"(\d+\.\d+)", rtag)
        minor = m.group(1) if m else rtag
        if minor not in seen_minor:
            seen_minor.add(minor)
            candidates.append(rel)
        if len(candidates) >= 4:
            break

    for rel in candidates:
        rtag = rel.get("tag_name", "unknown")
        print(f"--- Trying MiniZinc {rtag} ---")
        ok, detail = _try_install_release(rel, suffix, fmt)
        if ok:
            print(f"\nMiniZinc {rtag} installed successfully!")
            print(f"  Version: {detail}")
            print("Autoguess will automatically detect it on next run.")
            return
        if detail == "glibc":
            print(f"  Still too new for your glibc.\n")
        else:
            print(f"  Failed: {detail}\n")
            break

    # ---- All pre-built releases failed — try snap -------------------------
    print("\nNo compatible pre-built MiniZinc version found.")
    print("Trying snap instead (bundles its own libraries) ...\n")
    if _install_via_system_package_manager():
        print("Autoguess will automatically detect it on next run.")
        return

    print(
        "\nOptions to resolve this:\n"
        "  1. sudo snap install minizinc --classic  (recommended)\n"
        "  2. Upgrade your OS to get glibc >= 2.34\n"
        "  3. Build MiniZinc from source: https://github.com/MiniZinc/MiniZincIDE\n"
    )
    sys.exit(1)


if __name__ == "__main__":
    install_minizinc()
