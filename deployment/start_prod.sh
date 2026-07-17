#!/bin/bash

# Production startup script for MP4 Banner Optimizer
# This script starts the application in production mode

set -e  # Exit on any error

echo "🚀 Starting MP4 Banner Optimizer - Production Mode"
echo "============================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: Running as root is not recommended!"
    echo "   Consider creating a dedicated user."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
echo "🐍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "   Install with: apt install python3"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "   Found Python $PYTHON_VERSION"

# Check FFmpeg installation
echo "🎬 Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is not installed!"
    echo "   Install with: apt install ffmpeg"
    exit 1
fi
FFMPEG_VERSION=$(ffmpeg -version | head -1)
echo "   Found $FFMPEG_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "   Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install Flask Werkzeug gunicorn
echo "   Dependencies installed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs reports
echo "   Directories created"

# Check if directories are writable
echo "🔍 Checking directory permissions..."
for dir in uploads outputs reports; do
    if [ -w "$dir" ]; then
        echo "   ✅ $dir is writable"
    else
        echo "   ❌ $dir is not writable!"
        echo "      Run: chmod 755 $dir"
        exit 1
    fi
done

# Check if port is available
PORT=8080
if netstat -tuln | grep -q ":$PORT "; then
    echo "⚠️  Port $PORT is already in use!"
    echo "   Choose a different port or stop the conflicting service."
    exit 1
fi
echo "   ✅ Port $PORT is available"

# Start the application
echo ""
echo "🌟 Starting application..."
echo "   URL: http://localhost:$PORT"
echo "   Press Ctrl+C to stop"
echo ""

# Use Gunicorn for production
if command -v gunicorn &> /dev/null; then
    echo "🚀 Using Gunicorn (production server)"
    gunicorn --config gunicorn_config.py wsgi:app
else
    echo "🧪 Using Flask dev server (not recommended for production)"
    python3 web_app_prod.py
fi