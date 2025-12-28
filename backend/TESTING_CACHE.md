# Testing the Cache Service

This guide explains how to test the Redis caching service implementation.

## Prerequisites

1. **Redis running** (optional but recommended):
   ```bash
   docker-compose up -d redis
   ```
   
   Or verify Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. **Python environment activated**:
   ```bash
   cd backend
   source ../.venv/bin/activate
   ```

## Test Scripts

### 1. Simple Test (`test_cache_service.py`)

**Purpose:** Basic functionality test

**Run:**
```bash
python test_cache_service.py
```

**What it tests:**
- Message analysis caching
- URL analysis caching
- Cache invalidation
- Cache statistics

**Output:** Simple pass/fail indicators

---

### 2. Comprehensive Test (`test_cache_comprehensive.py`)

**Purpose:** Detailed test suite with colored output

**Run:**
```bash
python test_cache_comprehensive.py
```

**What it tests:**
1. ✅ Redis connection
2. ✅ Message caching (multiple test cases)
3. ✅ URL caching
4. ✅ Cache invalidation
5. ✅ Hash consistency (normalization)
6. ✅ Cache statistics
7. ✅ TTL configuration
8. ✅ Graceful degradation (works without Redis)

**Output:** 
- Color-coded results (green ✅, red ❌, yellow ⚠️)
- Detailed information for each test
- Clear pass/fail indicators

**Example output:**
```
============================================================
  COMPREHENSIVE CACHE SERVICE TEST SUITE
============================================================

============================================================
Test 1: Redis Connection
============================================================

▶ Testing Redis connection
  ✅ Redis connection successful
```

---

### 3. Integration Test (`test_cache_integration.py`)

**Purpose:** Demonstrates how cache integrates with Analysis Orchestrator

**Run:**
```bash
python test_cache_integration.py
```

**What it demonstrates:**
- Cache check before running analysis
- Caching results after analysis
- Performance benefit of cache hits
- Integration pattern for orchestrator

**Output:** Step-by-step demonstration of cache workflow

---

## Expected Results

### With Redis Running

All tests should pass:
- ✅ Cache writes succeed
- ✅ Cache reads return data
- ✅ Cache invalidation works
- ✅ Statistics are available

### Without Redis

Tests should still run but show warnings:
- ⚠️ Redis unavailable messages
- Cache operations return `None` or `False`
- No exceptions raised (graceful degradation)

---

## Troubleshooting

### Redis Connection Failed

**Error:** `Redis connection failed` or `Connection refused`

**Solution:**
```bash
# Start Redis with Docker
docker-compose up -d redis

# Or check if Redis is running
redis-cli ping
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment
source ../.venv/bin/activate

# Install dependencies if needed
pip install -r requirements.txt
```

### Cache Not Working

**Symptom:** Cache always returns `None`

**Check:**
1. Redis is running: `redis-cli ping`
2. Redis connection settings in `.env`:
   ```
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   ```
3. Check Redis logs: `docker-compose logs redis`

---

## Manual Testing

You can also test manually using Redis CLI:

```bash
# Connect to Redis
redis-cli

# Check if keys exist
KEYS msg:*

# View a cached value
GET msg:abc123...

# Check TTL
TTL msg:abc123...

# Delete a key
DEL msg:abc123...
```

---

## Performance Testing

To see cache performance benefits:

1. Run analysis on a message (cache miss)
2. Run analysis on the same message again (cache hit)
3. Compare response times:
   - Cache miss: ~200-500ms (ML inference)
   - Cache hit: <1ms (Redis lookup)

---

## Next Steps

After verifying cache works:

1. ✅ Integrate into `AnalysisOrchestrator`
2. ✅ Add cache checks before ML inference
3. ✅ Cache results after analysis completes
4. ✅ Monitor cache hit rates in production

