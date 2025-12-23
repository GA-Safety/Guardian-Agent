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
  %% --- Columns (left -> right) ---
  subgraph FE["Android App"]
    SMS["SMS Receiver"]
    Local["On-device Check"]
    Hi["High Risk Alert"]
    Med["Confirm Share?"]
  end

  subgraph BE["FastAPI Backend"]
    API["API Gateway"]
    Verify["Verification"]
    Dispatch["Dispatch"]
  end

  subgraph C["Redis"]
    R[(Cache)]
  end

  subgraph D["Postgres"]
    Logs[(Logs)]
    Shared[(Shared Msgs)]
  end

  %% --- Flow ---
  SMS --> Local

  Local -->|"HIGH"| Hi
  Hi -.->|"notify"| G1["Guardian"]

  Local -->|"MED"| API
  Local -->|"LOW"| Logs

  API --> R
  R --> Verify
  Verify -->|"risk"| Med
  Verify -->|"ok"| Logs

  Med -->|"share"| Dispatch
  Dispatch -.->|"notify"| G2["Guardian"]
  Dispatch --> Shared

  %% --- Dark minimal styling ---
  classDef panel fill:#15171A,stroke:#2A2F36,color:#E6E6E6,stroke-width:1px;
  classDef node  fill:#0F1115,stroke:#2A2F36,color:#E6E6E6,stroke-width:1px;
  classDef store fill:#0B0D10,stroke:#3A404A,color:#E6E6E6,stroke-width:1px;
  classDef warn  fill:#1B1D22,stroke:#6B7280,color:#EDEDED,stroke-width:1.5px;

  class FE,BE,C,D panel;
  class SMS,Local,API,Verify,Dispatch,G1,G2 node;
  class Logs,Shared,R store;
  class Hi,Med warn;

  linkStyle default stroke:#6B7280,stroke-width:1px;
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
