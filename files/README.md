# Guardian SMS

An AI-powered scam detection system that protects elderly users from SMS fraud in real-time.

## Overview

Guardian SMS monitors incoming text messages on Android devices, detects scam patterns using AI, and alerts both the elderly user and their family members when suspicious messages arrive. Messages are analyzed instantly without requiring the user to make decisions under pressure.

**What it solves:** Elderly Americans lost $5 billion to scams in 2024, with SMS scams being increasingly common. Guardian provides real-time protection without requiring technical expertise.

**Target audience:** Senior citizens (primary users) and their families (guardians/monitors).

## How It Works

### 1. Real-Time SMS Monitoring (Android)
- Android app runs in background using `BroadcastReceiver`
- Monitors all incoming SMS messages (requires `READ_SMS` permission)
- Messages are immediately sent to backend for analysis
- User sees their normal SMS app - Guardian runs silently

### 2. AI-Powered Analysis
Guardian uses a **hybrid detection approach**:

**Rules Engine (Fast)**
- Urgency/threat language ("act now", "account suspended")
- Suspicious links (URL shorteners, misspelled domains)
- Money requests (gift cards, crypto, wire transfer, Venmo/Zelle)
- MFA/code phishing ("send verification code")

**ML Classifier (Accurate)**
- Pre-trained BERT model fine-tuned on SMS spam/scam dataset
- Detects subtle phishing patterns
- Returns confidence score (0.0 - 1.0)

**Risk Assessment**
- **High Risk:** ML score > 0.8 OR 3+ rule matches
- **Caution:** ML score > 0.5 OR 1-2 rule matches  
- **Safe:** Otherwise

### 3. Immediate User Protection
When scam detected:
- ✅ **Full-screen alert** appears immediately
- ✅ Shows **simple explanation**: "This looks like a fake IRS message"
- ✅ **One-click actions**: "Delete Message" or "It's Safe"
- ✅ Auto-notifies family members (if enabled)

### 4. Family Dashboard
- Web-based dashboard for trusted family members
- Real-time alerts when scams are detected
- View history of blocked scams
- No access to message content (privacy-preserving)

### 5. Post-Analysis Learning
- User feedback improves detection
- Builds personal scam profile over time
- Adapts to new scam tactics

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ANDROID APP                          │
│  ┌─────────────────┐         ┌──────────────────┐      │
│  │  SMS Receiver   │ ──────> │  Analysis Client │      │
│  │ (Broadcast)     │         │                  │      │
│  └─────────────────┘         └────────┬─────────┘      │
│                                        │                │
│  ┌─────────────────┐         ┌────────▼─────────┐      │
│  │  Alert UI       │ <────── │  Local Cache     │      │
│  │ (Full Screen)   │         │  (SQLite)        │      │
│  └─────────────────┘         └──────────────────┘      │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS/REST
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                      │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐   ┌───────────┐  │
│  │   Ingestion  │───>│   Analysis   │──>│  Storage  │  │
│  │   Endpoint   │    │  Orchestrator│   │           │  │
│  └──────────────┘    └──────┬───────┘   └───────────┘  │
│                             │                           │
│                    ┌────────┴────────┐                  │
│                    │                 │                  │
│              ┌─────▼─────┐    ┌─────▼──────┐           │
│              │   Rules   │    │ ML Model   │           │
│              │  Engine   │    │ (BERT)     │           │
│              └───────────┘    └────────────┘           │
│                                                          │
│  ┌──────────────┐                   ┌──────────────┐   │
│  │    Alert     │                   │   Family     │   │
│  │  Dispatcher  │                   │   Dashboard  │   │
│  └──────────────┘                   │   (React)    │   │
│                                      └──────────────┘   │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ PostgreSQL  │
              │   + Redis   │
              └─────────────┘
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Mobile App** | Kotlin (Android) | SMS monitoring, user alerts |
| **Backend API** | FastAPI (Python) | Message analysis, orchestration |
| **ML Model** | HuggingFace Transformers | Scam classification |
| **Database** | PostgreSQL | Message logs, user data |
| **Cache** | Redis | Rate limiting, real-time sync |
| **Family Dashboard** | React + TypeScript | Web interface for guardians |
| **Notifications** | Twilio (SMS) + SendGrid (Email) | Family alerts |
| **Deployment** | Docker + Docker Compose | Containerization |
| **Cloud** | AWS (EC2/RDS) or Railway | Hosting |

## Project Structure

