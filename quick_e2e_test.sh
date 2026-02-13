#!/bin/bash
# Quick E2E Test Runner
# This script starts the server and runs E2E tests in one command

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Quick E2E Test Runner ===${NC}"
echo ""

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}Warning: ffmpeg not found. Installing...${NC}"
    sudo apt-get update && sudo apt-get install -y ffmpeg
fi

# Check if server is running
if curl -s http://localhost:5050/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is already running${NC}"
else
    echo -e "${YELLOW}Starting server...${NC}"
    nohup python3 run_local.py > server.log 2>&1 &
    sleep 5

    if curl -s http://localhost:5050/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server started successfully${NC}"
    else
        echo -e "${RED}✗ Server failed to start${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Running E2E tests...${NC}"
echo ""

# Run E2E tests
export SKIP_E2E_TESTS="false"
export API_BASE_URL="http://localhost:5050"
export TEST_API_KEY="HbbRxQNiz3py27wRvyb-e9LSmFYIImMs0murWGNB1HE"
export DOWNLOAD_DIR_HOST="$(pwd)/downloads"

pytest tests/e2e/ -v --no-cov

echo ""
echo -e "${GREEN}=== E2E Tests Complete ===${NC}"
