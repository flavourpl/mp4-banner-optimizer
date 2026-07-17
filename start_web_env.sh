#!/bin/bash

# MP4 Banner Optimizer - Web Interface Launcher (with virtual environment)

echo "🎬 MP4 Banner Optimizer - Web Interface"
echo "=========================================="
echo ""

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ Error: ffmpeg is not installed or not in PATH"
    echo "Please install ffmpeg from https://ffmpeg.org/download.html"
    exit 1
fi

echo "✅ ffmpeg found: $(ffmpeg -version | head -n 1)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "web_env" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv web_env
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source web_env/bin/activate
echo ""

# Install dependencies if needed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask and dependencies..."
    pip install Flask Werkzeug
    echo ""
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads outputs reports templates
echo ""

# Check if web_app.py exists
if [ ! -f "web_app.py" ]; then
    echo "❌ Error: web_app.py not found"
    echo "Please run this script from the project directory"
    exit 1
fi

echo "🚀 Starting web server..."
echo ""
echo "Open your browser to: http://localhost:5001"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python web_app.py