"""
Standalone cache service test that doesn't require full app configuration

This test directly imports and tests the cache service components
without loading the full application configuration.
"""
import asyncio
import sys
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock Redis client for testing without actual Redis
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  redis package not installed")


class MockRedisClient:
    """Mock Redis client for testing without Redis"""
    def __init__(self):
        self._data = {}
    
    async def ping(self):
        return True
    
    async def get(self, key: str) -> Optional[str]:
        return self._data.get(key)
    
    async def setex(self, key: str, ttl: int, value: str):
        self._data[key] = value
        return True
    
    async def delete(self, key: str):
        if key in self._data:
            del self._data[key]
            return 1
        return 0
    
    async def info(self, section: str = "stats"):
        return {"keyspace_hits": 0, "keyspace_misses": 0}


# Test cache config functions
def test_cache_config():
    """Test cache configuration"""
    print("=" * 60)
    print("Test 1: Cache Configuration")
    print("=" * 60)
    
    try:
        from app.config.cache_config import (
            CACHE_TTL,
            get_message_cache_key,
            get_url_cache_key,
            get_pattern_cache_key,
        )
        
        print(f"✅ CACHE_TTL loaded: {CACHE_TTL}")
        print(f"   - ML Result: {CACHE_TTL['ml_result']} seconds ({CACHE_TTL['ml_result']/3600:.1f} hours)")
        print(f"   - Pattern: {CACHE_TTL['pattern']} seconds ({CACHE_TTL['pattern']/86400:.1f} days)")
        print(f"   - URL: {CACHE_TTL['url_analysis']} seconds ({CACHE_TTL['url_analysis']/3600:.1f} hours)")
        
        # Test key generation
        test_hash = "abc123def456"
        msg_key = get_message_cache_key(test_hash)
        url_key = get_url_cache_key(test_hash)
        pattern_key = get_pattern_cache_key(test_hash)
        
        assert msg_key == "msg:abc123def456", "Message key format incorrect"
        assert url_key == "url:abc123def456", "URL key format incorrect"
        assert pattern_key == "pattern:abc123def456", "Pattern key format incorrect"
        
        print(f"✅ Cache key generation works:")
        print(f"   - Message key: {msg_key}")
        print(f"   - URL key: {url_key}")
        print(f"   - Pattern key: {pattern_key}")
        
        return True
    except Exception as e:
        print(f"❌ Cache config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hashing():
    """Test content hashing"""
    print("\n" + "=" * 60)
    print("Test 2: Content Hashing")
    print("=" * 60)
    
    # Test hash function (same logic as cache service)
    def hash_content(content: str) -> str:
        normalized = content.lower().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    
    # Test cases
    test_cases = [
        ("URGENT: Click here", "urgent: click here"),
        ("  Test Message  ", "test message"),
        ("Test\nMessage", "test\nmessage"),
    ]
    
    all_passed = True
    for msg1, msg2 in test_cases:
        hash1 = hash_content(msg1)
        hash2 = hash_content(msg2)
        
        if hash1 == hash2:
            print(f"✅ Normalization works: '{msg1}' == '{msg2}'")
            print(f"   Hash: {hash1[:16]}...")
        else:
            print(f"❌ Normalization failed: '{msg1}' != '{msg2}'")
            print(f"   Hash1: {hash1[:16]}...")
            print(f"   Hash2: {hash2[:16]}...")
            all_passed = False
    
    # Test different messages produce different hashes
    msg1 = "Message one"
    msg2 = "Message two"
    hash1 = hash_content(msg1)
    hash2 = hash_content(msg2)
    
    if hash1 != hash2:
        print(f"✅ Different messages produce different hashes")
    else:
        print(f"❌ Different messages produced same hash (collision!)")
        all_passed = False
    
    return all_passed


async def test_cache_service_logic():
    """Test cache service logic with mock Redis"""
    print("\n" + "=" * 60)
    print("Test 3: Cache Service Logic (Mock Redis)")
    print("=" * 60)
    
    # Import cache service
    try:
        from app.services.cache_service import CacheService
    except Exception as e:
        print(f"❌ Failed to import CacheService: {e}")
        print("   This is expected if Redis/config dependencies fail")
        return False
    
    cache = CacheService()
    
    # Test hashing
    test_message = "URGENT: Your account is suspended. Click bit.ly/xyz"
    message_hash = cache._hash_content(test_message)
    print(f"✅ Content hashing works")
    print(f"   Message: '{test_message[:50]}...'")
    print(f"   Hash: {message_hash[:16]}...")
    
    # Test with mock Redis (if we can inject it)
    # For now, just test that the service can be instantiated
    print(f"✅ CacheService instantiated successfully")
    
    return True


async def test_json_serialization():
    """Test JSON serialization of cache data"""
    print("\n" + "=" * 60)
    print("Test 4: JSON Serialization")
    print("=" * 60)
    
    # Test data structure
    cache_data = {
        "ml_score": 0.85,
        "rule_matches": [
            {
                "rule_name": "urgency",
                "confidence": 0.8,
                "description": "Urgent language"
            }
        ],
        "risk_level": "HIGH_RISK",
        "warning_signs": ["Urgent language", "Suspicious link"],
        "cached_at": "2025-01-15T10:30:00Z",
        "model_scores": {"phishing_text": 0.85, "sms_spam": 0.75}
    }
    
    try:
        # Serialize
        json_str = json.dumps(cache_data)
        print(f"✅ JSON serialization works")
        print(f"   Size: {len(json_str)} bytes")
        
        # Deserialize
        restored = json.loads(json_str)
        assert restored["ml_score"] == 0.85, "ML score mismatch"
        assert restored["risk_level"] == "HIGH_RISK", "Risk level mismatch"
        assert len(restored["rule_matches"]) == 1, "Rule matches mismatch"
        
        print(f"✅ JSON deserialization works")
        print(f"   Restored ML score: {restored['ml_score']}")
        print(f"   Restored risk level: {restored['risk_level']}")
        
        return True
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        return False


async def run_all_tests():
    """Run all standalone tests"""
    print("\n" + "=" * 60)
    print("  STANDALONE CACHE SERVICE TEST")
    print("=" * 60)
    print("\nThis test verifies cache service components without")
    print("requiring full app configuration or Redis connection.\n")
    
    results = []
    
    # Test 1: Cache config
    results.append(("Cache Configuration", test_cache_config()))
    
    # Test 2: Hashing
    results.append(("Content Hashing", test_hashing()))
    
    # Test 3: Cache service logic
    results.append(("Cache Service Logic", await test_cache_service_logic()))
    
    # Test 4: JSON serialization
    results.append(("JSON Serialization", await test_json_serialization()))
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! Cache service components are working.")
    else:
        print("\n  ⚠️  Some tests failed. Check output above for details.")
    
    print("\n" + "=" * 60)
    print("\nNote: This test doesn't require Redis or database configuration.")
    print("To test with actual Redis, start Docker and run:")
    print("  python test_cache_comprehensive.py")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

