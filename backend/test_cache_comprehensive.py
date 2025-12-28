"""
Comprehensive test script for cache service

Tests all cache functionality with detailed output and error handling.
"""
import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.cache_service import CacheService
from app.config.cache_config import CACHE_TTL


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_test(name: str):
    """Print test name"""
    print(f"{Colors.BOLD}▶ {name}{Colors.RESET}")


def print_success(message: str):
    """Print success message"""
    print(f"  {Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"  {Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message"""
    print(f"  {Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"  {Colors.BLUE}ℹ️  {message}{Colors.RESET}")


async def test_redis_connection():
    """Test 1: Redis connection"""
    print_header("Test 1: Redis Connection")
    
    cache = CacheService()
    client = await cache._get_client()
    
    if client is None:
        print_warning("Redis is not available")
        print_info("This is OK - the service will work without Redis")
        print_info("To start Redis: docker-compose up -d redis")
        return False
    else:
        print_success("Redis connection successful")
        return True


async def test_message_caching():
    """Test 2: Message analysis caching"""
    print_header("Test 2: Message Analysis Caching")
    
    cache = CacheService()
    
    # Test messages
    test_cases = [
        {
            "content": "URGENT: Your account is suspended. Click bit.ly/xyz to verify.",
            "ml_score": 0.85,
            "risk_level": "HIGH_RISK",
        },
        {
            "content": "Hi, this is your bank. Please verify your account.",
            "ml_score": 0.45,
            "risk_level": "MEDIUM_RISK",
        },
        {
            "content": "Thanks for your order! Your package will arrive tomorrow.",
            "ml_score": 0.15,
            "risk_level": "SAFE",
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print_test(f"Test Case {i}: {test_case['risk_level']} message")
        
        message = test_case["content"]
        
        # Check initial cache (should be None)
        cached = await cache.get_cached_analysis(message)
        if cached is None:
            print_info("Initial cache: empty (expected)")
        else:
            print_warning(f"Found existing cache: {cached.get('risk_level')}")
        
        # Cache the result
        success = await cache.cache_analysis_result(
            message_content=message,
            ml_score=test_case["ml_score"],
            rule_matches=[
                {
                    "rule_name": "test_rule",
                    "confidence": 0.8,
                    "description": "Test rule match"
                }
            ],
            risk_level=test_case["risk_level"],
            warning_signs=["Test warning sign"],
            model_scores={"phishing_text": test_case["ml_score"]},
        )
        
        if success:
            print_success("Result cached successfully")
        else:
            print_error("Failed to cache result (Redis may be unavailable)")
            continue
        
        # Retrieve from cache
        cached = await cache.get_cached_analysis(message)
        if cached:
            print_success(f"Cache hit! Retrieved: risk={cached.get('risk_level')}, score={cached.get('ml_score')}")
            
            # Verify data integrity
            assert cached["ml_score"] == test_case["ml_score"], "ML score mismatch"
            assert cached["risk_level"] == test_case["risk_level"], "Risk level mismatch"
            print_success("Data integrity verified")
        else:
            print_error("Cache miss after writing (unexpected)")


async def test_url_caching():
    """Test 3: URL analysis caching"""
    print_header("Test 3: URL Analysis Caching")
    
    cache = CacheService()
    
    test_urls = [
        {"url": "https://bit.ly/suspicious-link", "risk": 0.92, "label": "phishing"},
        {"url": "https://example.com/verify", "risk": 0.35, "label": "safe"},
        {"url": "http://tinyurl.com/xyz123", "risk": 0.78, "label": "suspicious"},
    ]
    
    for i, test_url in enumerate(test_urls, 1):
        print_test(f"URL {i}: {test_url['url']}")
        
        url = test_url["url"]
        
        # Check cache
        cached = await cache.get_cached_url_analysis(url)
        if cached is None:
            print_info("Initial cache: empty")
        else:
            print_warning(f"Found existing cache: risk={cached.get('risk_score')}")
        
        # Cache URL analysis
        success = await cache.cache_url_analysis(
            url=url,
            risk_score=test_url["risk"],
            label=test_url["label"],
        )
        
        if not success:
            print_error("Failed to cache URL (Redis may be unavailable)")
            continue
        
        print_success("URL analysis cached")
        
        # Retrieve
        cached = await cache.get_cached_url_analysis(url)
        if cached:
            print_success(f"Retrieved: risk={cached.get('risk_score')}, label={cached.get('label')}")
            assert cached["risk_score"] == test_url["risk"], "Risk score mismatch"
        else:
            print_error("Cache miss after writing")


async def test_cache_invalidation():
    """Test 4: Cache invalidation"""
    print_header("Test 4: Cache Invalidation")
    
    cache = CacheService()
    
    test_message = "Test message for invalidation"
    
    # Cache a result
    await cache.cache_analysis_result(
        message_content=test_message,
        ml_score=0.75,
        rule_matches=[],
        risk_level="MEDIUM_RISK",
        warning_signs=[],
    )
    
    # Verify it's cached
    cached = await cache.get_cached_analysis(test_message)
    if cached:
        print_success("Message cached successfully")
    else:
        print_warning("Message not cached (Redis may be unavailable)")
        return
    
    # Invalidate
    invalidated = await cache.invalidate_message_cache(test_message)
    if invalidated:
        print_success("Cache invalidated")
    else:
        print_error("Failed to invalidate cache")
        return
    
    # Verify it's gone
    cached_after = await cache.get_cached_analysis(test_message)
    if cached_after is None:
        print_success("Cache successfully removed")
    else:
        print_error("Cache still exists after invalidation")


async def test_hash_consistency():
    """Test 5: Hash consistency (same content = same hash)"""
    print_header("Test 5: Hash Consistency")
    
    cache = CacheService()
    
    # Same content with different formatting
    messages = [
        "URGENT: Click here",
        "urgent: click here",
        "  URGENT: Click here  ",
    ]
    
    hashes = [cache._hash_content(msg) for msg in messages]
    
    print_test("Testing hash normalization")
    print_info(f"Message 1: '{messages[0]}' → hash: {hashes[0][:16]}...")
    print_info(f"Message 2: '{messages[1]}' → hash: {hashes[1][:16]}...")
    print_info(f"Message 3: '{messages[2]}' → hash: {hashes[2][:16]}...")
    
    if len(set(hashes)) == 1:
        print_success("All messages produce the same hash (normalization working)")
    else:
        print_error("Hashes differ - normalization may not be working correctly")


async def test_cache_stats():
    """Test 6: Cache statistics"""
    print_header("Test 6: Cache Statistics")
    
    cache = CacheService()
    stats = await cache.get_cache_stats()
    
    print_test("Retrieving cache statistics")
    print_info(f"Stats: {json.dumps(stats, indent=2)}")
    
    if stats.get("status") == "available":
        print_success("Cache statistics retrieved")
        hits = stats.get("keyspace_hits", 0)
        misses = stats.get("keyspace_misses", 0)
        print_info(f"Cache hits: {hits}, misses: {misses}")
    elif stats.get("status") == "unavailable":
        print_warning("Redis unavailable - stats not available")
    else:
        print_error(f"Error getting stats: {stats.get('error')}")


async def test_ttl_configuration():
    """Test 7: TTL configuration"""
    print_header("Test 7: TTL Configuration")
    
    from app.config.cache_config import CACHE_TTL
    
    print_test("Checking TTL settings")
    print_info(f"ML Result TTL: {CACHE_TTL['ml_result']} seconds ({CACHE_TTL['ml_result'] / 3600:.1f} hours)")
    print_info(f"Pattern TTL: {CACHE_TTL['pattern']} seconds ({CACHE_TTL['pattern'] / 86400:.1f} days)")
    print_info(f"URL Analysis TTL: {CACHE_TTL['url_analysis']} seconds ({CACHE_TTL['url_analysis'] / 3600:.1f} hours)")
    
    print_success("TTL configuration loaded")


async def test_graceful_degradation():
    """Test 8: Graceful degradation (works without Redis)"""
    print_header("Test 8: Graceful Degradation")
    
    cache = CacheService()
    
    # These should not raise exceptions even if Redis is down
    print_test("Testing operations without Redis")
    
    try:
        result = await cache.get_cached_analysis("test message")
        print_success("get_cached_analysis() handled gracefully")
        print_info(f"Result: {result} (None is expected if Redis unavailable)")
    except Exception as e:
        print_error(f"get_cached_analysis() raised exception: {e}")
    
    try:
        result = await cache.cache_analysis_result(
            message_content="test",
            ml_score=0.5,
            rule_matches=[],
            risk_level="SAFE",
            warning_signs=[],
        )
        print_success("cache_analysis_result() handled gracefully")
        print_info(f"Result: {result} (False is expected if Redis unavailable)")
    except Exception as e:
        print_error(f"cache_analysis_result() raised exception: {e}")


async def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  COMPREHENSIVE CACHE SERVICE TEST SUITE")
    print("=" * 60)
    print(f"{Colors.RESET}")
    
    redis_available = await test_redis_connection()
    
    if not redis_available:
        print(f"\n{Colors.YELLOW}")
        print("⚠️  WARNING: Redis is not available")
        print("Some tests will show expected failures.")
        print("To start Redis: docker-compose up -d redis")
        print(f"{Colors.RESET}\n")
    
    await test_message_caching()
    await test_url_caching()
    await test_cache_invalidation()
    await test_hash_consistency()
    await test_cache_stats()
    await test_ttl_configuration()
    await test_graceful_degradation()
    
    print_header("Test Suite Complete")
    print_success("All tests completed!")
    print_info("Review the output above for any failures or warnings")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()

