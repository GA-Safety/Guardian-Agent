"""
Simple test script for cache service

Tests basic caching functionality without requiring database.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.cache_service import CacheService


async def test_cache_service():
    """Test cache service functionality"""
    print("🧪 Testing Cache Service...")
    print("-" * 50)
    
    cache = CacheService()
    
    # Test 1: Cache and retrieve message analysis
    print("\n1. Testing message analysis caching...")
    test_message = "URGENT: Your account is suspended. Click bit.ly/xyz to verify."
    
    # Try to get from cache (should be None initially)
    cached = await cache.get_cached_analysis(test_message)
    print(f"   Initial cache lookup: {cached}")
    
    # Cache a result
    cached_success = await cache.cache_analysis_result(
        message_content=test_message,
        ml_score=0.85,
        rule_matches=[
            {"rule_name": "urgency", "confidence": 0.8, "description": "Urgent language"},
            {"rule_name": "suspicious_link", "confidence": 0.9, "description": "Suspicious link"},
        ],
        risk_level="HIGH_RISK",
        warning_signs=["Urgent language", "Suspicious link detected"],
        model_scores={"phishing_text": 0.85, "sms_spam": 0.75},
    )
    print(f"   Cache write success: {cached_success}")
    
    # Retrieve from cache
    cached = await cache.get_cached_analysis(test_message)
    if cached:
        print(f"   ✅ Cache hit! ML score: {cached.get('ml_score')}, Risk: {cached.get('risk_level')}")
    else:
        print(f"   ❌ Cache miss (Redis may not be running)")
    
    # Test 2: URL caching
    print("\n2. Testing URL analysis caching...")
    test_url = "https://bit.ly/suspicious-link"
    
    url_cached = await cache.get_cached_url_analysis(test_url)
    print(f"   Initial URL cache lookup: {url_cached}")
    
    url_success = await cache.cache_url_analysis(
        url=test_url,
        risk_score=0.92,
        label="phishing",
    )
    print(f"   URL cache write success: {url_success}")
    
    url_cached = await cache.get_cached_url_analysis(test_url)
    if url_cached:
        print(f"   ✅ URL cache hit! Risk score: {url_cached.get('risk_score')}")
    else:
        print(f"   ❌ URL cache miss (Redis may not be running)")
    
    # Test 3: Cache invalidation
    print("\n3. Testing cache invalidation...")
    invalidated = await cache.invalidate_message_cache(test_message)
    print(f"   Invalidation success: {invalidated}")
    
    cached_after = await cache.get_cached_analysis(test_message)
    if cached_after is None:
        print(f"   ✅ Cache successfully invalidated")
    else:
        print(f"   ⚠️  Cache still exists (may be expected if Redis unavailable)")
    
    # Test 4: Cache stats
    print("\n4. Testing cache statistics...")
    stats = await cache.get_cache_stats()
    print(f"   Cache stats: {stats}")
    
    print("\n" + "-" * 50)
    print("✨ Cache service test complete!")
    print("\nNote: If Redis is not running, cache operations will fail gracefully.")
    print("Start Redis with: docker-compose up -d redis")


if __name__ == "__main__":
    asyncio.run(test_cache_service())

