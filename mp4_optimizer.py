#!/usr/bin/env python3
"""
mp4-banner-optimizer - Main entry point script
"""

import sys
import os

# Add the parent directory to the path so we can import mp4_optimizer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mp4_optimizer.cli import main

if __name__ == "__main__":
    main()