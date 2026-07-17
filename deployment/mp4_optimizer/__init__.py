"""
mp4-banner-optimizer
Optimize MP4 videos for HTML5 banner size limits.

A CLI tool that iteratively optimizes MP4 files to meet specific file size
requirements while maintaining the best possible visual quality.
"""

__version__ = "1.0.0"
__author__ = "Generated for KIMI Dynamic Ads"

from mp4_optimizer.config import (
    PRESETS,
    RESOLUTION_LADDER,
    MIN_BITRATE_FLOOR,
    MIN_FPS,
    FFMPEG_PARAMS
)
from mp4_optimizer.probe import probe_video
from mp4_optimizer.encoder import FFmpegEncoder
from mp4_optimizer.ladder import OptimizationLadder
from mp4_optimizer.report import OptimizationReport
from mp4_optimizer.cli import main

__all__ = [
    "PRESETS",
    "RESOLUTION_LADDER",
    "MIN_BITRATE_FLOOR",
    "MIN_FPS",
    "FFMPEG_PARAMS",
    "probe_video",
    "FFmpegEncoder",
    "OptimizationLadder",
    "OptimizationReport",
    "main"
]