"""
FFmpeg path configuration for different deployment environments.
Automatically detects static FFmpeg builds and system installations.
"""

import os
import subprocess
from pathlib import Path


def find_ffmpeg_binaries():
    """
    Find working FFmpeg and FFprobe binaries.
    Checks in order: static build in ~/bin, system PATH, environment variables.

    Returns:
        tuple: (ffmpeg_path, ffprobe_path) or (None, None) if not found
    """
    # Priority 1: Environment variables (for custom deployments)
    ffmpeg_env = os.environ.get("FFMPEG_PATH")
    ffprobe_env = os.environ.get("FFPROBE_PATH")

    if ffmpeg_env and ffprobe_env:
        if os.path.exists(ffmpeg_env) and os.path.exists(ffprobe_env):
            return ffmpeg_env, ffprobe_env

    # Priority 2: Static build in ~/bin (for Progreso.pl and shared hosting)
    home_bin = Path.home() / "bin"
    static_ffmpeg = home_bin / "ffmpeg"
    static_ffprobe = home_bin / "ffprobe"

    if static_ffmpeg.exists() and static_ffprobe.exists():
        print(f"[CONFIG] Using static FFmpeg build: {static_ffmpeg}")
        return str(static_ffmpeg), str(static_ffprobe)

    # Priority 3: System PATH
    try:
        ffmpeg_path = subprocess.check_output(
            ["which", "ffmpeg"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        ffprobe_path = subprocess.check_output(
            ["which", "ffprobe"],
            stderr=subprocess.DEVNULL
        ).decode().strip()

        if ffmpeg_path and ffprobe_path:
            print(f"[CONFIG] Using system FFmpeg: {ffmpeg_path}")
            return ffmpeg_path, ffprobe_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Priority 4: Fallback to default names (might fail but gives clear error)
    print("[CONFIG] WARNING: FFmpeg not found, will use default paths (may fail)")
    return "ffmpeg", "ffprobe"


def test_ffmpeg(ffmpeg_path, ffprobe_path):
    """
    Test if FFmpeg and FFprobe are working.

    Args:
        ffmpeg_path: Path to ffmpeg binary
        ffprobe_path: Path to ffprobe binary

    Returns:
        bool: True if both are working
    """
    try:
        # Test FFmpeg
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"[CONFIG] FFmpeg test failed: {result.stderr.decode()[:200]}")
            return False

        # Test FFprobe
        result = subprocess.run(
            [ffprobe_path, "-version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            print(f"[CONFIG] FFprobe test failed: {result.stderr.decode()[:200]}")
            return False

        print("[CONFIG] ✅ FFmpeg and FFprobe are working")
        return True

    except Exception as e:
        print(f"[CONFIG] ❌ FFmpeg test failed: {e}")
        return False


# Auto-detect paths at module import
FFMPEG_PATH, FPROBE_PATH = find_ffmpeg_binaries()

# Verify they work
FFMPEG_WORKING = test_ffmpeg(FFMPEG_PATH, FPROBE_PATH)


def get_ffmpeg_paths():
    """
    Get the detected FFmpeg paths.
    Use this to initialize FFmpegEncoder and probe functions.

    Returns:
        tuple: (ffmpeg_path, ffprobe_path)
    """
    return FFMPEG_PATH, FPROBE_PATH


def is_ffmpeg_working():
    """
    Check if FFmpeg is properly configured and working.

    Returns:
        bool: True if FFmpeg is available and working
    """
    return FFMPEG_WORKING