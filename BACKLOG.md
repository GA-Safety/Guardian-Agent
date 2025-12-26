# Guardian SMS Backlog

## Build Order

### Phase 1: Foundation (Week 1-2)
1. **BE-01** Database schema (DONE)
2. **BE-02** Backend API structure (DONE)
3. **BE-03** On-device rules engine (Android)
4. **BE-04** ML classifier integration
5. **BE-05** Analysis orchestrator (DONE)
6. **BE-06** Redis cache integration

### Phase 2: Core Features (Week 3-4)
7. **AND-01** SMS monitoring service
8. **AND-02** User Dashboard (Android)
9. **BE-07** Message analysis API
10. **BE-08** Notification service
11. **WEB-01** Guardian Dashboard (Web)
12. **WEB-02** SSE real-time updates

### Phase 3: Polish & Deploy (Week 5-6)
13. **BE-09** Auto-expiration job
14. **BE-10** Structured logging
15. **BE-11** Guardian management API
16. **BE-12** RBAC implementation
17. **AND-03** Message sharing
18. **AND-04** Guardian management
19. **WEB-03** Guardian authentication & invitations
20. **INF-01** Deployment setup
21. **TEST-01** Unit tests

---

## Epic 1: Database & Backend Foundation

### Story 1.1: Database Schema (DONE)

#### BE-01: Database Schema
**Title:** Design and implement core database schema

**Description:** Create PostgreSQL schema for messages, users, protected users, guardians, and shared messages.

**Acceptance Criteria:**
- Users table: id, phone_number, created_at, updated_at
- ProtectedUsers table: id, user_id, name, created_at
- Guardians table: id, protected_user_id, email, phone, name, access_level, created_at, invitation_code, invitation_expires_at, invitation_accepted_at
- Messages table: id, protected_user_id, sender_phone, content, risk_level, rule_matches, ml_score, analyzed_at, expires_at, deleted_at, job_id (for async processing)
- SharedMessages table: id, message_id, guardian_id, encrypted_content, shared_at, expires_at, viewed_at
- GuardianInvitations table: id, protected_user_id, guardian_email, invitation_code, expires_at, accepted_at, created_at
- Indexes on expires_at, analyzed_at, protected_user_id, invitation_code

**Technical Notes:**
- Use SQLAlchemy with Alembic migrations
- expires_at = analyzed_at + 7 days for messages
- expires_at = shared_at + 48 hours for shared messages
- Soft delete via deleted_at

**Dependencies:** None

**Effort:** M

**Owner:** BE

---

### Story 1.2: Backend API Structure (DONE)

#### BE-02: Backend API Structure
**Title:** Set up FastAPI application structure

**Description:** Create FastAPI project with routing, middleware, and database connection.

**Acceptance Criteria:**
- FastAPI app with CORS middleware
- Database connection pool (SQLAlchemy)
- Redis connection pool
- Environment configuration
- Health check endpoint
- Error handling middleware

**Technical Notes:**
- Use async/await for database operations
- Environment variables for secrets
- Structured logging setup

**Dependencies:** BE-01

**Effort:** S

**Owner:** BE

---

## Epic 2: Detection Engine

### Story 2.1: On-Device Rules Engine

#### BE-03: On-Device Rules Engine
**Title:** Implement Android on-device pattern matching rules

**Description:** Create rules engine that detects scam patterns locally on Android device.

**Acceptance Criteria:**
- Detects urgency language ("act now", "account suspended", "verify immediately")
- Detects suspicious links (URL shorteners, misspelled domains)
- Detects money requests (gift cards, crypto, wire transfer, Venmo/Zelle)
- Detects impersonation attempts (bank, government, tech support)
- Returns count of matched rules (0-5+)
- Runs in <50ms
- Returns structured list: `[{"type": "urgency", "match": "act now"}, ...]`

**Technical Notes:**
- Implement in Kotlin
- Regex + keyword matching
- Configurable keyword lists (YAML/JSON)
- Lightweight, no external dependencies

**Dependencies:** None

**Effort:** M

**Owner:** Android

---

### Story 2.2: ML Classifier Integration

#### BE-04: ML Classifier Integration
**Title:** Integrate HuggingFace BERT scam/phishing classifier

**Description:** Load pretrained BERT model and return scam probability score.

**Acceptance Criteria:**
- Loads model on startup (or lazy load)
- `classify(text) -> {"score": 0.0-1.0, "label": "scam"|"safe"}`
- Handles long text (truncation to 512 tokens)
- Returns score within 500ms for typical message
- Handles model errors gracefully

**Technical Notes:**
- Use `transformers` pipeline
- Model: `mrm8488/bert-tiny-finetuned-sms-spam-detection` or similar
- CPU inference acceptable for MVP
- Cache model in memory

**Dependencies:** BE-02

**Effort:** M

