#!/bin/bash
# Stop FastAPI server and Docker services

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if docker-compose is available
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Stop Redis container if it exists
if [ -n "$DOCKER_COMPOSE_CMD" ] && [ -f "docker-compose.yml" ]; then
    echo -e "${BLUE}🐳 Stopping Redis container...${NC}"
    $DOCKER_COMPOSE_CMD stop redis 2>/dev/null || true
    echo -e "${GREEN}✅ Redis container stopped${NC}"
fi

# Kill any running uvicorn processes
echo -e "${BLUE}🛑 Stopping FastAPI server...${NC}"
pkill -f "uvicorn app.main:app" 2>/dev/null && echo -e "${GREEN}✅ Server stopped${NC}" || echo -e "${YELLOW}⚠️  No server process found${NC}"

echo ""
echo -e "${GREEN}✨ All services stopped${NC}"

