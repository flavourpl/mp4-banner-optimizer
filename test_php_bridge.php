#!/bin/bash
#
# PHP Bridge Test Script
# Tests all functionality through PHP proxy
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "  PHP Bridge Test Suite"
echo "================================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Test 1: Backend connectivity
echo "Test 1: Backend connectivity"
if curl -s http://127.0.0.1:5000/api/presets > /dev/null; then
    echo -e "${GREEN}✓ PASS: Backend responding${NC}"
else
    echo -e "${RED}✗ FAIL: Backend not responding${NC}"
    exit 1
fi

# Test 2: PHP availability
echo ""
echo "Test 2: PHP availability"
if php -v > /dev/null; then
    echo -e "${GREEN}✓ PASS: PHP available${NC}"
else
    echo -e "${RED}✗ FAIL: PHP not available${NC}"
    exit 1
fi

# Test 3: API endpoints through PHP (will test after deployment)
echo ""
echo "Test 3: API endpoints (requires deployment)"
echo "  These tests require PHP Bridge to be deployed:"
echo ""
echo "  GET /api/presets:"
echo "    curl -s https://vid.flavour.pl/api/presets"
echo ""
echo "  POST /api/upload (file upload):"
echo "    curl -F 'file=@test.mp4' https://vid.flavour.pl/api/upload"
echo ""
echo "  GET /api/status/{job_id}:"
echo "    curl -s https://vid.flavour.pl/api/status/{job_id}"
echo ""
echo "  GET /api/download/{job_id}:"
echo "    curl -O https://vid.flavour.pl/api/download/{job_id}"

# Test 4: File permissions
echo ""
echo "Test 4: File permissions"
REQUIRED_FILES=("index.php" "web_app_prod.py" "passenger_wsgi.py" "start_bridge.sh")
ALL_OK=true

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        if [ -x "$file" ] && [[ "$file" == *.sh ]]; then
            echo -e "${GREEN}✓ $file (executable)${NC}"
        elif [ -r "$file" ]; then
            echo -e "${GREEN}✓ $file (readable)${NC}"
        else
            echo -e "${YELLOW}⚠ $file (permission issues)${NC}"
            ALL_OK=false
        fi
    else
        echo -e "${RED}✗ $file (missing)${NC}"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✓ PASS: All files present and readable${NC}"
else
    echo -e "${YELLOW}⚠ WARNING: Some files have issues${NC}"
fi

# Test 5: Working directories
echo ""
echo "Test 5: Working directories"
REQUIRED_DIRS=("uploads" "outputs" "reports" "templates")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓ $dir${NC}"
    else
        echo -e "${YELLOW}⚠ $dir (missing - will be created)${NC}"
        mkdir -p "$dir"
    fi
done

echo ""
echo "================================================"
if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}Local tests PASSED${NC}"
else
    echo -e "${YELLOW}Some tests had warnings${NC}"
fi
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Upload files to server via FTP"
echo "2. Run: ./start_bridge.sh"
echo "3. Test with: curl -s https://vid.flavour.pl/api/presets"
echo ""
echo "Ready for deployment!"