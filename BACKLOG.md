# Guardian MVP Backlog

## Build Order

### Week 1 (Critical Path)
1. **BE-01** Database schema
2. **BE-02** Email ingestion (SES)
3. **BE-03** Rules engine
4. **BE-04** ML classifier integration
5. **BE-05** Analysis orchestrator
6. **FE-01** Home page
7. **FE-02** Message inbox
8. **FE-03** Message review page

### Week 2
1. **BE-06** SMS ingestion (Twilio)
2. **BE-07** Auto-expiration job
3. **BE-08** Alert dispatcher
4. **BE-09** Structured logging
5. **FE-04** Trusted contacts management
6. **FE-05** Settings & consent
7. **INF-01** AWS deployment
8. **TEST-01** Unit tests
9. **DEMO-01** Red-team tooling

---

## Epic 1: Message Ingestion

### Story 1.1: Email Forwarding via SES

#### BE-01: Database Schema
**Title:** Design and implement core database schema

**Description:** Create PostgreSQL schema for messages, users, trusted contacts, and consent settings.

**Acceptance Criteria:**
- Messages table with: id, user_id, source, raw_content, imported_at, expires_at, deleted_at
- Users table with: id, email, created_at
- Trusted contacts table with: id, user_id, contact_email, contact_phone, consent_given, created_at
- Indexes on expires_at for cleanup job

**Technical Notes:**
- Use SQLAlchemy with Alembic migrations
- expires_at = imported_at + 7 days
- Soft delete via deleted_at

**Dependencies:** None

**Effort:** S

**Owner:** BE

---

#### BE-02: Email Ingestion Endpoint
**Title:** Implement SES inbound email webhook

**Description:** Receive forwarded emails from AWS SES, parse content, normalize, and store.

**Acceptance Criteria:**
- POST `/api/ingest/email` receives SES notification
- Extracts sender, subject, body (plain text preferred, HTML fallback)
- Creates or matches user by forwarding address
- Stores normalized message with expires_at
- Returns 200 on success, 400 on malformed input

**Technical Notes:**
- SES sends SNS notification with S3 pointer or raw content
- Use `email` stdlib for parsing
- Dedupe by message-id header

**Dependencies:** BE-01

**Effort:** M

**Owner:** BE

---

#### BE-06: SMS Ingestion Endpoint
**Title:** Implement Twilio SMS webhook

**Description:** Receive SMS messages forwarded via Twilio, normalize, and store.

**Acceptance Criteria:**
- POST `/api/ingest/sms` receives Twilio webhook
- Validates Twilio signature
- Extracts sender phone, body
- Creates or matches user by phone number
- Stores normalized message

**Technical Notes:**
- Use `twilio` SDK for signature validation
- Phone number normalization (E.164)

**Dependencies:** BE-01

**Effort:** M

**Owner:** BE

---

## Epic 2: Analysis Pipeline

### Story 2.1: Rules Engine

#### BE-03: Rules Engine
**Title:** Implement deterministic feature extraction

**Description:** Extract scam indicators from message text using rules.

**Acceptance Criteria:**
- Detects urgency/threat language ("act now", "account suspended", "verify immediately")
- Detects suspicious links (URL shorteners, misspelled domains, non-HTTPS)
- Detects money requests (gift cards, crypto, wire transfer, Venmo/Zelle)
- Detects MFA/code requests ("send code", "verification code")
- Returns list of matched warning signs

**Technical Notes:**
- Regex + keyword matching
- Return structured list: `[{"type": "urgency", "match": "act now"}, ...]`
- Configurable keyword lists in YAML

**Dependencies:** None

**Effort:** M

**Owner:** BE

---

### Story 2.2: ML Classifier

#### BE-04: ML Classifier Integration
**Title:** Integrate HuggingFace scam/phishing classifier

**Description:** Load pretrained model and return scam probability score.

**Acceptance Criteria:**
- Loads model on startup (or lazy load)
- `classify(text) -> {"score": 0.0-1.0, "label": "scam"|"safe"}`
- Handles long text (truncation)
- Returns score within 500ms for typical message

