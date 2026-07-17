"""
Bitrate calculation utilities for mp4-banner-optimizer.
"""

from mp4_optimizer.config import SAFETY_MARGIN


def calculate_target_bitrate(
    max_kb: int,
    duration_s: float,
    audio_bitrate_kbps: int = 0,
    safety_margin: float = SAFETY_MARGIN
) -> int:
    """
    Calculate target video bitrate to fit within file size limit.

    Formula:
    target_bitrate_kbps = (max_kb * 8 / duration_seconds - audio_bitrate_kbps) * safety_margin

    Note: 1 KB = 8 kilobits, so max_kb * 8 converts kilobytes to kilobits

    Args:
        max_kb: Maximum file size in KB
        duration_s: Video duration in seconds
        audio_bitrate_kbps: Audio bitrate in kbps (0 if no audio)
        safety_margin: Safety factor (default 0.92) to account for container overhead

    Returns:
        Target video bitrate in kbps (integer)
    """
    if duration_s <= 0:
        raise ValueError("Duration must be positive")

    # Total available bitrate for the file
    # max_kb * 8 converts kilobytes to kilobits
    total_bitrate_kbps = (max_kb * 8) / duration_s

    # Subtract audio bitrate
    video_bitrate_kbps = total_bitrate_kbps - audio_bitrate_kbps

    # Apply safety margin for container overhead and encoding variance
    target_bitrate = int(video_bitrate_kbps * safety_margin)

    return max(0, target_bitrate)


def check_quality_floor(target_bitrate: int, resolution: str,
                        min_bitrate_floor: dict) -> bool:
    """
    Check if target bitrate is above minimum acceptable quality floor.

    Args:
        target_bitrate: Calculated target bitrate in kbps
        resolution: Resolution string (e.g., "300x400")
        min_bitrate_floor: Dictionary mapping resolutions to minimum bitrates

    Returns:
        True if bitrate is acceptable (above floor), False if too low
    """
    floor = min_bitrate_floor.get(resolution, 0)
    return target_bitrate >= floor


def reduce_bitrate_iteration(current_bitrate: int, factor: float = 0.90) -> int:
    """
    Reduce bitrate by a factor for iterative refinement.

    Args:
        current_bitrate: Current bitrate in kbps
        factor: Reduction factor (default 0.90 = 10% reduction)

    Returns:
        New bitrate in kbps
    """
    return max(1, int(current_bitrate * factor))