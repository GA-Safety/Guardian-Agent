# Quick Start: Testing Cache Service

## Option 1: Start Docker and Redis (Recommended)

### Step 1: Start Docker Desktop

1. **Open Docker Desktop** on your Mac
   - Look for Docker icon in Applications or menu bar
   - Click to open Docker Desktop
   - Wait until Docker status shows "Docker Desktop is running"

2. **Verify Docker is running:**
   ```bash
   docker ps
   # Should return empty list or running containers (not an error)
   ```

### Step 2: Start Redis

```bash
# From project root
docker-compose up -d redis

# Verify Redis is running
docker ps | grep redis
# Should show redis container
```

### Step 3: Test Cache Service

```bash
cd backend
source ../.venv/bin/activate

# Run simple test
python test_cache_service.py

# Or comprehensive test
python test_cache_comprehensive.py
```

---

## Option 2: Test Without Redis (Graceful Degradation)

The cache service is designed to work **even without Redis**! It will:
- ✅ Run all tests without errors
- ⚠️ Show warnings that Redis is unavailable
- ✅ Return `None` for cache operations (graceful degradation)
- ✅ Demonstrate that the app continues working

**To test without Redis:**

```bash
cd backend
source ../.venv/bin/activate

# These will work, just show Redis unavailable warnings
python test_cache_service.py
python test_cache_comprehensive.py
```

**Expected output without Redis:**
```
⚠️  WARNING: Redis is not available
This is OK - the service will work without Redis
To start Redis: docker-compose up -d redis

❌ Cache miss (Redis may not be running)
```

This is **expected behavior** - the service gracefully handles Redis being unavailable.

---

## Troubleshooting

### Docker Not Starting?

1. **Check if Docker Desktop is installed:**
   ```bash
   which docker
   # Should return: /usr/local/bin/docker
   ```

2. **If Docker Desktop isn't installed:**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

3. **If Docker Desktop is installed but not running:**
   - Open Docker Desktop manually
   - Wait for it to fully start (whale icon in menu bar should be steady)

### Redis Connection Issues?

If Redis container starts but tests still fail:

1. **Check Redis is actually running:**
   ```bash
   docker ps | grep redis
   ```

2. **Check Redis logs:**
   ```bash
   docker-compose logs redis
   ```

3. **Test Redis connection manually:**
   ```bash
   docker exec -it guardian-redis redis-cli ping
   # Should return: PONG
   ```

### Permission Errors?

If you see permission errors with `.env` file:
- Make sure you're in the correct directory
- Check file permissions: `ls -la .env`
- The cache service will work without `.env` (uses defaults)

---

## What to Expect

### With Redis Running:
```
✅ Redis connection successful
✅ Cache write success
✅ Cache hit! ML score: 0.85, Risk: HIGH_RISK
✅ URL cache hit! Risk score: 0.92
```

### Without Redis:
```
⚠️  Redis is not available
❌ Cache miss (Redis may not be running)
⚠️  Failed to cache (Redis may be unavailable)
```

**Both are valid!** The service is designed to work in both scenarios.

---

## Next Steps

Once you've verified the cache service works:

1. ✅ Cache service is ready
2. ⏳ Integrate into `AnalysisOrchestrator` 
3. ⏳ Implement ML model integration
4. ⏳ Add URL extraction and analysis

---

## Quick Commands Reference

```bash
# Start Redis
docker-compose up -d redis

# Stop Redis
docker-compose down

# Check Redis status
docker ps | grep redis

# Test cache (simple)
cd backend && python test_cache_service.py

# Test cache (comprehensive)
cd backend && python test_cache_comprehensive.py

# Test integration
cd backend && python test_cache_integration.py
```