**Technical Notes:**
- Use `transformers` pipeline
- Model: TBD (e.g., `mrm8488/bert-tiny-finetuned-sms-spam-detection` or similar)
- CPU inference acceptable for MVP

**Dependencies:** None

**Effort:** M

**Owner:** BE

---

### Story 2.3: Analysis Orchestrator

#### BE-05: Analysis Orchestrator
**Title:** Combine rules + ML into final risk assessment

**Description:** Run both engines, compute final risk level, generate output.

**Acceptance Criteria:**
- Calls rules engine and ML classifier
- Computes risk level:
  - High Risk: ML score > 0.8 OR 3+ rule matches
  - Caution: ML score > 0.5 OR 1-2 rule matches
  - Safe: otherwise
- Returns: `{risk_level, warning_signs, safe_next_steps}`
- safe_next_steps from pre-approved template list

**Technical Notes:**
- Templates stored in config (not generated)
- Example steps: "Do not click any links", "Do not reply", "Contact your bank directly using the number on your card"

**Dependencies:** BE-03, BE-04

**Effort:** M

**Owner:** BE

---

## Epic 3: Message Lifecycle

### Story 3.1: Auto-Expiration

#### BE-07: Auto-Expiration Job
**Title:** Implement scheduled message cleanup

**Description:** Delete messages older than 7 days.

**Acceptance Criteria:**
- Runs daily (or on-demand)
- Deletes messages where expires_at < now()
- Logs count of deleted messages
- Does not delete messages already soft-deleted

**Technical Notes:**
- Use APScheduler or cron via ECS scheduled task
- Hard delete (not soft) for expired messages

**Dependencies:** BE-01

**Effort:** S

**Owner:** BE

---

## Epic 4: Alerts

### Story 4.1: Alert Dispatcher

#### BE-08: Alert Dispatcher
**Title:** Send alerts to trusted contacts

**Description:** Notify trusted contacts when high-risk message detected.

**Acceptance Criteria:**
- Only triggers if user has consented
- Only triggers for High Risk messages
- Sends email (via SES) and/or SMS (via Twilio) to trusted contact
- Payload: risk level, warning signs, timestamp, link to Guardian
- Does NOT include message excerpt unless user opted in

**Technical Notes:**
- Check consent flag before sending
- Use templates for email/SMS body
- Rate limit: max 1 alert per message

**Dependencies:** BE-05, BE-01

**Effort:** M

**Owner:** BE

---

## Epic 5: Logging & Auditability

### Story 5.1: Structured Logging

#### BE-09: Structured Logging
**Title:** Implement metadata-only structured logging

**Description:** Add structured JSON logging across all backend operations for auditability and explainability.

**Acceptance Criteria:**
- All logs are JSON-formatted with `message_id` and `timestamp`
- Log ingestion events: source, message_id, user_id (hashed), status
- Log analysis decisions: message_id, rules_fired, ml_score, final_risk_level
- Log alert dispatches: message_id, contact_id (hashed), channel, status
- Log deletions: message_id, deletion_type (user_initiated | auto_expired)
- NO raw message content in logs
- NO full email addresses or phone numbers (hash or mask)
- NO screenshots or OCR output

**Technical Notes:**
- Use `structlog` or Python `logging` with JSON formatter
- Create logging utility with PII scrubbing
- Mask emails: `j***@example.com`
- Mask phones: `***-***-1234`
- CloudWatch ingestion-ready format

**Dependencies:** BE-02, BE-05, BE-07, BE-08

**Effort:** M

**Owner:** BE

---

## Epic 6: Frontend

### Story 5.1: Core Pages

#### FE-01: Home Page
**Title:** Build home/landing page

**Description:** Explain how to use Guardian and how to forward messages.

**Acceptance Criteria:**
- Clear instructions for email forwarding
- Large, readable text (senior-friendly)
- Link to inbox
- No login required for MVP (or simple email-based auth)

**Technical Notes:**
- Static content, minimal interactivity
- Use Tailwind with large font defaults

**Dependencies:** None

**Effort:** S

**Owner:** FE

---