**Owner:** BE

---

### Story 2.3: Analysis Orchestrator

#### BE-05: Analysis Orchestrator
**Title:** Combine rules + ML into final risk assessment

**Description:** Run both engines, compute final risk level, generate output.

**Acceptance Criteria:**
- Receives rule matches count and ML score
- Computes risk level:
  - High Risk: ML score > 0.8 OR 3+ rule matches
  - Medium Risk: ML score 0.5-0.8 OR 1-2 rule matches
  - Safe: otherwise
- Returns: `{risk_level, warning_signs, safe_next_steps, ml_score, rule_matches}`
- safe_next_steps from pre-approved template list

**Technical Notes:**
- Templates stored in config (not generated)
- Example steps: "Do not click any links", "Do not reply", "Contact your bank directly using the number on your card"

**Dependencies:** BE-03, BE-04

**Effort:** M

**Owner:** BE

---

### Story 2.4: Redis Cache Integration

#### BE-06: Redis Cache Integration
**Title:** Implement Redis caching for message patterns and ML results

**Description:** Cache message hashes and ML results to avoid reprocessing similar messages.

**Acceptance Criteria:**
- Hash message content (SHA-256)
- Check cache before running ML: `cache_key = f"msg:{hash}"`
- Store ML results: `{risk_level, ml_score, rule_matches, timestamp}`
- TTL: 24 hours for ML results
- TTL: 7 days for known scam patterns
- Handle cache misses gracefully

**Technical Notes:**
- Use Redis for pattern cache
- Cache key format: `msg:{hash}` for results, `pattern:{hash}` for known scams
- Async cache operations

**Dependencies:** BE-02

**Effort:** S

**Owner:** BE

---

## Epic 3: Android App

### Story 3.1: SMS Monitoring

#### AND-01: SMS Monitoring Service
**Title:** Implement SMS monitoring and interception on Android

**Description:** Monitor incoming SMS messages in real-time and trigger analysis.

**Acceptance Criteria:**
- BroadcastReceiver for SMS_RECEIVED intent
- Extract sender phone number and message content
- Trigger on-device rules engine
- If 3+ rule matches → show immediate alert
- If 1-2 rule matches → send to backend API
- Handle permissions (READ_SMS)
- Works in background

**Technical Notes:**
- Use Android BroadcastReceiver
- Request SMS permissions at runtime
- Background service for continuous monitoring
- Handle Android 8.0+ background restrictions

**Dependencies:** BE-03

**Effort:** M

**Owner:** Android

---

### Story 3.2: User Dashboard

#### AND-02: User Dashboard (Android)
**Title:** Build main dashboard for protected users

**Description:** Display analyzed messages, risk levels, alerts, and allow sharing.

**Acceptance Criteria:**
- Onboarding flow: phone number registration, create protected user profile
- List of analyzed messages (newest first)
- Shows: sender, snippet, risk level badge, timestamp
- Risk level color-coded (green/yellow/red)
- Click to view message details
- Message detail page shows: full content, risk level, warning signs, safe next steps
- Share button to send to guardians
- Settings page for guardian management (add/remove guardians, set access levels)
- Real-time updates: poll API or receive push notifications when ML completes analysis
- Large, readable text (senior-friendly UI)

**Technical Notes:**
- Use Jetpack Compose or XML layouts
- Material Design 3
- Large font sizes (18sp+)
- High contrast colors
- Simple navigation

**Dependencies:** AND-01, BE-07

**Effort:** L

**Owner:** Android

---

### Story 3.3: Guardian Management

#### AND-04: Guardian Management
**Title:** Allow protected users to manage their guardians

**Description:** Enable protected users to add, remove, and configure guardian access.

**Acceptance Criteria:**
- Settings page in User Dashboard
- Add guardian: enter email/phone, generate invitation
- Remove guardian: revoke access
- Set access level (view all messages / view shared only)
- View list of active guardians
- Show guardian invitation status

**Technical Notes:**
- Invitation codes/links generated by backend
- Store invitations in database with expiration

**Dependencies:** AND-02, BE-01

**Effort:** M

**Owner:** Android

---

### Story 3.4: Message Sharing

#### AND-03: Message Sharing
**Title:** Allow users to share messages with guardians

**Description:** Enable protected users to manually share messages with their guardians.

**Acceptance Criteria:**
- Share button on message detail page
- Select which guardians to share with
- Confirmation dialog
- Shows sharing status
- Encrypted before sending to backend

**Technical Notes:**
- Client-side encryption (AES-256) before API call
- Show success/error feedback

**Dependencies:** AND-02, BE-08

**Effort:** S

**Owner:** Android

---

## Epic 4: Backend API

### Story 4.1: Message Analysis API

#### BE-07: Message Analysis API
**Title:** Implement API endpoints for message analysis

**Description:** Create REST API endpoints for Android app to submit messages and get analysis results.

