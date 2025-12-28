# Guardian SMS - Development Setup Guide

This guide will help you get Guardian SMS running locally for development.

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Android Studio | Latest Stable (Hedgehog+) | Mobile app development |
| Python | 3.11+ | Backend API |
| Node.js | 18+ | Dashboard frontend |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Caching & real-time sync |
| Git | Latest | Version control |

### Optional but Recommended
- Docker Desktop (easier setup)
- Postman or Insomnia (API testing)
- VS Code with Python + ESLint extensions

---

## Option 1: Docker Setup (Recommended)

### 1. Install Docker
```bash
# macOS
brew install docker docker-compose

# Windows/Linux
# Download from https://www.docker.com/products/docker-desktop
```

### 2. Clone and Start
```bash
git clone https://github.com/your-org/guardian-sms
cd guardian-sms

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Services running:
# - Backend API: http://localhost:8000
# - Dashboard: http://localhost:3000
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### 3. Run Migrations
```bash
docker-compose exec backend alembic upgrade head
```

### 4. Create Test User
```bash
docker-compose exec backend python -m app.scripts.create_user \
  --phone "+15551234567" \
  --name "Test User"
```

---

## Option 2: Manual Setup

### Step 1: PostgreSQL

#### macOS
```bash
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb guardian_dev
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql-15

sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres createdb guardian_dev
sudo -u postgres psql -c "CREATE USER guardian WITH PASSWORD 'dev_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE guardian_dev TO guardian;"
```

#### Windows
```bash
# Download installer from https://www.postgresql.org/download/windows/
# During installation, remember the password for 'postgres' user

# Using psql:
psql -U postgres
CREATE DATABASE guardian_dev;
CREATE USER guardian WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE guardian_dev TO guardian;
\q
```

### Step 2: Redis

#### macOS
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### Windows
```bash
# Use WSL2 or Docker:
docker run -d -p 6379:6379 redis:7-alpine
```

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Download ML model (this takes ~500MB and a few minutes)
python -m app.scripts.download_model
```

#### Environment Variables

Create `backend/.env`:
```bash
# Database
DATABASE_URL=postgresql://guardian:dev_password@localhost:5432/guardian_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys (optional for MVP)
ANTHROPIC_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
SENDGRID_API_KEY=your_key_here

# Security
SECRET_KEY=dev_secret_key_change_in_production
ENVIRONMENT=development

# ML Model
MODEL_NAME=mrm8488/bert-tiny-finetuned-sms-spam-detection
MODEL_CACHE_DIR=./models
```

#### Run Migrations
```bash
alembic upgrade head
```

#### Start Backend
```bash
uvicorn app.main:app --reload --port 8000

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete.
```

#### Verify Backend
```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", "database": "connected", "redis": "connected"}
```

### Step 4: Dashboard Setup

```bash
cd dashboard

# Install dependencies
npm install

# Create .env.local
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development
EOF

# Start dev server
npm run dev

# Dashboard runs on http://localhost:3000
```

### Step 5: Android App Setup

#### Install Android Studio
1. Download from https://developer.android.com/studio
2. Install with default settings
3. Open Android Studio → SDK Manager
4. Install:
   - Android SDK Platform 34 (Android 14)
   - Android SDK Build-Tools 34.0.0
   - Android Emulator

#### Configure App
```bash
# Open project
# Android Studio → Open → guardian-sms/android/

# Update API URL
# File: android/app/src/main/res/values/strings.xml
```

**For Android Emulator:**
```xml
<string name="api_base_url">http://10.0.2.2:8000</string>
```

**For Physical Device:**
```xml
<!-- Replace with your computer's local IP -->
<string name="api_base_url">http://192.168.1.XXX:8000</string>
```

**Find your local IP:**
```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr IPv4
```

#### Build and Run
1. In Android Studio, click "Sync Project with Gradle Files"
2. Create/start emulator: Tools → Device Manager → Create Device
3. Select Pixel 6 (or similar) with API 34
4. Click "Run" (green play button)

---

## Verification Checklist

After setup, verify everything works:

