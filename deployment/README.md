# mp4-banner-optimizer

CLI tool to optimize MP4 videos for HTML5 banner size limits.

## Overview

This tool iteratively optimizes MP4 files (typically 3-5 second clips for HTML5 advertising banners) to meet specific file size requirements while maintaining the best possible visual quality.

**Key features:**
- Target specific file size limits (400KB, 450KB, 500KB presets or custom)
- Automatic resolution fallback ladder (300×400 → 300×300 → 150×150)
- Multiple optimization levers applied intelligently
- Detailed JSON reports for debugging and tuning
- Aspect ratio handling (crop, pad, stretch)
- Audio handling (strip or compress)

## Requirements

- Python 3.6+
- **ffmpeg** and **ffprobe** must be installed and available in PATH
  - Download from: https://ffmpeg.org/download.html

## Installation

1. Clone this repository
2. Ensure ffmpeg/ffprobe are in your PATH
3. No Python package installation needed (uses standard library only)

```bash
# Verify ffmpeg installation
ffmpeg -version
ffprobe -version
```

## Usage

### Basic usage

```bash
python mp4_optimizer.py input.mp4 --preset med --output output.mp4
```

### Command-line options

```
Usage: mp4_optimizer.py INPUT.mp4 [OPTIONS]

Options:
  --preset {low,med,high}      Weight limit preset (default: med)
                               low=400KB, med=450KB, high=500KB
  --max-kb N                   Custom limit in KB (overrides --preset)
  --output PATH                Output file path
  --fit {crop,pad,stretch}     Aspect ratio handling (default: crop)
  --keep-audio                 Keep audio track (default: remove)
  --resolution-ladder STR       Custom resolution ladder
  --min-fps N                   Minimum FPS (default: 15)
  --report PATH                Save JSON report to path
  --dry-run                    Show plan without encoding
```

### Examples

```bash
# Basic optimization with medium preset (450KB)
python mp4_optimizer.py clip.mp4 --preset med --output clip_450kb.mp4

# Custom size limit
python mp4_optimizer.py banner.mp4 --max-kb 420

# Keep audio and use letterbox (pad) mode
python mp4_optimizer.py video.mp4 --keep-audio --fit pad

# Custom resolution ladder
python mp4_optimizer.py ad.mp4 --resolution-ladder "300x400,300x300,150x150"

# Dry run to see what would happen
python mp4_optimizer.py test.mp4 --preset low --dry-run
```

## How it works

The optimizer applies a series of techniques in order, testing after each step whether the file meets the size limit:

### Optimization levers (from least to most impactful)

1. **Strip metadata + faststart** (no quality loss)
   - Removes metadata and moves moov atom to start of file

2. **Audio handling**
   - Default: Remove audio track completely
   - `--keep-audio`: Compress to 48kbps mono AAC

3. **FPS reduction**
   - Reduce frame rate: source → 24 → 20 → 15 fps minimum

4. **2-pass bitrate encoding** (main optimization)
   - Calculate target bitrate from desired file size
   - Encode with H.264 at calculated bitrate
   - Iterative refinement if still too large

5. **Resolution fallback**
   - If quality floor is reached, step down resolution:
   - 300×400 → 300×300 → 150×150

### Quality floor

The tool won't encode below minimum sensible bitrates:
- 300×400: 180 kbps minimum
- 300×300: 140 kbps minimum  
- 150×150: 80 kbps minimum

If target bitrate falls below these thresholds, it automatically drops to the next resolution.

## Output

The tool generates:

1. **Optimized MP4 file** - The best result achieved
2. **JSON report** (`<output>.report.json`) - Detailed iteration history

### Example report

```json
{
  "input_file": "clip.mp4",
  "input_size_kb": 2140,
  "input_resolution": "1080x1350",
  "input_duration_s": 4.2,
  "target_max_kb": 450,
  "final_size_kb": 438,
  "final_resolution": "300x400",
  "status": "success",
  "iterations": [
    {"step": "strip_metadata_faststart", "size_kb": 2138},
    {"step": "strip_audio", "size_kb": 1980},
    {"step": "fps_24", "size_kb": 1750},
    {"step": "bitrate_2pass_762kbps", "target_kbps": 762, "size_kb": 438}
  ]
}
```

## Exit codes

- `0` - Success (file meets target size limit)
- `1` - Error (invalid input, ffmpeg failure, etc.)
- `2` - Best effort failed (could not meet limit, but returned best result)

## Architecture

```
mp4_optimizer/
├── __init__.py           # Package initialization
├── cli.py                # CLI argument parsing and entry point
├── probe.py              # ffprobe wrapper for video metadata
├── encoder.py            # ffmpeg wrapper for encoding operations
├── ladder.py             # Main optimization logic
├── bitrate_calc.py       # Bitrate calculations
├── report.py             # Report generation
└── config.py             # Configuration constants
```

## Integration with existing tools

This tool can be integrated into existing banner generation pipelines:

```bash
# In your generator script
python mp4_optimizer.py assets/video.mp4 --preset high --output banners/video_opt.mp4

# Check exit code
if [ $? -eq 0 ]; then
    echo "Optimization successful"
elif [ $? -eq 2 ]; then
    echo "Warning: Could not meet target, but got best effort"
else
    echo "Error: Optimization failed"
fi
```

## Troubleshooting

**"ffprobe failed" error:**
- Ensure ffmpeg/ffprobe are installed and in PATH
- Test with: `ffmpeg -version`

**File still too large:**
- Try a higher preset (high) or custom `--max-kb`
- Some content (high motion, noise) may not fit even at lowest settings
- The tool will return exit code 2 and the best achievable result

**Encoding fails:**
- Check source file is valid MP4
- Ensure sufficient disk space for temporary files
- Try with `--dry-run` first to validate parameters

## License

This tool was developed for KIMI Dynamic Ads projects.

## Contributing

To modify presets or behavior, edit `mp4_optimizer/config.py`. All constants are centralized there for easy adjustment.