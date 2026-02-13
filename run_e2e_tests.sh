#!/bin/bash
# Script to run E2E tests for ID3 tag validation
#
# Usage:
#   ./run_e2e_tests.sh                    # Run all E2E tests
#   ./run_e2e_tests.sh --help             # Show help
#   ./run_e2e_tests.sh --setup-only       # Just setup environment, don't run tests

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
API_BASE_URL="${API_BASE_URL:-http://localhost:5050}"
TEST_API_KEY="${TEST_API_KEY:-test-api-key}"
DOWNLOAD_DIR_HOST="${DOWNLOAD_DIR_HOST:-./downloads}"
SKIP_E2E_TESTS="false"

function show_help() {
    echo "E2E Test Runner for ID3 Tag Validation"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help              Show this help message"
    echo "  --setup-only        Setup environment without running tests"
    echo "  --api-url URL       API endpoint (default: http://localhost:5050)"
    echo "  --api-key KEY       API key for authentication (default: test-api-key)"
    echo "  --download-dir DIR  Download directory path (default: ./downloads)"
    echo ""
    echo "Environment Variables:"
    echo "  API_BASE_URL        API endpoint"
    echo "  TEST_API_KEY        API key"
    echo "  DOWNLOAD_DIR_HOST   Download directory"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 --api-key my-secret-key"
    echo "  API_BASE_URL=http://localhost:8080 $0"
}

# Parse arguments
SETUP_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --api-url)
            API_BASE_URL="$2"
            shift 2
            ;;
        --api-key)
            TEST_API_KEY="$2"
            shift 2
            ;;
        --download-dir)
            DOWNLOAD_DIR_HOST="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== E2E Test Environment Setup ===${NC}"
echo ""
echo "API URL:          $API_BASE_URL"
echo "API Key:          ${TEST_API_KEY:0:10}..."
echo "Download Dir:     $DOWNLOAD_DIR_HOST"
echo ""

# Export environment variables
export API_BASE_URL
export TEST_API_KEY
export DOWNLOAD_DIR_HOST
export SKIP_E2E_TESTS

# Check if API is running
echo -e "${YELLOW}Checking API availability...${NC}"
if curl -s -f "${API_BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${RED}✗ API is not responding at ${API_BASE_URL}${NC}"
    echo ""
    echo "Please ensure the API server is running:"
    echo "  docker compose up -d"
    echo ""
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest not found${NC}"
    echo ""
    echo "Please install test dependencies:"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Create download directory if it doesn't exist
mkdir -p "$DOWNLOAD_DIR_HOST"

if [ "$SETUP_ONLY" = true ]; then
    echo -e "${GREEN}Environment setup complete!${NC}"
    echo ""
    echo "You can now run tests manually:"
    echo "  pytest tests/e2e/ -v -m e2e --no-cov"
    exit 0
fi

# Run E2E tests
echo ""
echo -e "${GREEN}=== Running E2E Tests ===${NC}"
echo ""

# Run with or without coverage based on preference
if [ "${WITH_COVERAGE:-false}" = "true" ]; then
    pytest tests/e2e/ -v -m e2e
else
    pytest tests/e2e/ -v -m e2e --no-cov
fi

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=== All E2E Tests Passed! ===${NC}"
else
    echo -e "${RED}=== E2E Tests Failed ===${NC}"
fi

exit $TEST_EXIT_CODE
