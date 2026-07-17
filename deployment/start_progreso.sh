#!/bin/bash

# Quick start script for Progreso.pl hosting
# This starts the MP4 Banner Optimizer with static FFmpeg

echo "🚀 Starting MP4 Banner Optimizer on Progreso.pl"
echo "=============================================="
echo ""

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check static FFmpeg
if [ -f ~/bin/ffmpeg ]; then
    echo "✅ Using static FFmpeg: ~/bin/ffmpeg"
    export FFMPEG_PATH=~/bin/ffmpeg
    export FPROBE_PATH=~/bin/ffprobe
else
    echo "❌ Static FFmpeg not found in ~/bin/"
    echo "Please run: ./deploy_progreso.sh"
    exit 1
fi

# Set port (you can change this if needed)
export PORT=${PORT:-8080}

echo "🌐 Starting server on port $PORT"
echo "Access at: http://your-domain.com:$PORT"
echo ""
echo "Press Ctrl+C to stop"
echo "----------------------------------------------"

# Start the application
python3 web_app_prod.py