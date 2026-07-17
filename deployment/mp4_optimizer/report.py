"""
Report generation for mp4-banner-optimizer.
Creates detailed JSON reports of the optimization process.
"""

import json
import os
from datetime import datetime
from typing import Dict


class OptimizationReport:
    """Generates and saves optimization reports."""

    def __init__(self):
        self.report_data: Dict = {}

    def generate(
        self,
        input_file: str,
        source_info: Dict,
        target_max_kb: int,
        result: Dict,
        output_file: str
    ) -> Dict:
        """
        Generate a complete optimization report.

        Args:
            input_file: Input file path
            source_info: Probed source video information
            target_max_kb: Target maximum file size in KB
            result: Optimization result from ladder
            output_file: Output file path

        Returns:
            Complete report dictionary
        """
        self.report_data = {
            "input_file": os.path.basename(input_file),
            "input_size_kb": source_info["size_kb"],
            "input_resolution": source_info["resolution"],
            "input_duration_s": source_info["duration_s"],
            "input_fps": source_info["fps"],
            "input_has_audio": source_info["has_audio"],
            "target_max_kb": target_max_kb,
            "final_size_kb": result.get("final_size_kb", 0),
            "final_resolution": result.get("final_resolution", "unknown"),
            "status": result.get("status", "unknown"),
            "output_file": os.path.basename(output_file),
            "timestamp": datetime.now().isoformat(),
            "iterations": result.get("iterations", [])
        }

        # Add warning if best effort failed
        if result.get("status") == "best_effort_failed":
            self.report_data["warning"] = (
                f"Could not fit under {target_max_kb}KB. "
                f"Best result: {result['final_size_kb']}KB at {result['final_resolution']}."
            )

        return self.report_data

    def save(self, report_path: str) -> str:
        """
        Save report to JSON file.

        Args:
            report_path: Path to save the report

        Returns:
            Path where report was saved
        """
        with open(report_path, 'w') as f:
            json.dump(self.report_data, f, indent=2)
        return report_path

    def print_summary(self):
        """Print a human-readable summary of the optimization result."""
        print("\n" + "="*50)
        print("OPTIMIZATION SUMMARY")
        print("="*50)
        print(f"Input:  {self.report_data['input_file']} ({self.report_data['input_size_kb']} KB, {self.report_data['input_resolution']})")
        print(f"Output: {self.report_data['output_file']} ({self.report_data['final_size_kb']} KB, {self.report_data['final_resolution']})")
        print(f"Target: {self.report_data['target_max_kb']} KB")
        print(f"Status: {self.report_data['status'].upper()}")

        if self.report_data['status'] == 'best_effort_failed':
            print(f"\n⚠️  {self.report_data.get('warning', 'Could not meet target file size')}")

        print(f"\nIterations: {len(self.report_data['iterations'])}")
        print("-" * 50)
        for i, iteration in enumerate(self.report_data['iterations'], 1):
            step = iteration['step']
            size = iteration['size_kb']
            bitrate = iteration.get('target_kbps', 'N/A')
            print(f"{i:2d}. {step:30s} → {size:4d} KB (bitrate: {bitrate})")
        print("="*50 + "\n")