#### FE-02: Message Inbox
**Title:** Build message inbox view

**Description:** Display list of imported messages with risk indicators.

**Acceptance Criteria:**
- Lists messages sorted by imported_at (newest first)
- Shows: sender, subject/snippet, risk level badge, date
- Risk level color-coded (green/yellow/red)
- Click to view details
- Delete button per message

**Technical Notes:**
- Fetch from `GET /api/messages`
- Pagination optional for MVP

**Dependencies:** BE-02, FE-01

**Effort:** M

**Owner:** FE

---

#### FE-03: Message Review Page
**Title:** Build message detail/review page

**Description:** Display analysis results for a single message.

**Acceptance Criteria:**
- Shows risk level prominently
- Lists warning signs as bullets
- Shows safe next steps
- Shows message preview (sender, subject, snippet)
- Delete button
- Back to inbox

**Technical Notes:**
- Fetch from `GET /api/messages/{id}`
- Large, readable typography

**Dependencies:** BE-05, FE-02

**Effort:** M

**Owner:** FE

---

### Story 5.2: Trusted Contacts

#### FE-04: Trusted Contacts Management
**Title:** Build trusted contacts page

**Description:** Allow user to add/remove trusted contacts.

**Acceptance Criteria:**
- Add contact form: name, email, phone (optional)
- List existing contacts
- Remove contact button
- Consent toggle per contact

**Technical Notes:**
- CRUD via `POST/GET/DELETE /api/contacts`

**Dependencies:** BE-01

**Effort:** M

**Owner:** FE

---

#### FE-05: Settings & Consent
**Title:** Build settings page

**Description:** Allow user to manage consent and preferences.

**Acceptance Criteria:**
- Toggle: enable/disable alerts to trusted contacts
- Toggle: include message excerpts in alerts (default off)
- Save button

**Technical Notes:**
- PATCH `/api/settings`

**Dependencies:** BE-08

**Effort:** S

**Owner:** FE

---

## Epic 7: Infrastructure

#### INF-01: AWS Deployment
**Title:** Deploy MVP to AWS

**Description:** Set up production environment.

**Acceptance Criteria:**
- FastAPI running on ECS Fargate
- PostgreSQL on RDS
- SES configured for inbound email
- Domain configured (guardian.app or placeholder)
- HTTPS enabled

**Technical Notes:**
- Use Terraform or CDK
- Secrets in AWS Secrets Manager
- CloudWatch logs enabled

**Dependencies:** All BE tickets

**Effort:** L

**Owner:** Infra

---

## Epic 8: Testing & Demo

#### TEST-01: Unit Tests
**Title:** Implement core unit tests

**Description:** Test coverage for critical paths.

**Acceptance Criteria:**
- Rules engine: test each rule type
- ML classifier: test score thresholds
- Analysis orchestrator: test risk level logic
- Ingestion: test email/SMS parsing
- 80% coverage on core modules

**Technical Notes:**
- Use pytest
- Mock ML model for speed

**Dependencies:** BE-03, BE-04, BE-05

**Effort:** M

**Owner:** BE

---

#### DEMO-01: Red-Team Tooling
**Title:** Build demo/test message generator

**Description:** Internal tool to inject test scam messages.

**Acceptance Criteria:**
- CLI or admin endpoint to inject fake messages
- Presets: "Nigerian prince", "IRS threat", "Gift card request", "Safe newsletter"
- Bypasses email parsing (direct DB insert)
- Clearly marked as test data

**Technical Notes:**
- Not user-facing
- Useful for demos and testing

**Dependencies:** BE-01, BE-05

**Effort:** S

**Owner:** BE

---

## Critical Path Summary

```
BE-01 → BE-02 → BE-03 + BE-04 → BE-05 → FE-02 → FE-03
                                    ↓
                                 BE-08 → FE-04 → FE-05
```

**Must-haves for demo:**
- Email ingestion working
- Analysis returning risk + signs + steps
- Inbox + review pages functional
- At least one alert path (email)

**Nice-to-haves:**
- SMS ingestion
- Gmail import
- Auto-expiration job running
