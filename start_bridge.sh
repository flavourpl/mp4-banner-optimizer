#!/bin/bash
#
# MP4 Banner Optimizer - PHP Bridge Startup Script
# Starts Flask backend and verifies PHP proxy operation
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "  MP4 Banner Optimizer - PHP Bridge Startup"
echo "================================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if Flask app is already running
if pgrep -f "web_app_prod.py" > /dev/null; then
    echo -e "${YELLOW}Flask app already running${NC}"
    echo "Stopping existing instance..."
    pkill -f web_app_prod.py || true
    sleep 2
fi

# Start Flask backend
echo "Starting Flask backend on port 5000..."
PORT=5000 nohup python3 web_app_prod.py > optimizer.log 2>&1 &
FLASK_PID=$!

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Check if Flask process is running
if pgrep -f "web_app_prod.py" > /dev/null; then
    echo -e "${GREEN}✓ Flask backend started successfully${NC}"
    echo "  PID: $(pgrep -f 'web_app_prod.py' | head -1)"
else
    echo -e "${RED}✗ Flask backend failed to start${NC}"
    echo "Check optimizer.log for details"
    exit 1
fi

# Test local Flask connectivity
echo ""
echo "Testing local Flask connectivity..."
if curl -s http://127.0.0.1:5000/api/presets > /dev/null; then
    echo -e "${GREEN}✓ Flask backend responding locally${NC}"
    PRESETS=$(curl -s http://127.0.0.1:5000/api/presets)
    echo "  Presets: $PRESETS"
else
    echo -e "${RED}✗ Flask backend not responding${NC}"
    exit 1
fi

# Test PHP availability
echo ""
echo "Checking PHP availability..."
if command -v php > /dev/null; then
    PHP_VERSION=$(php -v | head -1)
    echo -e "${GREEN}✓ PHP available${NC}"
    echo "  $PHP_VERSION"
else
    echo -e "${RED}✗ PHP not found${NC}"
    exit 1
fi

# Test PHP modules
echo ""
echo "Checking PHP modules..."
PHP_MODULES=("curl" "json" "mbstring")
ALL_MODULES_OK=true

for module in "${PHP_MODULES[@]}"; do
    if php -m | grep -q "$module"; then
        echo -e "${GREEN}✓ $module${NC}"
    else
        echo -e "${RED}✗ $module missing${NC}"
        ALL_MODULES_OK=false
    fi
done

if [ "$ALL_MODULES_OK" = false ]; then
    echo -e "${RED}PHP modules missing - bridge may not work properly${NC}"
    exit 1
fi

# Verify required files exist
echo ""
echo "Checking required files..."
REQUIRED_FILES=("index.php" "web_app_prod.py" "passenger_wsgi.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file missing${NC}"
        exit 1
    fi
done

# Final status
echo ""
echo "================================================"
echo -e "${GREEN}PHP Bridge startup complete!${NC}"
echo "================================================"
echo ""
echo "Services status:"
echo "  • Flask backend:  http://127.0.0.1:5000"
echo "  • PHP bridge:     https://vid.flavour.pl"
echo "  • Process ID:     $(pgrep -f 'web_app_prod.py' | head -1)"
echo ""
echo "Log files:"
echo "  • Flask:  optimizer.log"
echo "  • PHP:    php_bridge.log"
echo ""
echo -e "${GREEN}Ready to process video uploads!${NC}"
echo ""
echo "Monitor logs with:"
echo "  tail -f optimizer.log"
echo "  tail -f php_bridge.log"