### Backend
- [ ] Backend running on http://localhost:8000
- [ ] `/health` endpoint returns healthy status
- [ ] `/docs` shows interactive API documentation
- [ ] Database connection working
- [ ] Redis connection working

### Dashboard
- [ ] Dashboard running on http://localhost:3000
- [ ] Can access home page
- [ ] No console errors in browser

### Android
- [ ] App builds successfully
- [ ] App runs on emulator/device
- [ ] SMS permission can be granted
- [ ] App can communicate with backend

---

## Testing the Integration

### 1. Send Test SMS to Backend

```bash
curl -X POST http://localhost:8000/api/ingest/sms \
  -H "Content-Type: application/json" \
  -d '{
    "user_phone": "+15551234567",
    "sender": "+18005551234",
    "body": "URGENT: Your bank account has been suspended. Click here: bit.ly/scam123"
  }'

# Should return:
# {
#   "message_id": "msg_abc123",
#   "risk_level": "high_risk",
#   "confidence": 0.95,
#   "warning_signs": ["urgency_language", "suspicious_link", "impersonation"]
# }
```

### 2. Check Dashboard

1. Open http://localhost:3000
2. Navigate to Messages
3. You should see the test message with "High Risk" badge

### 3. Test Android App

#### Option A: Use Android Debug Bridge (ADB)
```bash
# Send fake SMS to emulator
adb emu sms send +18005551234 "URGENT: Your bank account has been suspended"

# Check app - should show alert
```

#### Option B: Use Another Phone
- Have a friend text your device
- Or use Google Voice to text yourself

---

## Common Issues & Solutions

### Issue: Backend won't start - "ModuleNotFoundError"
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database connection error
```bash
# Check if PostgreSQL is running
# macOS
brew services list | grep postgresql

# Ubuntu
sudo systemctl status postgresql

# Verify credentials in .env match database setup
```

### Issue: Redis connection error
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running:
brew services start redis  # macOS
sudo systemctl start redis # Ubuntu
```

### Issue: Android app can't reach backend
```bash
# Make sure you're using the right IP:

# For emulator: http://10.0.2.2:8000
# For device: http://YOUR_COMPUTER_IP:8000

# Test from device browser first:
# Open Chrome on Android device
# Navigate to http://YOUR_IP:8000/health
# Should see: {"status": "healthy"}
```

### Issue: ML model download fails
```bash
# Manual download:
cd backend
mkdir -p models
python -c "
from transformers import pipeline
classifier = pipeline('text-classification', model='mrm8488/bert-tiny-finetuned-sms-spam-detection')
"
```

### Issue: Port already in use
```bash
# Find what's using the port
# macOS/Linux
lsof -i :8000  # Backend
lsof -i :3000  # Dashboard

# Kill the process
kill -9 <PID>

# Or use different port:
uvicorn app.main:app --port 8001
```

---

## Development Workflow

### Daily Workflow
```bash
# 1. Start backend services
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# 2. In new terminal, start dashboard
cd dashboard
npm run dev

# 3. Open Android Studio and run app
```

### Running Tests
```bash
# Backend tests
cd backend
pytest tests/ -v

# Dashboard tests
cd dashboard
npm test
```

### Database Migrations

**Create new migration:**
```bash
cd backend
alembic revision -m "add_user_preferences_table"
# Edit the generated file in alembic/versions/
alembic upgrade head
```

**Reset database:**
```bash
alembic downgrade base
alembic upgrade head
```

---

## IDE Setup Recommendations

### VS Code (Backend)
Install extensions:
- Python
- Pylance
- Python Test Explorer
- Docker (optional)

**settings.json:**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

### Android Studio
- Enable "Auto Import" in Preferences → Editor → General → Auto Import
- Use Kotlin style guide formatting
- Install "Rainbow Brackets" plugin (helpful for nested code)

---

## Next Steps

1. ✅ Complete setup verification checklist
2. 📖 Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
3. 📋 Check [BACKLOG.md](BACKLOG.md) for development tasks
4. 🔨 Pick a task and start coding!

## Getting Help

- **Backend issues:** Check backend/README.md
- **Android issues:** Check android/README.md  
- **General questions:** Create GitHub issue or ask in team Slack

---

**Happy coding! 🚀**
