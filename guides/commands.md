# Guardian Agent - Development Commands Guide

Quick reference for common development commands. **No sensitive information included.**

## Server Management

### Start Server (with Redis)
```bash
./start_server.sh
```
Starts Redis in Docker and the FastAPI server automatically.

### Start Server (without Redis)
```bash
./start_server.sh --no-redis
```

### Start Server (custom port)
```bash
./start_server.sh --port 8080
```

### Stop Server
```bash
./stop_server.sh
```
Stops both Redis container and FastAPI server.

### Server URLs
- API: http://127.0.0.1:8000
- API Documentation: http://127.0.0.1:8000/docs
- Health Check: http://127.0.0.1:8000/health

## Docker Commands

### Start Redis Container
```bash
docker compose up -d redis
```

### Stop Redis Container
```bash
docker compose stop redis
```

### View Redis Logs
```bash
docker compose logs redis
```

### View Redis Logs (follow)
```bash
docker compose logs -f redis
```

### Restart Redis Container
```bash
docker compose restart redis
```

### Remove Redis Container (keeps data)
```bash
docker compose down redis
```

### Remove Redis Container and Data
```bash
docker compose down -v redis
```

### Check Redis Status
```bash
docker compose ps redis
```

### Connect to Redis CLI
```bash
docker compose exec redis redis-cli
```

## Database Commands

### Run Migrations
```bash
cd backend
alembic upgrade head
```

### Create New Migration
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Rollback Last Migration
```bash
cd backend
alembic downgrade -1
```

### Check Current Migration Version
```bash
cd backend
alembic current
```

### View Migration History
```bash
cd backend
alembic history
```

### Test Database Connection
```bash
./test_db_connection.sh
```

## Python Environment

### Activate Virtual Environment
```bash
source .venv/bin/activate
```

### Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Update Dependencies
```bash
pip install --upgrade -r backend/requirements.txt
```

### Run Python Shell
```bash
cd backend
python
```

### Run Python Script
```bash
cd backend
python script_name.py
```

## Testing & Debugging

### Check Health Endpoint
```bash
curl http://127.0.0.1:8000/health
```

### Check Root Endpoint
```bash
curl http://127.0.0.1:8000/
```

### View Server Logs
Server logs appear in the terminal where `./start_server.sh` is running.

### Check if Server is Running
```bash
lsof -i :8000
```

### Check if Redis is Running
```bash
docker compose ps redis
# or
lsof -i :6379
```

## Project Setup

### Initial Setup
```bash
./setup.sh
```
Creates virtual environment, installs dependencies, and optionally runs migrations.

### Check Project Structure
```bash
tree -L 2 -I '__pycache__|*.pyc|.venv'
```

## Environment Variables

### Required Environment Variables
Create a `.env` file in the project root with:
```
DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=postgres
DB_PORT=5432
```

### Optional Environment Variables
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
DEBUG=False
LOG_LEVEL=INFO
```

**Note:** Never commit `.env` file to version control!

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti :8000 | xargs kill -9

# Kill process on port 6379
lsof -ti :6379 | xargs kill -9
```

### Docker Not Starting
```bash
# Check Docker status
docker info

# Restart Docker Desktop (macOS)
# Use Docker Desktop GUI or:
killall Docker && open /Applications/Docker.app
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Database Connection Issues
1. Check `.env` file has correct credentials
2. Verify database is accessible
3. Test connection: `./test_db_connection.sh`

### Redis Connection Issues
1. Check if Redis container is running: `docker compose ps redis`
2. Check Redis logs: `docker compose logs redis`
3. Restart Redis: `docker compose restart redis`

## Quick Reference

| Task | Command |
|------|---------|
| Start everything | `./start_server.sh` |
| Stop everything | `./stop_server.sh` |
| View API docs | Open http://127.0.0.1:8000/docs |
| Check health | `curl http://127.0.0.1:8000/health` |
| Run migrations | `cd backend && alembic upgrade head` |
| Redis CLI | `docker compose exec redis redis-cli` |

## Notes

- All commands assume you're in the project root directory unless specified
- The server auto-reloads on code changes (when using `./start_server.sh`)
- Redis data persists in a Docker volume even if container is stopped
- Database migrations should be run before starting the server for the first time

