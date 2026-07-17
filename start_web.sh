#!/bin/bash

# MP4 Banner Optimizer - Web Interface Launcher

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

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
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
echo "Open your browser to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python3 web_app.py