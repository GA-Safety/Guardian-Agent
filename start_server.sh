#!/bin/bash
# Start FastAPI development server

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

# Check if Docker is available
DOCKER_AVAILABLE=false
if command -v docker &> /dev/null && docker info &> /dev/null; then
    DOCKER_AVAILABLE=true
fi

# Check if docker-compose is available
DOCKER_COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo "Run ./setup.sh first to create the virtual environment"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo -e "${RED}❌ backend directory not found${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "The server may fail to start without proper database configuration"
    echo ""
fi

# Default values
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-true}"
START_REDIS="${START_REDIS:-true}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --no-reload)
            RELOAD="false"
            shift
            ;;
        --no-redis)
            START_REDIS="false"
            shift
            ;;
        --help)
            echo "Usage: ./start_server.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --host HOST       Host to bind to (default: 127.0.0.1)"
            echo "  --port PORT       Port to bind to (default: 8000)"
            echo "  --no-reload       Disable auto-reload on code changes"
            echo "  --no-redis        Don't start Redis in Docker"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./start_server.sh"
            echo "  ./start_server.sh --port 8080"
            echo "  ./start_server.sh --host 0.0.0.0 --port 8000"
            echo "  ./start_server.sh --no-redis"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Start Redis in Docker if requested and Docker is available
if [ "$START_REDIS" = "true" ] && [ "$DOCKER_AVAILABLE" = "true" ] && [ -n "$DOCKER_COMPOSE_CMD" ]; then
    if [ -f "docker-compose.yml" ]; then
        echo -e "${BLUE}🐳 Starting Redis in Docker...${NC}"
        $DOCKER_COMPOSE_CMD up -d redis
        echo -e "${GREEN}✅ Redis container started${NC}"
        echo ""
    else
        echo -e "${YELLOW}⚠️  docker-compose.yml not found, skipping Redis${NC}"
    fi
elif [ "$START_REDIS" = "true" ] && [ "$DOCKER_AVAILABLE" = "false" ]; then
    echo -e "${YELLOW}⚠️  Docker not available, skipping Redis startup${NC}"
    echo "Install Docker to automatically start Redis, or start Redis manually"
    echo ""
fi

# Change to backend directory
cd backend

echo -e "${GREEN}🚀 Starting FastAPI server...${NC}"
echo ""
echo "Server will be available at:"
echo -e "  ${GREEN}http://${HOST}:${PORT}${NC}"
echo "  http://${HOST}:${PORT}/docs (API documentation)"
echo "  http://${HOST}:${PORT}/health (Health check)"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Build uvicorn command
UVICORN_CMD="uvicorn app.main:app --host $HOST --port $PORT"

if [ "$RELOAD" = "true" ]; then
    UVICORN_CMD="$UVICORN_CMD --reload"
fi

# Start the server
exec $UVICORN_CMD

