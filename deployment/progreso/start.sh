#!/bin/bash
# Start/restart MP4 Banner Optimizer on Progreso.pl
# Usage: ./start.sh [port]   (default port: 5000)

PORT="${1:-5000}"
cd "$(dirname "$0")"

echo "==> Creating working directories"
mkdir -p uploads outputs reports
chmod 755 uploads outputs reports

echo "==> Checking FFmpeg"
for binary in ffmpeg ffprobe; do
    if [ -x ~/bin/$binary ]; then
        echo "    ~/bin/$binary: $(~/bin/$binary -version 2>/dev/null | head -1)"
    else
        echo "    WARNING: ~/bin/$binary not found - see INSTALL.md step 3"
    fi
done

echo "==> Stopping old instances"
pkill -f web_app_prod.py 2>/dev/null && sleep 1 || true

echo "==> Starting on port $PORT"
export PYTHONIOENCODING=utf-8
PORT=$PORT nohup python3 web_app_prod.py > optimizer.log 2>&1 &
sleep 3

echo "==> Status"
if pgrep -f web_app_prod.py > /dev/null; then
    echo "    RUNNING (pid $(pgrep -f web_app_prod.py))"
    curl -s "http://127.0.0.1:$PORT/api/health" && echo
    echo ""
    echo "    Log: tail -f optimizer.log"
else
    echo "    FAILED TO START - last log lines:"
    tail -20 optimizer.log
    exit 1
fi
