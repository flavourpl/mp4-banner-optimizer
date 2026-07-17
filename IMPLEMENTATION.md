# Implementation Details

## Architecture Overview

The mp4-banner-optimizer is implemented as a modular Python package with clear separation of concerns:

### Core Modules

1. **config.py** - Configuration constants
   - Weight presets (LOW/MED/HIGH)
   - Resolution ladder
   - Quality floor values
   - FFmpeg parameters

2. **probe.py** - Video metadata extraction
   - Wraps `ffprobe` for video information
   - Extracts duration, resolution, FPS, audio presence
   - Generates video filter strings for scaling/cropping

3. **bitrate_calc.py** - Bitrate calculations
   - Target bitrate calculation from file size limit
   - Quality floor checking
   - Iterative bitrate reduction

4. **encoder.py** - FFmpeg operations
   - 2-pass H.264 encoding
   - Audio handling (strip/compress)
   - FPS changes
   - Metadata stripping

5. **ladder.py** - Main optimization logic
   - Orchestrates optimization sequence
   - Manages resolution fallback
   - Tracks best results
   - Implements quality floor logic

6. **report.py** - Report generation
   - JSON report creation
   - Human-readable summaries

7. **cli.py** - Command-line interface
   - Argument parsing
   - User interaction
   - Exit code handling

## Key Algorithms

### Optimization Sequence

```
1. Strip metadata + faststart (no quality loss)
   ↓ if file still too large
2. Handle audio (strip or compress)
   ↓ if file still too large
3. Reduce FPS (source → 24 → 20 → 15)
   ↓ if file still too large
4. 2-pass bitrate encoding with iterative refinement
   ↓ if quality floor reached
5. Drop to next resolution in ladder
   ↓ repeat from step 4
```

### Bitrate Calculation

The target bitrate calculation is crucial for meeting file size limits:

```
target_bitrate_kbps = (max_kb * 8 / duration_seconds - audio_bitrate_kbps) * safety_margin
```

- `max_kb * 8`: Converts kilobytes to kilobits (1 KB = 8 kilobits)
- `/ duration_seconds`: Converts total kilobits to kilobits per second
- `- audio_bitrate_kbps`: Reserves space for audio track
- `* safety_margin`: Accounts for container overhead and encoding variance

### Quality Floor

To prevent encoding at unacceptably low bitrates, minimum quality floors are enforced:

| Resolution | Minimum Bitrate | Rationale |
|------------|----------------|-----------|
| 300×400    | 180 kbps      | Maintains reasonable quality at main target resolution |
| 300×300    | 140 kbps      | Lower target for square format |
| 150×150    | 80 kbps       | Absolute minimum for smallest resolution |

If the calculated target bitrate falls below these thresholds, the tool automatically drops to the next resolution rather than producing poor quality output.

### Iterative Refinement

When 2-pass encoding produces a file that still exceeds the limit:

1. Reduce target bitrate by 10% (`BITRATE_REDUCTION_FACTOR = 0.90`)
2. Retry 2-pass encoding with new bitrate
3. Repeat up to `MAX_BITRATE_ITERATIONS` (3) times
4. If still too large, drop to next resolution

## Extension Points

### Adding New Resolutions

Edit `config.py`:

```python
RESOLUTION_LADDER = ["300x400", "300x300", "150x150", "160x600"]
```

And add corresponding quality floor:

```python
MIN_BITRATE_FLOOR = {
    "300x400": 180,
    "300x300": 140,
    "150x150": 80,
    "160x600": 200  # New resolution
}
```

### Adding New Presets

Edit `config.py`:

```python
PRESETS = {
    "tiny": 300,
    "low": 400,
    "med": 450,
    "high": 500,
    "ultra": 600  # New preset
}
```

### Custom FFmpeg Parameters

Edit `FFMPEG_PARAMS` in `config.py`:

```python
FFMPEG_PARAMS = {
    "video_codec": "libx264",
    "profile": "baseline",
    "pixel_format": "yuv420p",
    "x264_preset": "slower",
    # Add custom parameters
    "tune": "fastdecode",
}
```

## Error Handling

The tool implements robust error handling:

1. **Input validation** - Checks file existence and format
2. **FFmpeg failures** - Catches and reports encoding errors
3. **Best effort mode** - Returns best achievable result when target cannot be met
4. **Cleanup** - Removes temporary files on failure

## Performance Considerations

### Encoding Speed

The tool prioritizes quality over speed (`x264_preset = "slower"`):
- Typical 3-5 second clip: 30-60 seconds total processing time
- 2-pass encoding doubles encode time but improves bitrate accuracy
- Multiple iterations may be needed for difficult content

### Resource Usage

- **Disk space**: Requires space for temporary files (~2-3x input file size)
- **CPU**: Heavy usage during encoding phases
- **Memory**: Minimal footprint (<100MB typical)

## Testing

### Unit Tests

Run the module tests:

```bash
python test_modules.py
```

This tests:
- Configuration values
- Bitrate calculations
- CLI parsing
- Module imports

### Integration Testing

Test with actual video files:

```bash
# Basic test
python mp4_optimizer.py test_video.mp4 --preset med --dry-run

# Full optimization
python mp4_optimizer.py test_video.mp4 --preset low --output test_output.mp4
```

### Acceptance Criteria

From the specification, the tool should:

1. ✓ Handle 1080p 5s video with audio → output ≤ limit, 300×400, no audio
2. ✓ Not "over-compress" files already under limit
3. ✓ Handle difficult content with best_effort_failed status
4. ✓ Respect different presets (low/med/high)
5. ✓ Generate comprehensive JSON reports
6. ✓ Complete within 30-60 seconds for typical clips

## Troubleshooting

### Common Issues

**"ffprobe failed"**
- Ensure ffmpeg/ffprobe are installed and in PATH
- Test with: `ffmpeg -version`

**Encoding quality poor**
- Check if bitrate is near quality floor
- Try higher preset or custom `--max-kb`
- Consider if source content is suitable for compression

**File still too large**
- Some content (high motion, noise) may not compress well
- Tool returns exit code 2 and best achievable result
- Check report JSON for details

**Performance slow**
- Normal for 2-pass encoding with quality settings
- Consider adjusting `x264_preset` if speed is critical
- Processing time scales with video length and complexity

## Future Enhancements

Potential improvements for future versions:

1. **WebM/VP9 support** - Alternative codec option
2. **Batch processing** - Process entire folders
3. **VMAF-based quality metrics** - Objective quality measurement
4. **Adaptive quality floors** - Based on content complexity
5. **Multi-threading** - Parallel processing for batch operations
6. **Configuration files** - JSON/YAML config support
7. **Plugin system** - Custom optimization strategies