**Acceptance Criteria:**
- POST `/api/messages/analyze` - receives message, returns analysis (sync or async)
- GET `/api/messages` - list messages for protected user
- GET `/api/messages/{id}` - get message details
- GET `/api/messages/{id}/status` - check analysis status (for async processing)
- POST `/api/messages/{id}/share` - share message with guardians
- Check Redis cache first
- If cache miss, run ML verifier
- Store results in cache and database
- Return analysis immediately (or return job_id for async)
- If ML detects high risk, trigger notification service AND return result to User Dashboard
- Support both sync (wait for ML) and async (poll for results) modes

**Technical Notes:**
- Async endpoints
- Rate limiting (100 requests/minute per user)
- Input validation
- Error handling

**Dependencies:** BE-05, BE-06

**Effort:** M

**Owner:** BE

---

### Story 4.2: Notification Service

#### BE-08: Notification Service
**Title:** Implement notification service for guardians

**Description:** Send notifications to guardians when high-risk messages detected or user shares message.

**Acceptance Criteria:**
- Triggered automatically when ML detects high risk
- Triggered when user manually shares message
- Sends email to guardian (via SMTP/SES)
- Sends SMS to guardian (via Twilio) - optional
- Payload: risk level, warning signs, timestamp, link to Guardian Dashboard
- Does NOT include message content unless user opted in
- Rate limit: max 1 alert per message per guardian
- Only sends if user has consented
- Also sends push notification to Guardian Dashboard via SSE event

**Technical Notes:**
- Check consent flags before sending
- Use email templates
- Async notification sending
- Track notification status in database

**Dependencies:** BE-07, BE-01

**Effort:** M

**Owner:** BE

---

### Story 4.3: Guardian Management API

#### BE-11: Guardian Management API
**Title:** Implement API endpoints for guardian management

**Description:** Create API endpoints for protected users to manage guardians and invitations.

**Acceptance Criteria:**
- POST `/api/guardians/invite` - create guardian invitation
- GET `/api/guardians` - list guardians for protected user
- DELETE `/api/guardians/{id}` - remove guardian
- PATCH `/api/guardians/{id}` - update guardian access level
- POST `/api/guardians/accept` - accept invitation (for guardians)
- GET `/api/invitations/{code}` - validate invitation code

**Technical Notes:**
- Generate unique invitation codes
- Set invitation expiration (7 days)
- Track invitation acceptance

**Dependencies:** BE-01, BE-02

**Effort:** M

**Owner:** BE

---

### Story 4.4: Role-Based Access Control (RBAC)

#### BE-12: RBAC Implementation
**Title:** Implement role-based access control for guardians

**Description:** Enforce access levels for guardians based on their permissions (view all messages vs view shared only).

**Acceptance Criteria:**
- Access level enum: `VIEW_ALL`, `VIEW_SHARED_ONLY`
- Middleware/decoration to check guardian permissions
- `VIEW_ALL`: Guardian can see all messages for protected user (high/medium/safe)
- `VIEW_SHARED_ONLY`: Guardian can only see messages explicitly shared by user
- Enforce at API level: `/api/messages` endpoint checks access level
- Enforce at Guardian Dashboard: filter messages based on access level
- Protected users can change guardian access levels
- Default access level: `VIEW_SHARED_ONLY`

**Technical Notes:**
- Use decorators/middleware for permission checks
- Query filtering based on access_level
- Log access attempts for audit

**Dependencies:** BE-01, BE-07, BE-11

**Effort:** M

**Owner:** BE

---

## Epic 5: Guardian Dashboard (Web)

### Story 5.1: Guardian Dashboard

#### WEB-01: Guardian Dashboard (Web)
**Title:** Build web dashboard for guardians

**Description:** Web application for family members to view shared messages and check on protected users.

**Acceptance Criteria:**
- Next.js application
- Authentication (email/password or magic link)
- Onboarding: sign up, accept guardian invitation from protected user
- List of protected users they're guardians for
- View shared messages (decrypted)
- See risk summaries (high/medium/safe counts) per protected user
- Message detail view with risk analysis
- Mark messages as false positives
- View message history (within expiration period)
- Large, readable text
- Responsive design

**Technical Notes:**
- Next.js 14+ with App Router
- Tailwind CSS for styling
- Server-side rendering
- API routes for backend communication

**Dependencies:** BE-07

**Effort:** L

**Owner:** Web

---

### Story 5.2: SSE Real-time Updates

#### WEB-02: SSE Real-time Updates
**Title:** Implement Server-Sent Events for real-time updates

**Description:** Push real-time updates to Guardian Dashboard when new high-risk messages are detected.

**Acceptance Criteria:**
- SSE endpoint: `/api/events/{guardian_id}`
- Sends events when:
  - New high-risk message detected for protected user
  - User shares a message
  - Message status changes