```
guardian-sms/
├── android/                    # Android app (Kotlin)
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/guardian/
│   │   │   │   ├── receivers/      # SMS BroadcastReceiver
│   │   │   │   ├── services/       # Background service
│   │   │   │   ├── ui/             # Alert activities
│   │   │   │   └── api/            # Backend client
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle
│   └── README.md
│
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/                # REST endpoints
│   │   │   ├── ingest.py       # SMS ingestion
│   │   │   ├── messages.py     # Message CRUD
│   │   │   └── contacts.py     # Trusted contacts
│   │   ├── models/             # SQLAlchemy models
│   │   ├── analysis/
│   │   │   ├── rules.py        # Rules engine
│   │   │   ├── classifier.py   # ML model
│   │   │   └── orchestrator.py # Analysis pipeline
│   │   ├── services/
│   │   │   ├── alerts.py       # Family notifications
│   │   │   └── cleanup.py      # Auto-expiration
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── dashboard/                  # Family web dashboard (React)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   ├── package.json
│   └── README.md
│
├── docker-compose.yml          # Local development
├── README.md                   # This file
└── docs/
    ├── SETUP.md               # Setup instructions
    ├── ARCHITECTURE.md        # Technical details
    └── BACKLOG.md            # Development tasks
```

## Local Development

### Prerequisites
- **Android Studio** (latest stable)
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Redis 7+**
- **Docker** (optional, recommended)

### Quick Start with Docker

```bash
# Clone repository
git clone https://github.com/your-org/guardian-sms
cd guardian-sms

# Start backend + database + redis
docker-compose up -d

# Backend runs on http://localhost:8000
# Dashboard runs on http://localhost:3000
```

### Manual Setup

#### 1. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/guardian"
export REDIS_URL="redis://localhost:6379"
export ANTHROPIC_API_KEY="your-key-here"  # For advanced analysis (optional)

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

#### 2. Dashboard
```bash
cd dashboard
npm install
npm run dev  # Runs on http://localhost:3000
```

#### 3. Android App
```bash
# Open in Android Studio
cd android
# Open android/ folder in Android Studio

# Update backend URL in app/src/main/res/values/strings.xml
<string name="api_base_url">http://10.0.2.2:8000</string>  # For emulator
# or
<string name="api_base_url">http://YOUR_LOCAL_IP:8000</string>  # For device

# Build and run on device/emulator
```

## Testing

### Send Test SMS (For Demo)

```bash
# Use Twilio CLI or send from another phone
# The app will detect and analyze in real-time

# Or use the demo endpoint:
curl -X POST http://localhost:8000/api/demo/inject-sms \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "+18005551234",
    "body": "URGENT: Your bank account has been suspended. Click here to verify: bit.ly/scam123"
  }'
```

### Run Backend Tests
```bash
cd backend
pytest tests/ -v
```

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment guide.

**Quick deploy to Railway:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

## Privacy & Security

### Data Handling
- ✅ **End-to-end encryption** for API calls
- ✅ **No message content stored** after analysis (metadata only)
- ✅ **Auto-expiration** - logs deleted after 7 days
- ✅ **Local processing** - sensitive detection happens on-device when possible
- ✅ **Consent-based alerts** - family only notified if user enables

### Permissions (Android)
- `READ_SMS` - Monitor incoming messages
- `RECEIVE_SMS` - Detect new messages
- `INTERNET` - Send to backend for analysis
- `FOREGROUND_SERVICE` - Run in background

## Roadmap

### Week 1 (MVP)
- [x] Android SMS monitoring
- [x] Rules engine for scam detection
- [x] ML classifier integration
- [x] Backend API (FastAPI)
- [x] PostgreSQL schema
- [x] Basic alert UI

### Week 2 (Core Features)
- [ ] Family dashboard (React)
- [ ] SMS/Email notifications to family
- [ ] User feedback loop
- [ ] Auto-expiration job
- [ ] Docker deployment

### Week 3 (Polish + Demo)
- [ ] UI/UX improvements
- [ ] Demo data generator
- [ ] Production deployment
- [ ] Documentation
- [ ] Pitch deck

### Future (Post-Hackathon)
- [ ] Email forwarding (stretch goal)
- [ ] iOS support (limited - notification-based)
- [ ] Voice call screening (research phase)
- [ ] Multi-language support
- [ ] Offline mode

## Contributing

We're building this for the ColorStack Hackathon (3-week sprint). After the hackathon, we plan to open-source fully.

## Team

- **David Reyes** - Backend, ML, Infrastructure
- **Daniel Leon Silva** - Android, Frontend, Design

## License

MIT License - see [LICENSE.md](LICENSE.md)

## Responsible AI Principles

Guardian is built with **Responsible AI** at its core:

1. **Transparency** - Users see exactly why a message was flagged
2. **User Control** - Elderly users maintain agency, Guardian advises
3. **Privacy-First** - Minimal data collection, auto-expiration
4. **Explainability** - No black-box decisions, clear reasoning
5. **Accountability** - Audit logs for all actions
6. **Equity** - Designed for less tech-savvy users (accessibility-first)

## Acknowledgments

- FTC for scam pattern data
- HuggingFace for pre-trained models
- ColorStack for organizing the hackathon
- Our families who inspired this project

---

**⚠️ Note:** Guardian is an educational project built for a hackathon. It is not a replacement for human judgment or professional financial advice. Always verify suspicious communications directly with the organization through official channels.
