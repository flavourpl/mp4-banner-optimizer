"""
Video file probing using ffprobe.
Extracts duration, resolution, FPS, audio presence, and other metadata.
"""

import subprocess
import json
from typing import Dict, Optional, Tuple


def probe_video(file_path: str, ffprobe_path: str = "ffprobe") -> Dict:
    """
    Probe video file and extract metadata using ffprobe.

    Args:
        file_path: Path to the video file
        ffprobe_path: Path to ffprobe executable (default: "ffprobe" from PATH)

    Returns:
        Dictionary with video metadata:
        - duration_s: float, duration in seconds
        - width: int, video width in pixels
        - height: int, video height in pixels
        - fps: float, frames per second
        - has_audio: bool, whether video has audio track
        - resolution: str, "WxH" format
        - video_bitrate_kbps: int, estimated video bitrate in kbps
        - audio_bitrate_kbps: int, estimated audio bitrate in kbps (0 if no audio)
        - size_kb: int, file size in KB
    """
    cmd = [
        ffprobe_path,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,bit_rate",
        "-show_entries", "format=duration,size,bit_rate",
        "-of", "json",
        file_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe failed: {e.stderr}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse ffprobe output: {e}") from e

    # Extract video stream info
    stream = data.get("streams", [{}])[0]
    format_data = data.get("format", {})

    width = int(stream.get("width", 0))
    height = int(stream.get("height", 0))

    # Parse FPS from fraction like "30000/1001"
    fps_str = stream.get("r_frame_rate", "30/1")
    if "/" in fps_str:
        num, den = fps_str.split("/")
        fps = float(num) / float(den)
    else:
        fps = float(fps_str)

    # Duration
    duration_s = float(format_data.get("duration", 0))

    # Resolution string
    resolution = f"{width}x{height}"

    # File size in bytes, convert to KB (1024 bytes)
    size_bytes = int(format_data.get("size", 0))
    size_kb = size_bytes // 1024

    # Bitrate from format (overall)
    total_bitrate = int(format_data.get("bit_rate", 0))

    # Check for audio
    has_audio = check_audio_presence(file_path, ffprobe_path)

    # Estimate video bitrate (subtract audio if present)
    video_bitrate_kbps = total_bitrate // 1000  # convert to kbps
    audio_bitrate_kbps = 0

    if has_audio:
        audio_bitrate_kbps = estimate_audio_bitrate(file_path, ffprobe_path)
        video_bitrate_kbps = max(0, video_bitrate_kbps - audio_bitrate_kbps)

    return {
        "duration_s": duration_s,
        "width": width,
        "height": height,
        "fps": fps,
        "has_audio": has_audio,
        "resolution": resolution,
        "video_bitrate_kbps": video_bitrate_kbps,
        "audio_bitrate_kbps": audio_bitrate_kbps,
        "size_kb": size_kb
    }


def check_audio_presence(file_path: str, ffprobe_path: str = "ffprobe") -> bool:
    """Check if video file has an audio track."""
    cmd = [
        ffprobe_path,
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "csv=p=0",
        file_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def estimate_audio_bitrate(file_path: str, ffprobe_path: str = "ffprobe") -> int:
    """
    Estimate audio bitrate in kbps.
    Returns 0 if no audio track found.
    """
    cmd = [
        ffprobe_path,
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=bit_rate",
        "-of", "csv=p=0",
        file_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        bitrate_str = result.stdout.strip()
        if bitrate_str and bitrate_str != "N/A":
            return int(bitrate_str) // 1000  # convert to kbps
    except (subprocess.CalledProcessError, ValueError):
        pass

    return 0


def get_video_filters(current_resolution: str, target_resolution: str,
                      fit_mode: str, source_aspect: float) -> str:
    """
    Generate ffmpeg video filter chain for scaling/cropping to target resolution.

    Args:
        current_resolution: Current resolution string "WxH"
        target_resolution: Target resolution string "WxH"
        fit_mode: "crop", "pad", or "stretch"
        source_aspect: Source aspect ratio (width/height)

    Returns:
        ffmpeg filter string
    """
    if current_resolution == target_resolution:
        return ""

    target_w, target_h = map(int, target_resolution.split("x"))
    target_aspect = target_w / target_h

    if fit_mode == "stretch":
        # Simple scaling without aspect ratio preservation
        return f"scale={target_w}:{target_h}"

    elif fit_mode == "pad":
        # Scale to fit within target, then letterbox/pillarbox
        if source_aspect > target_aspect:
            # Source is wider - pillarbox
            scale_h = target_h
            scale_w = int(scale_h * source_aspect)
        else:
            # Source is taller - letterbox
            scale_w = target_w
            scale_h = int(scale_w / source_aspect)

        return f"scale={scale_w}:{scale_h},pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2"

    else:  # crop (default)
        # Scale to cover target area, then center crop
        # For crop to work, scaled image must be AT LEAST target size in both dimensions

        if source_aspect > target_aspect:
            # Source is wider (relative to target) - scale by height to ensure we have enough height
            scale_h = target_h
            scale_w = int(target_h * source_aspect)
        else:
            # Source is taller (relative to target) - scale by width to ensure we have enough width
            scale_w = target_w
            scale_h = int(target_w / source_aspect)

        # Ensure minimum dimensions to avoid negative crop
        scale_w = max(scale_w, target_w)
        scale_h = max(scale_h, target_h)

        return f"scale={scale_w}:{scale_h}:flags=bicubic,crop={target_w}:{target_h}:(iw-ow)/2:(ih-oh)/2"