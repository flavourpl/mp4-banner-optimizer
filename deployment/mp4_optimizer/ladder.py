"""
Optimization ladder logic.
Implements the sequential optimization steps and resolution fallback.
"""

import os
import sys
import time
from typing import List, Dict, Optional
from mp4_optimizer.config import (
    RESOLUTION_LADDER, MIN_BITRATE_FLOOR, MIN_FPS,
    MAX_BITRATE_ITERATIONS, BITRATE_REDUCTION_FACTOR
)
from mp4_optimizer.probe import probe_video, get_video_filters
from mp4_optimizer.bitrate_calc import (
    calculate_target_bitrate, check_quality_floor, reduce_bitrate_iteration
)
from mp4_optimizer.encoder import FFmpegEncoder, get_file_size_kb


def log(message, level="INFO"):
    """Log message to console with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)
    sys.stdout.flush()


class OptimizationLadder:
    """
    Manages the optimization process through the resolution ladder and optimization levers.
    """

    def __init__(self, encoder: Optional[FFmpegEncoder] = None):
        """
        Initialize optimization ladder.

        Args:
            encoder: FFmpegEncoder instance (creates new one if None)
        """
        self.encoder = encoder or FFmpegEncoder()
        self.iterations: List[Dict] = []
        self.best_result: Optional[Dict] = None

    def optimize(
        self,
        input_path: str,
        output_path: str,
        max_kb: int,
        keep_audio: bool = False,
        fit_mode: str = "crop",
        resolution_ladder: Optional[List[str]] = None,
        fps_ladder: Optional[List[int]] = None
    ) -> Dict:
        """
        Run optimization through the entire ladder.

        Args:
            input_path: Input video file
            output_path: Output video file (final result)
            max_kb: Maximum file size in KB
            keep_audio: Whether to keep audio track
            fit_mode: Aspect ratio handling mode (crop/pad/stretch)
            resolution_ladder: Custom resolution ladder (uses default if None)
            fps_ladder: Custom FPS ladder (uses default if None)

        Returns:
            Result dictionary with status and metadata
        """
        log("="*60, "INFO")
        log("Starting MP4 Banner Optimization", "INFO")
        log(f"Input file: {input_path}", "INFO")
        log(f"Target limit: {max_kb} KB", "INFO")
        log("="*60, "INFO")

        # Probe source video
        log("Probing source video...", "INFO")
        source_info = probe_video(input_path)
        source_aspect = source_info["width"] / source_info["height"]

        log(f"Source info: {source_info['resolution']}, {source_info['fps']:.1f} FPS, "
            f"{source_info['duration_s']:.1f}s, {source_info['size_kb']} KB", "INFO")
        log(f"Source has audio: {source_info['has_audio']}", "INFO")

        # Use default ladders if not provided
        if resolution_ladder is None:
            resolution_ladder = RESOLUTION_LADDER

        if fps_ladder is None:
            fps_ladder = self._build_fps_ladder(source_info["fps"])

        log(f"Resolution ladder: {resolution_ladder}", "INFO")
        log(f"FPS ladder: {fps_ladder}", "INFO")
        log(f"Keep audio: {keep_audio}", "INFO")
        log(f"Fit mode: {fit_mode}", "INFO")

        # Track best result across all attempts
        self.best_result = {
            "size_kb": float('inf'),
            "resolution": None,
            "path": None
        }

        # Try each resolution in the ladder
        for i, target_resolution in enumerate(resolution_ladder, 1):
            log(f"\n[{i}/{len(resolution_ladder)}] Trying resolution: {target_resolution}", "INFO")

            result = self._optimize_at_resolution(
                input_path=input_path,
                output_path=output_path,
                target_resolution=target_resolution,
                max_kb=max_kb,
                source_info=source_info,
                source_aspect=source_aspect,
                keep_audio=keep_audio,
                fit_mode=fit_mode,
                fps_ladder=fps_ladder
            )

            if result["status"] == "success":
                # Success at this resolution
                log(f"✅ SUCCESS at {target_resolution}! Final size: {result['size_kb']} KB", "INFO")
                self.encoder.cleanup_pass_files()
                return {
                    "status": "success",
                    "final_size_kb": result["size_kb"],
                    "final_resolution": target_resolution,
                    "iterations": self.iterations.copy()
                }

            # Update best result if this attempt was better
            if result["size_kb"] < self.best_result["size_kb"]:
                self.best_result.update({
                    "size_kb": result["size_kb"],
                    "resolution": target_resolution,
                    "path": result.get("path")
                })
                log(f"📊 New best result: {result['size_kb']} KB at {target_resolution}", "INFO")

        # If we get here, we couldn't fit under the limit at any resolution
        log(f"\n⚠️  Could not fit under {max_kb} KB at any resolution", "WARNING")
        log(f"Best result: {self.best_result['size_kb']} KB at {self.best_result['resolution']}", "WARNING")

        self.encoder.cleanup_pass_files()

        # Copy best result to output path
        if self.best_result["path"] and os.path.exists(self.best_result["path"]):
            import shutil
            shutil.copy(self.best_result["path"], output_path)
            log(f"Copied best result to: {output_path}", "INFO")

        return {
            "status": "best_effort_failed",
            "final_size_kb": self.best_result["size_kb"],
            "final_resolution": self.best_result["resolution"],
            "target_max_kb": max_kb,
            "iterations": self.iterations.copy()
        }

    def _optimize_at_resolution(
        self,
        input_path: str,
        output_path: str,
        target_resolution: str,
        max_kb: int,
        source_info: Dict,
        source_aspect: float,
        keep_audio: bool,
        fit_mode: str,
        fps_ladder: List[int]
    ) -> Dict:
        """
        Try to optimize at a specific resolution.

        Args:
            input_path: Input video file
            output_path: Output video file
            target_resolution: Target resolution string
            max_kb: Maximum file size in KB
            source_info: Probed video information
            source_aspect: Source aspect ratio
            keep_audio: Whether to keep audio
            fit_mode: Aspect ratio handling mode
            fps_ladder: List of FPS values to try

        Returns:
            Result dictionary for this resolution attempt
        """
        log(f"  Starting optimization at {target_resolution}", "INFO")

        current_input = input_path
        # Use unique temp file name for each step to avoid conflicts
        import uuid
        temp_id = str(uuid.uuid4())[:8]
        temp_output = f"{output_path}.temp_{temp_id}.mp4"
        temp_encoded = f"{output_path}.encoded_{temp_id}.mp4"  # Different name for encoded output

        # Generate video filters for this resolution
        # Use actual aspect ratio from source info
        actual_aspect = source_info["width"] / source_info["height"]
        video_filters = get_video_filters(
            source_info["resolution"],
            target_resolution,
            fit_mode,
            actual_aspect
        )

        if video_filters:
            log(f"  Video filters: {video_filters[:50]}...", "INFO")

        # Audio bitrate for target calculation
        audio_bitrate_kbps = 48 if keep_audio else 0

        # Step 1: Strip metadata and faststart
        log(f"  [Step 1/5] Strip metadata + faststart", "INFO")
        if self.encoder.strip_metadata_and_faststart(current_input, temp_output):
            size_kb = get_file_size_kb(temp_output)
            log(f"    Result: {size_kb} KB (target: {max_kb} KB)", "INFO")
            self._record_iteration("strip_metadata_faststart", size_kb)
            if size_kb <= max_kb:
                log(f"    ✅ FITS under limit! Saving to {output_path}", "INFO")
                os.replace(temp_output, output_path)
                return {"status": "success", "size_kb": size_kb, "path": output_path}
            current_input = temp_output
        else:
            # If stripping fails, use original input
            log(f"    ⚠️  Stripping failed, using original", "WARNING")
            current_input = input_path

        # Step 2: Handle audio
        log(f"  [Step 2/5] Handle audio (keep={keep_audio})", "INFO")
        if source_info["has_audio"]:
            if keep_audio:
                # Compress audio instead of stripping
                log(f"    Compressing audio to {audio_bitrate_kbps} kbps", "INFO")
                if self.encoder.compress_audio(current_input, temp_output):
                    size_kb = get_file_size_kb(temp_output)
                    log(f"    Result: {size_kb} KB (target: {max_kb} KB)", "INFO")
                    self._record_iteration("compress_audio", size_kb)
                    if size_kb <= max_kb:
                        log(f"    ✅ FITS under limit! Saving to {output_path}", "INFO")
                        os.replace(temp_output, output_path)
                        return {"status": "success", "size_kb": size_kb, "path": output_path}
                    current_input = temp_output
            else:
                # Strip audio
                log(f"    Stripping audio track", "INFO")
                if self.encoder.strip_audio(current_input, temp_output):
                    size_kb = get_file_size_kb(temp_output)
                    log(f"    Result: {size_kb} KB (target: {max_kb} KB)", "INFO")
                    self._record_iteration("strip_audio", size_kb)
                    if size_kb <= max_kb:
                        log(f"    ✅ FITS under limit! Saving to {output_path}", "INFO")
                        os.replace(temp_output, output_path)
                        return {"status": "success", "size_kb": size_kb, "path": output_path}
                    current_input = temp_output
        else:
            log(f"    No audio track to process", "INFO")

        # Step 3: Try FPS reduction ladder
        log(f"  [Step 3/5] FPS reduction ladder (source: {source_info['fps']:.1f} FPS)", "INFO")
        log(f"    ⚠️  Skipping FPS reduction for now - focusing on bitrate encoding", "INFO")
        log(f"    (FPS reduction will be added in future update)", "INFO")

        # Temporary: Skip FPS reduction to focus on getting basic encoding working
        # fps_attempted = 0
        # for fps in fps_ladder:
        #     if fps >= source_info["fps"]:
        #         log(f"    Skipping {fps} FPS (not reducing from source)", "INFO")
        #         continue  # Skip if not actually reducing
        #
        #     fps_attempted += 1
        #     log(f"    Trying {fps} FPS...", "INFO")
        #     if self.encoder.change_fps(current_input, temp_output, fps):
        #         size_kb = get_file_size_kb(temp_output)
        #         log(f"    Result: {size_kb} KB (target: {max_kb} KB)", "INFO")
        #         self._record_iteration(f"fps_{fps}", size_kb)
        #         if size_kb <= max_kb:
        #             log(f"    ✅ FITS under limit! Saving to {output_path}", "INFO")
        #             os.replace(temp_output, output_path)
        #             return {"status": "success", "size_kb": size_kb, "path": output_path}
        #         current_input = temp_output
        #     else:
        #         log(f"    ⚠️  FPS change failed", "WARNING")
        #
        # if fps_attempted == 0:
        #     log(f"    No FPS reduction performed (source FPS already low)", "INFO")

        # Step 4: Single-pass bitrate encoding with iterative refinement
        log(f"  [Step 4/5] Single-pass bitrate encoding", "INFO")

        # Calculate target bitrate
        target_bitrate = calculate_target_bitrate(
            max_kb=max_kb,
            duration_s=source_info["duration_s"],
            audio_bitrate_kbps=audio_bitrate_kbps
        )

        log(f"    Calculated target bitrate: {target_bitrate} kbps", "INFO")
        log(f"    Video duration: {source_info['duration_s']:.1f}s", "INFO")
        log(f"    Audio bitrate: {audio_bitrate_kbps} kbps", "INFO")

        # Check quality floor
        floor = MIN_BITRATE_FLOOR.get(target_resolution, 0)
        log(f"    Quality floor for {target_resolution}: {floor} kbps", "INFO")

        if not check_quality_floor(target_bitrate, target_resolution, MIN_BITRATE_FLOOR):
            log(f"    ❌ Bitrate {target_bitrate} kbps BELOW quality floor ({floor} kbps)", "WARNING")
            log(f"    Skipping to next resolution in ladder", "INFO")
            return {
                "status": "quality_floor_failed",
                "size_kb": float('inf'),
                "reason": "bitrate_below_floor"
            }

        # Try bitrate encoding with iterative refinement
        for iteration in range(MAX_BITRATE_ITERATIONS):
            current_bitrate = target_bitrate if iteration == 0 else reduce_bitrate_iteration(current_bitrate)
            log(f"    Iteration {iteration + 1}/{MAX_BITRATE_ITERATIONS}: bitrate={current_bitrate} kbps", "INFO")

            # Use single-pass encoding instead of 2-pass (more reliable)
            log(f"    Starting single-pass encode...", "INFO")
            encode_success = self.encoder.encode_single_pass(
                input_path=current_input,
                output_path=temp_encoded,  # Use different name to avoid conflict
                target_bitrate_kbps=current_bitrate,
                video_filters=video_filters,
                keep_audio=keep_audio,
                audio_bitrate_kbps=audio_bitrate_kbps
            )

            if encode_success:
                size_kb = get_file_size_kb(temp_encoded)
                log(f"    Encoding result: {size_kb} KB (target: {max_kb} KB)", "INFO")
                self._record_iteration(f"bitrate_single_{current_bitrate}kbps", size_kb, current_bitrate)

                if size_kb <= max_kb:
                    log(f"    ✅ FITS under limit! Saving to {output_path}", "INFO")
                    os.replace(temp_encoded, output_path)
                    return {"status": "success", "size_kb": size_kb, "path": output_path}
                else:
                    log(f"    Still {size_kb - max_kb} KB over limit, will try lower bitrate", "INFO")

                current_input = temp_encoded  # Use encoded file as next input
            else:
                log(f"    ❌ Encoding failed at bitrate {current_bitrate} kbps", "ERROR")
                break

        # If we get here, we couldn't fit at this resolution
        log(f"    ❌ Could not fit at {target_resolution} even with bitrate optimization", "WARNING")
        final_size = get_file_size_kb(current_input) if os.path.exists(current_input) else float('inf')
        log(f"    Best result at this resolution: {final_size} KB", "INFO")
        return {
            "status": "resolution_failed",
            "size_kb": final_size,
            "path": current_input
        }

    def _record_iteration(self, step: str, size_kb: int, target_kbps: Optional[int] = None):
        """Record an optimization step in the iteration history."""
        record = {"step": step, "size_kb": size_kb}
        if target_kbps is not None:
            record["target_kbps"] = target_kbps
        self.iterations.append(record)
        print(f"    Result: {size_kb} KB")

    def _build_fps_ladder(self, source_fps: float) -> List[int]:
        """Build FPS reduction ladder from source FPS."""
        ladder = [24, 20, 15]  # Default targets
        result = []

        for fps in ladder:
            if fps < MIN_FPS:
                continue
            if fps < source_fps:
                result.append(fps)

        return result