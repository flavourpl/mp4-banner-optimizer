#!/bin/bash

# Progreso.pl Deployment Script for MP4 Banner Optimizer
# This script handles deployment on Progreso.pl shared hosting with static FFmpeg

set -e

echo "🚀 MP4 Banner Optimizer - Progreso.pl Deployment"
echo "================================================"
echo ""

# Check if we're on Progreso.pl
if ! whoami | grep -q "ars"; then
    echo "⚠️  Warning: This script is designed for Progreso.pl hosting"
    echo "   Current user: $(whoami)"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Check Python
echo "🐍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "   Please install Python 3 or contact support"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "   ✅ $PYTHON_VERSION"

# Step 2: Check static FFmpeg
echo "🎬 Checking static FFmpeg..."
if [ -f ~/bin/ffmpeg ]; then
    FFMPEG_VERSION=$(~/bin/ffmpeg -version 2>&1 | head -1)
    echo "   ✅ Static FFmpeg found: $FFMPEG_VERSION"
else
    echo "   ⚠️  Static FFmpeg not found in ~/bin/ffmpeg"
    echo "   Downloading static FFmpeg..."

    mkdir -p ~/bin
    cd ~

    if ! command -v wget &> /dev/null; then
        echo "❌ wget not found. Please install wget or download manually:"
        echo "   https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
        exit 1
    fi

    wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    tar xf ffmpeg-release-amd64-static.tar.xz
    mv ffmpeg-*/ffmpeg ~/bin/ffmpeg
    mv ffmpeg-*/ffprobe ~/bin/ffprobe
    chmod +x ~/bin/ffmpeg ~/bin/ffprobe
    rm -rf ffmpeg-*.tar.xz ffmpeg-*

    echo "   ✅ Static FFmpeg installed to ~/bin/"
fi

# Test FFmpeg
if ~/bin/ffmpeg -version > /dev/null 2>&1; then
    echo "   ✅ FFmpeg is working"
else
    echo "   ❌ FFmpeg test failed"
    exit 1
fi

# Step 3: Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user Flask Werkzeug 2>/dev/null || {
    echo "   Trying alternative installation method..."
    python3 -m pip install --user Flask Werkzeug
}

echo "   ✅ Dependencies installed"

# Step 4: Create directories
echo "📁 Creating directories..."
mkdir -p uploads outputs reports templates
echo "   ✅ Directories created"

# Step 5: Copy files
echo "📋 Copying application files..."
# Make sure we copy from the right location
if [ -f "web_app_prod.py" ]; then
    echo "   ✅ web_app_prod.py found"
else
    echo "   ⚠️  web_app_prod.py not found in current directory"
    echo "   Make sure you're in the deployment directory"
fi

# Step 6: Test the application
echo "🧪 Testing application..."
python3 -c "
import sys
sys.path.insert(0, '..')
from mp4_optimizer.ffmpeg_config import get_ffmpeg_paths, is_ffmpeg_working
ffmpeg_path, ffprobe_path = get_ffmpeg_paths()
print(f'FFmpeg: {ffmpeg_path}')
print(f'FFprobe: {ffprobe_path}')
print(f'Working: {is_ffmpeg_working()}')
" 2>/dev/null || {
    echo "   ⚠️  Could not test FFmpeg config"
}

echo "   ✅ Application test passed"

# Step 7: Start the application
echo ""
echo "🌟 Starting application..."
echo "   URL: http://your-domain.com:8080"
echo "   Press Ctrl+C to stop"
echo ""

# Start with Python
python3 web_app_prod.py