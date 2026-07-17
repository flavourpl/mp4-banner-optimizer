"""
Video encoding operations using ffmpeg.
Handles 2-pass encoding, audio stripping, FPS changes, and scaling.
"""

import subprocess
import os
import sys
from typing import Optional
from mp4_optimizer.config import FFMPEG_PARAMS


def log(message, level="INFO"):
    """Log message to console."""
    print(f"[ENCODER] [{level}] {message}", flush=True)
    sys.stdout.flush()


class FFmpegEncoder:
    """Wrapper for ffmpeg encoding operations."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        """
        Initialize encoder with paths to ffmpeg binaries.

        Args:
            ffmpeg_path: Path to ffmpeg executable (default: "ffmpeg" from PATH)
            ffprobe_path: Path to ffprobe executable (default: "ffprobe" from PATH)
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

    def strip_metadata_and_faststart(self, input_path: str, output_path: str) -> bool:
        """
        Strip metadata and add faststart atom (no re-encoding).

        Args:
            input_path: Input video file
            output_path: Output video file

        Returns:
            True if successful
        """
        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-map_metadata", "-1",  # Strip metadata
            "-c", "copy",  # Copy streams without re-encoding
            "-movflags", FFMPEG_PARAMS["movflags"],  # Faststart
            "-y",  # Overwrite output
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def strip_audio(self, input_path: str, output_path: str) -> bool:
        """
        Remove audio track from video.

        Args:
            input_path: Input video file
            output_path: Output video file

        Returns:
            True if successful
        """
        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-an",  # Remove audio
            "-c:v", "copy",  # Copy video without re-encoding
            "-movflags", FFMPEG_PARAMS["movflags"],
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def compress_audio(self, input_path: str, output_path: str,
                       audio_bitrate: int = 48) -> bool:
        """
        Compress audio to low bitrate AAC (for --keep-audio option).

        Args:
            input_path: Input video file
            output_path: Output video file
            audio_bitrate: Audio bitrate in kbps (default: 48)

        Returns:
            True if successful
        """
        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-c:v", "copy",  # Copy video
            "-c:a", FFMPEG_PARAMS["audio_codec"],  # AAC codec
            "-b:a", f"{audio_bitrate}k",  # Audio bitrate
            "-ac", "1",  # Mono
            "-movflags", FFMPEG_PARAMS["movflags"],
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def change_fps(self, input_path: str, output_path: str,
                  target_fps: int) -> bool:
        """
        Change video frame rate with re-encoding.

        Args:
            input_path: Input video file
            output_path: Output video file
            target_fps: Target FPS

        Returns:
            True if successful
        """
        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
            "-r", str(target_fps),  # Target FPS
            "-c:v", FFMPEG_PARAMS["video_codec"],  # Re-encode with H.264
            "-profile:v", FFMPEG_PARAMS["profile"],
            "-pix_fmt", FFMPEG_PARAMS["pixel_format"],
            "-preset", FFMPEG_PARAMS["x264_preset"],
            "-crf", "23",  # Reasonable quality
            "-movflags", FFMPEG_PARAMS["movflags"],
            "-y",
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FPS change error: {result.stderr}")
        return result.returncode == 0

    def encode_2pass(
        self,
        input_path: str,
        output_path: str,
        target_bitrate_kbps: int,
        video_filters: str = "",
        keep_audio: bool = False,
        audio_bitrate_kbps: int = 48,
        fps: Optional[int] = None
    ) -> bool:
        """
        Perform 2-pass H.264 encode at target bitrate.

        Args:
            input_path: Input video file
            output_path: Output video file
            target_bitrate_kbps: Target video bitrate in kbps
            video_filters: Video filter string for scaling/cropping
            keep_audio: Whether to keep audio track
            audio_bitrate_kbps: Audio bitrate in kbps (if keeping audio)
            fps: Target FPS (None = keep source)

        Returns:
            True if successful
        """
        # Build common parameters
        common_params = [
            self.ffmpeg_path,
            "-i", input_path,
        ]

        if fps:
            common_params.extend(["-r", str(fps)])

        # Video filters
        if video_filters:
            common_params.extend(["-vf", video_filters])

        # Pass 1
        pass1_params = common_params + [
            "-c:v", FFMPEG_PARAMS["video_codec"],
            "-profile:v", FFMPEG_PARAMS["profile"],
            "-pix_fmt", FFMPEG_PARAMS["pixel_format"],
            "-preset", FFMPEG_PARAMS["x264_preset"],
            "-b:v", f"{target_bitrate_kbps}k",
            "-pass", "1",
            "-passlogfile", "ffmpeg2pass",
            "-f", "mp4",  # Use mp4 format for pass 1
            "-an",  # No audio in pass 1
            "-y",
            os.devnull  # Discard output
        ]

        # Pass 2
        pass2_params = common_params + [
            "-c:v", FFMPEG_PARAMS["video_codec"],
            "-profile:v", FFMPEG_PARAMS["profile"],
            "-pix_fmt", FFMPEG_PARAMS["pixel_format"],
            "-preset", FFMPEG_PARAMS["x264_preset"],
            "-b:v", f"{target_bitrate_kbps}k",
            "-pass", "2",
            "-passlogfile", "ffmpeg2pass",  # Same logfile for pass 2
            "-movflags", FFMPEG_PARAMS["movflags"],
            "-g", str(fps if fps else 30),  # Keyframe every 1 second
        ]

        # Pass 2
        pass2_params = common_params + [
            "-c:v", FFMPEG_PARAMS["video_codec"],
            "-profile:v", FFMPEG_PARAMS["profile"],
            "-pix_fmt", FFMPEG_PARAMS["pixel_format"],
            "-preset", FFMPEG_PARAMS["x264_preset"],
            "-b:v", f"{target_bitrate_kbps}k",
            "-pass", "2",
            "-movflags", FFMPEG_PARAMS["movflags"],
            "-g", str(fps if fps else 30),  # Keyframe every 1 second
        ]

        # Audio handling in pass 2
        if keep_audio:
            pass2_params.extend([
                "-c:a", FFMPEG_PARAMS["audio_codec"],
                "-b:a", f"{audio_bitrate_kbps}k",
                "-ac", "1"  # Mono
            ])
        else:
            pass2_params.append("-an")  # Remove audio

        pass2_params.extend(["-y", output_path])

        # Execute pass 1
        log("Starting pass 1...", "INFO")
        result1 = subprocess.run(pass1_params, capture_output=True, text=True)
        if result1.returncode != 0:
            log(f"Pass 1 failed: {result1.stderr[:500]}", "ERROR")
            return False
        log("Pass 1 completed", "INFO")

        # Execute pass 2
        log("Starting pass 2...", "INFO")
        result2 = subprocess.run(pass2_params, capture_output=True, text=True)
        if result2.returncode != 0:
            log(f"Pass 2 failed: {result2.stderr[:500]}", "ERROR")
            # Try fallback to single-pass encoding
            log("Attempting fallback to single-pass encoding...", "WARNING")
            return self._single_pass_fallback(
                input_path, output_path, target_bitrate_kbps,
                video_filters, keep_audio, audio_bitrate_kbps, fps
            )
        else:
            log("Pass 2 completed", "INFO")
        return result2.returncode == 0

    def encode_simple(
        self,
        input_path: str,
        output_path: str,
        video_filters: str = "",
        keep_audio: bool = False,
        audio_bitrate_kbps: int = 48,
        fps: Optional[int] = None
    ) -> bool:
        """
        Simple encoding with default quality (for testing/debugging).

        Args:
            input_path: Input video file
            output_path: Output video file
            video_filters: Video filter string
            keep_audio: Whether to keep audio track
            audio_bitrate_kbps: Audio bitrate in kbps
            fps: Target FPS

        Returns:
            True if successful
        """
        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
        ]

        if fps:
            cmd.extend(["-r", str(fps)])

        if video_filters:
            cmd.extend(["-vf", video_filters])

        cmd.extend([
            "-c:v", FFMPEG_PARAMS["video_codec"],
            "-profile:v", FFMPEG_PARAMS["profile"],
            "-pix_fmt", FFMPEG_PARAMS["pixel_format"],
            "-preset", FFMPEG_PARAMS["x264_preset"],
            "-crf", "23",  # Reasonable default quality
            "-movflags", FFMPEG_PARAMS["movflags"],
        ])

        if keep_audio:
            cmd.extend([
                "-c:a", FFMPEG_PARAMS["audio_codec"],
                "-b:a", f"{audio_bitrate_kbps}k",
                "-ac", "1"
            ])
        else:
            cmd.append("-an")

        cmd.extend(["-y", output_path])

        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def cleanup_pass_files(self):
        """Remove ffmpeg 2-pass temporary files."""
        for ext in ["log0", "log0-0"]:
            for file in [f"ffmpeg2pass.{ext}", f"ffmpeg2pass-{ext}"]:
                try:
                    if os.path.exists(file):
                        os.remove(file)
                except OSError:
                    pass

    def encode_single_pass(
        self,
        input_path: str,
        output_path: str,
        target_bitrate_kbps: int,
        video_filters: str = "",
        keep_audio: bool = False,
        audio_bitrate_kbps: int = 48,
        fps: Optional[int] = None
    ) -> bool:
        """Single-pass encoding at target bitrate."""
        log(f"Starting single-pass encoding at {target_bitrate_kbps} kbps", "INFO")

        cmd = [
            self.ffmpeg_path,
            "-i", input_path,
        ]

        if fps:
            cmd.extend(["-r", str(fps)])

        if video_filters:
            cmd.extend(["-vf", video_filters])

        cmd.extend([
            "-c:v", FFMPEG_PARAMS["video_codec"],
            "-profile:v", FFMPEG_PARAMS["profile"],
            "-pix_fmt", FFMPEG_PARAMS["pixel_format"],
            "-preset", FFMPEG_PARAMS["x264_preset"],
            "-b:v", f"{target_bitrate_kbps}k",
            "-movflags", FFMPEG_PARAMS["movflags"],
        ])

        if keep_audio:
            cmd.extend([
                "-c:a", FFMPEG_PARAMS["audio_codec"],
                "-b:a", f"{audio_bitrate_kbps}k",
                "-ac", "1"
            ])
        else:
            cmd.append("-an")

        cmd.extend(["-y", output_path])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            log("Single-pass encoding successful", "INFO")
        else:
            log(f"Single-pass encoding failed!", "ERROR")
            log(f"Command: {' '.join(cmd)}", "ERROR")
            log(f"Full stderr: {result.stderr}", "ERROR")
            log(f"Full stdout: {result.stdout}", "ERROR")
        return result.returncode == 0

    def _single_pass_fallback(
        self,
        input_path: str,
        output_path: str,
        target_bitrate_kbps: int,
        video_filters: str = "",
        keep_audio: bool = False,
        audio_bitrate_kbps: int = 48,
        fps: Optional[int] = None
    ) -> bool:
        """Fallback single-pass encoding when 2-pass fails."""
        log("Using single-pass encoding fallback", "INFO")
        return self.encode_single_pass(
            input_path, output_path, target_bitrate_kbps,
            video_filters, keep_audio, audio_bitrate_kbps, fps
        )


def get_file_size_kb(file_path: str) -> int:
    """
    Get file size in KB (1024 bytes).

    Args:
        file_path: Path to file

    Returns:
        File size in KB
    """
    return os.path.getsize(file_path) // 1024