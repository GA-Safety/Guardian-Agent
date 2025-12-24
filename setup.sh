#!/bin/bash
# Setup script for Guardian SMS project
# This script sets up the Python virtual environment and installs all dependencies

set -e  # Exit on error

echo "🚀 Guardian SMS Setup"
echo "===================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Found Python ${PYTHON_VERSION}${NC}"

# Check Python version (need 3.11+)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${YELLOW}⚠️  Warning: Python 3.11+ is recommended${NC}"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install backend requirements
if [ -f "backend/requirements.txt" ]; then
    echo ""
    echo "📥 Installing backend dependencies..."
    pip install -r backend/requirements.txt
    echo -e "${GREEN}✅ Backend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  backend/requirements.txt not found${NC}"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    if [ -f ".env.example" ]; then
        echo "📋 Copying .env.example to .env..."
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env file from .env.example${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env file with your database credentials${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.example not found. Please create .env file manually${NC}"
    fi
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Check database connection (optional)
if [ -f "test_db_connection.py" ]; then
    echo ""
    read -p "Test database connection? (y/n) [n]: " TEST_DB
    TEST_DB=${TEST_DB:-n}

    if [ "$TEST_DB" = "y" ] || [ "$TEST_DB" = "Y" ]; then
        echo ""
        echo "🔌 Testing database connection..."
        if python3 test_db_connection.py 2>/dev/null; then
            echo -e "${GREEN}✅ Database connection successful${NC}"
        else
            echo -e "${YELLOW}⚠️  Database connection failed. Please check your .env file${NC}"
        fi
    fi
fi

# Run database migrations (optional)
echo ""
read -p "Run database migrations? (y/n) [n]: " RUN_MIGRATIONS
RUN_MIGRATIONS=${RUN_MIGRATIONS:-n}

if [ "$RUN_MIGRATIONS" = "y" ] || [ "$RUN_MIGRATIONS" = "Y" ]; then
    echo ""
    echo "🗄️  Running database migrations..."
    cd backend
    if alembic upgrade head; then
        echo -e "${GREEN}✅ Database migrations completed${NC}"
    else
        echo -e "${YELLOW}⚠️  Database migrations failed. Please check your database connection${NC}"
    fi
    cd ..
fi

echo ""
echo -e "${GREEN}✨ Setup complete!${NC}"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run database migrations manually:"
echo "  cd backend && alembic upgrade head"
echo ""

