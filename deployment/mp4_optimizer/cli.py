"""
CLI interface for mp4-banner-optimizer.
"""

import argparse
import os
import sys
from typing import List
from mp4_optimizer.config import PRESETS, RESOLUTION_LADDER, DEFAULT_FIT_MODE
from mp4_optimizer.probe import probe_video
from mp4_optimizer.ladder import OptimizationLadder
from mp4_optimizer.encoder import FFmpegEncoder, get_file_size_kb
from mp4_optimizer.report import OptimizationReport


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Optimize MP4 videos for HTML5 banner size limits.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s clip.mp4 --preset high --output clip_450kb.mp4
  %(prog)s input.mp4 --max-kb 420 --fit pad
  %(prog)s banner.mp4 --preset low --keep-audio --report banner_report.json
        """
    )

    # Required arguments
    parser.add_argument(
        "input",
        help="Input MP4 video file"
    )

    # Optional arguments
    parser.add_argument(
        "--preset",
        choices=["low", "med", "high"],
        default="med",
        help="Weight limit preset (default: med)"
    )

    parser.add_argument(
        "--max-kb",
        type=int,
        help="Override preset with custom limit in KB"
    )

    parser.add_argument(
        "--output",
        help="Output file path (default: <input>_optimized.mp4)"
    )

    parser.add_argument(
        "--fit",
        choices=["crop", "pad", "stretch"],
        default=DEFAULT_FIT_MODE,
        help="Aspect ratio handling (default: crop)"
    )

    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Keep audio track (default: remove audio)"
    )

    parser.add_argument(
        "--resolution-ladder",
        help='Custom resolution ladder (e.g., "300x400,300x300,150x150")'
    )

    parser.add_argument(
        "--min-fps",
        type=int,
        default=15,
        help="Minimum FPS (default: 15)"
    )

    parser.add_argument(
        "--report",
        help="Save JSON report to specified path"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show optimization plan without encoding"
    )

    return parser.parse_args()


def parse_resolution_ladder(ladder_str: str) -> List[str]:
    """Parse resolution ladder from comma-separated string."""
    resolutions = [r.strip() for r in ladder_str.split(",")]
    # Validate format
    for res in resolutions:
        try:
            w, h = res.split("x")
            int(w), int(h)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Invalid resolution format: {res}. Expected WxH format."
            )
    return resolutions


def main():
    """Main entry point for CLI."""
    args = parse_arguments()

    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not args.input.lower().endswith('.mp4'):
        print(f"Warning: Input file may not be MP4 format: {args.input}")

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        output_path = f"{base}_optimized.mp4"

    # Determine target size limit
    if args.max_kb:
        max_kb = args.max_kb
    else:
        max_kb = PRESETS[args.preset]

    # Parse resolution ladder if provided
    resolution_ladder = None
    if args.resolution_ladder:
        try:
            resolution_ladder = parse_resolution_ladder(args.resolution_ladder)
        except argparse.ArgumentTypeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Probe source video
    print(f"Probing source video: {args.input}")
    try:
        source_info = probe_video(args.input)
        print(f"Source: {source_info['resolution']}, {source_info['fps']:.1f} FPS, "
              f"{source_info['duration_s']:.1f}s, {source_info['size_kb']} KB")
        if source_info['has_audio']:
            print(f"Audio track present: {source_info['audio_bitrate_kbps']} kbps")
    except Exception as e:
        print(f"Error probing video: {e}", file=sys.stderr)
        sys.exit(1)

    # Dry run mode
    if args.dry_run:
        print("\nDry run mode - optimization plan:")
        print(f"  Target limit: {max_kb} KB")
        print(f"  Resolution ladder: {resolution_ladder or RESOLUTION_LADDER}")
        print(f"  Fit mode: {args.fit}")
        print(f"  Keep audio: {args.keep_audio}")
        print(f"  Output: {output_path}")
        print("\nNo encoding performed (dry run)")
        sys.exit(0)

    # Run optimization
    print(f"\nStarting optimization (target: {max_kb} KB)...")

    encoder = FFmpegEncoder()
    ladder = OptimizationLadder(encoder)

    try:
        result = ladder.optimize(
            input_path=args.input,
            output_path=output_path,
            max_kb=max_kb,
            keep_audio=args.keep_audio,
            fit_mode=args.fit,
            resolution_ladder=resolution_ladder
        )
    except Exception as e:
        print(f"Error during optimization: {e}", file=sys.stderr)
        encoder.cleanup_pass_files()
        sys.exit(1)

    # Generate report
    report = OptimizationReport()
    report.generate(
        input_file=args.input,
        source_info=source_info,
        target_max_kb=max_kb,
        result=result,
        output_file=output_path
    )

    # Print summary
    report.print_summary()

    # Save report if requested
    if args.report:
        report_path = args.report
    else:
        report_path = f"{output_path}.report.json"

    report.save(report_path)
    print(f"Report saved to: {report_path}")

    # Exit with appropriate code
    if result["status"] == "success":
        print(f"✓ Optimization successful: {output_path}")
        sys.exit(0)
    else:
        print(f"⚠️  Could not meet target limit (best effort returned)")
        sys.exit(2)


if __name__ == "__main__":
    main()