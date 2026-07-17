#!/bin/bash

# Quick deployment script for VPS
# Usage: ./deploy_vps.sh your_server_ip

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <server_ip>"
    echo "Example: $0 123.45.67.89"
    exit 1
fi

SERVER_IP=$1
PROJECT_NAME="mp4_optimizer"
REMOTE_USER="root"  # Change to your username if needed
REMOTE_DIR="/opt/$PROJECT_NAME"

echo "🚀 Deploying MP4 Banner Optimizer to VPS"
echo "============================================"
echo "Server: $SERVER_IP"
echo "User: $REMOTE_USER"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Check if SSH connection works
echo "🔍 Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 ${REMOTE_USER}@${SERVER_IP} "echo 'Connection successful'" 2>/dev/null; then
    echo "❌ Cannot connect to server!"
    echo "   Check:"
    echo "   - Server IP is correct"
    echo "   - SSH key is set up"
    echo "   - User has sudo privileges"
    exit 1
fi
echo "   ✅ SSH connection successful"

echo ""
echo "📦 Deploying files to server..."
# Create directory structure
ssh ${REMOTE_USER}@${SERVER_IP} "mkdir -p $REMOTE_DIR && cd $REMOTE_DIR && mkdir -p uploads outputs reports"

# Copy deployment files
scp -r deployment/* ${REMOTE_USER}@${SERVER_IP}:$REMOTE_DIR/

echo "   ✅ Files copied successfully"

echo ""
echo "🔧 Setting up environment on server..."
ssh ${REMOTE_USER}@${SERVER_IP} << 'ENDSSH'
cd $REMOTE_DIR

# Install FFmpeg if not present
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing FFmpeg..."
    apt update
    apt install -y ffmpeg
fi

# Install Python and dependencies
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    apt install -y python3 python3-pip python3-venv
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install Flask Werkzeug gunicorn

# Make start script executable
chmod +x start_prod.sh

echo "✅ Environment setup complete"
ENDSSH

echo ""
echo "🧪 Testing deployment..."
ssh ${REMOTE_USER}@${SERVER_IP} "cd $REMOTE_DIR && chmod +x start_prod.sh && ./start_prod.sh" &
START_PID=$!

echo "Waiting 5 seconds for startup..."
sleep 5

echo "Checking if service is running..."
if curl -s http://${SERVER_IP}:8080/health > /dev/null; then
    echo "✅ Service is running!"
    echo "🌐 Open your browser: http://${SERVER_IP}:8080"
else
    echo "❌ Service failed to start"
    echo "Check logs: ssh ${REMOTE_USER}@${SERVER_IP} 'journalctl -f -n 100'"
fi

echo ""
echo "============================================"
echo "✅ Deployment complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Test the web interface: http://${SERVER_IP}:8080"
echo "2. Upload a test video file"
echo "3. Check logs: ssh ${REMOTE_USER}@${SERVER_IP} 'tail -f /var/log/syslog'"
echo ""
echo "To manage the service:"
echo "- Stop: ssh ${REMOTE_USER}@${SERVER_IP} 'sudo systemctl stop mp4-optimizer'"
echo "- Start: ssh ${REMOTE_USER}@${SERVER_IP} 'sudo systemctl start mp4-optimizer'"
echo "- Restart: ssh ${REMOTE_USER}@${SERVER_IP} 'sudo systemctl restart mp4-optimizer'"
echo "- Logs: ssh ${REMOTE_USER}@${SERVER_IP} 'journalctl -u mp4-optimizer -f'"
echo ""