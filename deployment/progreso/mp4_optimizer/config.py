"""
Configuration constants for mp4-banner-optimizer.
All presets and limits are defined here for easy modification.
"""

# Weight presets in KB (1 KB = 1024 bytes)
PRESETS = {
    "low": 400,
    "med": 450,  # default
    "high": 500
}

# Resolution ladder - ordered from highest to lowest
RESOLUTION_LADDER = ["300x400", "300x300", "150x150"]

# Minimum acceptable video bitrates (quality floor)
# Tool won't encode below these values for respective resolutions
MIN_BITRATE_FLOOR = {
    "300x400": 180,  # kbps
    "300x300": 140,  # kbps
    "150x150": 80,   # kbps
}

# FPS reduction ladder
FPS_LADDER = None  # None means use source FPS, then: [24, 20, 15]
MIN_FPS = 15

# Encoding parameters
FFMPEG_PARAMS = {
    "video_codec": "libx264",
    "profile": "baseline",  # fallback to "main" if baseline fails
    "pixel_format": "yuv420p",
    "x264_preset": "slower",  # quality over speed
    "audio_codec": "aac",  # AAC-LC
    "audio_bitrate": 48,  # kbps, used when --keep-audio
    "container_format": "mp4",
    "movflags": "+faststart"
}

# Safety margin for bitrate calculation
SAFETY_MARGIN = 0.92

# Maximum additional bitrate iterations after initial encode
MAX_BITRATE_ITERATIONS = 3

# Bitrate reduction percentage when file exceeds limit
BITRATE_REDUCTION_FACTOR = 0.90  # reduce by 10%

# Default fit mode for aspect ratio handling
DEFAULT_FIT_MODE = "crop"  # options: crop, pad, stretch

# Default background color for pad mode
PAD_BACKGROUND_COLOR = "black"