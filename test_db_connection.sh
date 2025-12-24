#!/bin/bash
# Quick test script for PostgreSQL connection
# Reads configuration from environment variables or .env file

# Load from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Get connection details from environment or prompt
HOST="${DB_HOST:-}"
PORT="${DB_PORT:-5432}"

if [ -z "$HOST" ]; then
    read -p "Database host: " HOST
fi

if [ -z "$HOST" ]; then
    echo "ERROR: Database host is required"
    echo "Set DB_HOST environment variable or provide it when prompted"
    exit 1
fi

echo "Testing PostgreSQL connection to: $HOST:$PORT"
echo ""

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "ERROR: psql not found. Install PostgreSQL client tools."
    echo "On macOS: brew install postgresql"
    echo "On Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

# Get credentials from environment or prompt
DB_NAME="${DB_NAME:-postgres}"
if [ -z "$DB_NAME" ] || [ "$DB_NAME" = "postgres" ]; then
    read -p "Database name [postgres]: " INPUT_DB_NAME
    DB_NAME="${INPUT_DB_NAME:-postgres}"
fi

DB_USER="${DB_USER:-}"
if [ -z "$DB_USER" ]; then
    read -p "Username: " DB_USER
fi

DB_PASSWORD="${DB_PASSWORD:-}"
if [ -z "$DB_PASSWORD" ]; then
    read -sp "Password: " DB_PASSWORD
    echo ""
fi

# Test connection
PGPASSWORD="$DB_PASSWORD" psql -h "$HOST" -p "$PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Connection successful!"
else
    echo ""
    echo "❌ Connection failed!"
    exit 1
fi