- Event format: `{type: "new_message", data: {...}}`
- Automatic reconnection on disconnect
- Browser EventSource API integration

**Technical Notes:**
- FastAPI SSE support
- Redis pub/sub for event distribution (optional)
- Handle connection timeouts
- Heartbeat messages every 30 seconds

**Dependencies:** WEB-01, BE-08

**Effort:** M

**Owner:** Web

---

### Story 5.3: Guardian Authentication

#### WEB-03: Guardian Authentication & Invitations
**Title:** Implement authentication and guardian invitation system

**Description:** Allow guardians to sign up, authenticate, and be linked to protected users via invitations.

**Acceptance Criteria:**
- Sign up page (email, password)
- Login page
- Password reset flow
- Session management
- Protected routes
- Guardian invitation system:
  - Protected user can generate invitation link/code
  - Guardian can accept invitation to link accounts
  - Invitation expires after 7 days
  - Track invitation status in database

**Technical Notes:**
- Use NextAuth.js or similar
- JWT tokens or session cookies
- Secure password hashing (bcrypt)

**Dependencies:** WEB-01, BE-01

**Effort:** M

**Owner:** Web

---

## Epic 6: Data Management

### Story 6.1: Auto-Expiration Job

#### BE-09: Auto-Expiration Job
**Title:** Implement scheduled message cleanup

**Description:** Delete messages and shared messages older than expiration time.

**Acceptance Criteria:**
- Runs daily (or on-demand)
- Deletes messages where expires_at < now()
- Deletes shared messages where expires_at < now() OR viewed_at is set
- Logs count of deleted messages
- Does not delete messages already soft-deleted

**Technical Notes:**
- Use APScheduler or cron via scheduled task
- Hard delete (not soft) for expired messages
- Run during low-traffic hours

**Dependencies:** BE-01

**Effort:** S

**Owner:** BE

---

### Story 6.2: Structured Logging

#### BE-10: Structured Logging
**Title:** Implement metadata-only structured logging

**Description:** Add structured JSON logging across all backend operations for auditability.

**Acceptance Criteria:**
- All logs are JSON-formatted with `message_id` and `timestamp`
- Log analysis events: message_id, rules_fired, ml_score, final_risk_level
- Log notification dispatches: message_id, guardian_id (hashed), channel, status
- Log deletions: message_id, deletion_type (user_initiated | auto_expired)
- NO raw message content in logs
- NO full phone numbers (hash or mask)
- NO full email addresses (mask)

**Technical Notes:**
- Use `structlog` or Python `logging` with JSON formatter
- Create logging utility with PII scrubbing
- Mask phones: `***-***-1234`
- Mask emails: `j***@example.com`

**Dependencies:** BE-07, BE-08, BE-09

**Effort:** M

**Owner:** BE

---

## Epic 7: Infrastructure & Testing

### Story 7.1: Deployment

#### INF-01: Deployment Setup
**Title:** Deploy application to production

**Description:** Set up production environment on Railway/Render.

**Acceptance Criteria:**
- FastAPI backend deployed
- PostgreSQL database provisioned
- Redis cache provisioned
- Next.js frontend deployed
- Environment variables configured
- HTTPS enabled
- Domain configured
- Health checks working

**Technical Notes:**
- Railway for backend + database + Redis
- Vercel or Railway for Next.js frontend
- Secrets in environment variables
- Database migrations run on deploy

**Dependencies:** All BE and WEB tickets

**Effort:** L

**Owner:** Infra

---

### Story 7.2: Unit Tests

#### TEST-01: Unit Tests
**Title:** Implement core unit tests

**Description:** Test coverage for critical paths.

**Acceptance Criteria:**
- Rules engine: test each rule type
- ML classifier: test score thresholds
- Analysis orchestrator: test risk level logic
- API endpoints: test request/response
- 80% coverage on core modules

**Technical Notes:**
- Use pytest for backend
- Use JUnit for Android
- Mock ML model for speed
- Mock external services

**Dependencies:** BE-05, BE-07

**Effort:** M

**Owner:** All

---

## Critical Path Summary

```
BE-01 → BE-02 → BE-03 + BE-04 → BE-05 → BE-06
                                    ↓
AND-01 → AND-02 → BE-07 → BE-08 → BE-11 → BE-12
                            ↓         ↓
                        WEB-01 → WEB-02
                            ↓
                        AND-04 → WEB-03
```

**Must-haves for MVP:**
- SMS monitoring working
- On-device rules detecting high risk
- Backend ML verification
- User Dashboard showing alerts
- Guardian Dashboard with real-time updates
- Auto-notification for high-risk messages

**Nice-to-haves:**
- Push notifications (FCM) for Android
- Async ML processing
- Fallback to rules-only if ML unavailable
- Message deduplication
- Rate limiting
