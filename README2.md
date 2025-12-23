# Guardian SMS

A safety assistant that helps older adults identify scam SMS messages in real-time.

## Overview

Guardian SMS monitors incoming text messages on Android, analyzes them for scam indicators using hybrid AI detection, and alerts both the elderly user and their trusted family members. Messages are analyzed instantly without requiring technical expertise.

**What it solves:** Older adults are disproportionately targeted by SMS scams. Guardian provides instant protection and family oversight without requiring decisions under pressure.

**Target audience:** Senior citizens (protected users) and their family members (guardians).

## How It Works

### Message Monitoring
- **Android app:** Monitors incoming SMS messages in real-time
- **Local detection:** On-device rules engine (<50ms)
- **Backend verification:** ML analysis for uncertain cases (200ms)

### Analysis
- Hybrid detection: Local rules engine + Backend ML classifier
- Rule-based patterns: urgency language, suspicious links, money requests, impersonation
- Pretrained BERT model for scam/phishing detection
- Redis caching for fast repeated pattern detection

### Results
- Risk level (Safe / Medium Risk / High Risk)
- Warning signs identified in the message
- Safe next steps in plain language
- Real-time alerts to protected user

### Alerts
Guardian automatically notifies trusted family members when high-risk scams are detected. Medium-risk messages prompt the user to share. Family members can view shared messages with user consent to verify false positives.

## Privacy & Safety

- **Metadata-only storage** - Raw message content never stored permanently
- **Encrypted sharing** - Messages shared with family are encrypted (AES-256)
- **Auto-expiration** - Logs deleted after 7 days, shared messages after 48 hours or viewing
- **User control** - Protected users control guardian access levels
- **No modifications** - Original messages in system SMS app never touched

## Tech Stack

| Layer | Technology |
|-------|------------|
| Mobile App | Kotlin (Android) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache | Redis |
| ML | HuggingFace BERT classifier |
| Infrastructure | Railway / Render |

## Architecture

```mermaid
graph LR
    subgraph Frontend["🎯 Android App"]
        SMS[SMS Receiver]
        LOCAL[Local Rules<br/>⚡ 50ms]
        UI_HIGH[⚠️ High Risk Alert<br/>Elderly User]
        UI_MED[⚡ Medium Risk<br/>Share with Family?]
    end
    
    subgraph Backend["⚙️ FastAPI Backend"]
        API[API Gateway]
        VERIFY[ML Verification]
        ALERT[Alert Dispatcher]
    end
    
    subgraph Cache["💾 Redis"]
        REDIS[(Cache<br/>2-5ms)]
    end
    
    subgraph Database["🗄️ PostgreSQL"]
        DB[(Logs)]
        ENC[(Shared Msgs)]
    end
    
    SMS --> LOCAL
    LOCAL -->|🔴 HIGH| UI_HIGH
    LOCAL -->|🟡 MEDIUM| API
    LOCAL -->|🟢 LOW| DB
    
    UI_HIGH -.->|Auto-notify| Guardian1[📲 Guardian]
    
    API --> REDIS
    REDIS --> VERIFY
    VERIFY -->|Scam| UI_MED
    VERIFY -->|Safe| DB
    
    UI_MED -->|User clicks Yes| ALERT
    ALERT -.->|Notify| Guardian2[📲 Guardian]
    
    ALERT --> ENC
    
    style Frontend fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,color:#000
    style Backend fill:#E3F2FD,stroke:#2196F3,stroke-width:2px,color:#000
    style Cache fill:#FFF9C4,stroke:#FBC02D,stroke-width:2px,color:#000
    style Database fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#000
    style UI_HIGH fill:#EF5350,stroke:#C62828,stroke-width:3px,color:#FFF
    style UI_MED fill:#FFA726,stroke:#E65100,stroke-width:2px,color:#000
```

## Local Setup

### Requirements
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Android Studio (latest)

### Run Locally

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Android
# Open android/ in Android Studio
# Update API URL in strings.xml
# Build and run on emulator/device
```

## License

MIT
