#!/bin/bash
# Quick script to check database tables using psql

# Load .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Get connection details from environment or prompt
HOST="${DB_HOST:-}"
PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-}"

if [ -z "$HOST" ]; then
    read -p "Database host: " HOST
fi

if [ -z "$DB_USER" ]; then
    read -p "Database user: " DB_USER
fi

if [ -z "$HOST" ] || [ -z "$DB_USER" ]; then
    echo "ERROR: Database host and user are required"
    exit 1
fi

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo "ERROR: psql not found. Install PostgreSQL client tools."
    echo "On macOS: brew install postgresql"
    echo "On Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

echo "Connecting to: $HOST:$PORT/$DB_NAME as $DB_USER"
echo ""

# List all tables
PGPASSWORD="$DB_PASSWORD" psql -h "$HOST" -p "$PORT" -U "$DB_USER" -d "$DB_NAME" << EOF
-- List all tables
\dt

-- Show table details
\du

-- Show current database
SELECT current_database();

-- Count tables
SELECT COUNT(*) as table_count 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- List all tables with row counts
SELECT 
    schemaname,
    tablename,
    (SELECT COUNT(*) FROM information_schema.tables t2 WHERE t2.table_name = t.tablename) as exists
FROM pg_tables t
WHERE schemaname = 'public'
ORDER BY tablename;
EOF

