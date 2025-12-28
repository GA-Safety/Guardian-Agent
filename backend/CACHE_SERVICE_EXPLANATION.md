# Cache Service Implementation Explanation

This document explains each component of the Redis caching service implementation.

## Overview

The caching service stores analysis results (ML scores, rule matches, URL analysis) in Redis to avoid reprocessing identical or similar messages. This significantly improves performance and reduces ML model inference costs.

---

## File-by-File Breakdown

### 1. `backend/app/config/cache_config.py`

**Purpose:** Centralized configuration for cache behavior.

**What it does:**
- **TTL Settings (Time-To-Live):** Defines how long cached data stays in Redis
  - `ml_result`: 24 hours (86400 seconds) - ML analysis results
  - `pattern`: 7 days (604800 seconds) - Pattern match results  
  - `url_analysis`: 24 hours (86400 seconds) - URL risk analysis
  
- **Cache Key Prefixes:** Organizes cache keys by type
  - `msg:` for message analysis
  - `pattern:` for pattern matches
  - `url:` for URL analysis

- **Key Generation Functions:** Creates consistent cache keys
  - `get_message_cache_key(hash)` → `"msg:abc123..."`
  - `get_pattern_cache_key(hash)` → `"pattern:def456..."`
  - `get_url_cache_key(hash)` → `"url:ghi789..."`

**Why it matters:** 
- Makes TTL values easy to tune via environment variables
- Ensures consistent cache key naming across the codebase
- Prevents cache key collisions between different data types

---

### 2. `backend/app/services/cache_service.py`

**Purpose:** Main service that handles all Redis caching operations.

#### Key Components:

##### `CacheService` Class

**`_get_client()` method:**
- Gets or creates Redis connection
- Tests connection with `ping()`
- Returns `None` if Redis unavailable (graceful degradation)
- **Why:** App continues working even if Redis is down

**`_hash_content()` method:**
- Takes message content, normalizes it (lowercase, strip whitespace)
- Generates SHA-256 hash
- **Why:** Same message content = same hash = same cache key
- Example: `"URGENT: Click here"` and `"urgent: click here"` → same hash

**`get_cached_analysis()` method:**
- Checks if analysis result exists in cache
- Returns cached data (ML score, risk level, etc.) or `None`
- **Why:** Skip expensive ML inference if we've seen this message before

**`cache_analysis_result()` method:**
- Stores complete analysis result in Redis
- Includes: ML score, rule matches, risk level, warning signs
- Sets TTL (24 hours by default)
- **Why:** Future requests for same message get instant results

**`get_cached_url_analysis()` / `cache_url_analysis()` methods:**
- Similar to message caching, but for URL risk scores
- **Why:** URLs are analyzed separately, so cache them separately

**`get_cached_pattern()` / `cache_pattern()` methods:**
- Caches pattern match results
- **Why:** Pattern matching can be expensive, cache helps

**`invalidate_message_cache()` method:**
- Deletes cached result for a message
- **Why:** If analysis needs to be re-run (e.g., model updated), clear cache

**`get_cache_stats()` method:**
- Returns Redis statistics (hits, misses)
- **Why:** Monitor cache performance

#### Singleton Pattern

The `get_cache_service()` function ensures only one `CacheService` instance exists:
- **Why:** Avoids creating multiple Redis connections
- Reuses the same service instance across requests

---

### 3. Module Exports (`__init__.py` files)

**What changed:**
- `backend/app/services/__init__.py`: Exports `CacheService` and `get_cache_service()`
- `backend/app/config/__init__.py`: Exports cache config functions

**Why:** Makes imports cleaner:
```python
from app.services import CacheService  # Instead of app.services.cache_service
from app.config import CACHE_TTL  # Instead of app.config.cache_config
```

---

## How It Works (Flow Diagram)

```
1. Message arrives → "URGENT: Click bit.ly/xyz"
                    ↓
2. Hash content → SHA256("urgent: click bit.ly/xyz") = "abc123..."
                    ↓
3. Check cache → Redis GET "msg:abc123..."
                    ↓
   ┌───────────────┴───────────────┐
   │                               │
   │ Cache Hit?                    │ Cache Miss?
   │                               │
   ↓                               ↓
4a. Return cached result    4b. Run ML analysis
   (instant, <1ms)                (200-500ms)
                                ↓
                           5. Cache result
                                ↓
                           6. Return result
```

---

## Cache Key Structure

```
msg:{sha256_hash}          → Full analysis result
url:{sha256_hash}          → URL risk score
pattern:{sha256_hash}      → Pattern matches
```

Example:
- Message: `"URGENT: Click here"`
- Hash: `a1b2c3d4e5f6...` (64 hex chars)
- Cache key: `msg:a1b2c3d4e5f6...`

---

## Graceful Degradation

**What happens if Redis is down?**

1. `_get_client()` returns `None`
2. Cache methods return `None` or `False` (not exceptions)
3. App continues normally, just without caching
4. ML analysis still runs, just not cached

**Why this design:**
- Redis is a performance optimization, not critical
- App should work even if Redis fails
- No user-facing errors from cache failures

---

## Data Stored in Cache

### Message Analysis Cache:
```json
{
  "ml_score": 0.85,
  "rule_matches": [
    {"rule_name": "urgency", "confidence": 0.8, "description": "Urgent language"}
  ],
  "risk_level": "HIGH_RISK",
  "warning_signs": ["Urgent language", "Suspicious link"],
  "cached_at": "2025-01-15T10:30:00Z",
  "model_scores": {"phishing_text": 0.85, "sms_spam": 0.75}
}
```

### URL Analysis Cache:
```json
{
  "risk_score": 0.92,
  "label": "phishing",
  "cached_at": "2025-01-15T10:30:00Z"
}
```

---

## Performance Benefits

**Without Cache:**
- Every message → Full ML inference (200-500ms)
- 1000 messages/day → 1000 ML calls

**With Cache:**
- First message → ML inference (200-500ms) + cache write
- Duplicate messages → Cache read (<1ms)
- 1000 messages, 100 unique → 100 ML calls, 900 cache hits
- **~90% reduction in ML inference time**

---

## Environment Variables

You can tune cache behavior via environment variables:

```bash
# In .env file
CACHE_TTL_ML_RESULT=86400      # 24 hours (default)
CACHE_TTL_PATTERN=604800       # 7 days (default)
CACHE_TTL_URL_ANALYSIS=86400   # 24 hours (default)
```

---

## Next Steps

This caching service is ready to integrate into:
1. `AnalysisOrchestrator` - Check cache before running ML
2. ML model service - Cache model predictions
3. URL analysis service - Cache URL risk scores

The service is designed to be non-intrusive - it won't break anything if Redis is unavailable.

