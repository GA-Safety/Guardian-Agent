"""
Cache configuration for Redis caching service
"""
import os
from typing import Dict

# Cache TTL settings (in seconds)
CACHE_TTL = {
    "ml_result": int(os.getenv("CACHE_TTL_ML_RESULT", "86400")),  # 24 hours
    "pattern": int(os.getenv("CACHE_TTL_PATTERN", "604800")),  # 7 days
    "url_analysis": int(os.getenv("CACHE_TTL_URL_ANALYSIS", "86400")),  # 24 hours
}

# Cache key prefixes
CACHE_KEY_PREFIXES = {
    "message": "msg",
    "pattern": "pattern",
    "url": "url",
}

# Cache key format: {prefix}:{hash}
def get_message_cache_key(message_hash: str) -> str:
    """Generate cache key for message analysis result"""
    return f"{CACHE_KEY_PREFIXES['message']}:{message_hash}"


def get_pattern_cache_key(pattern_hash: str) -> str:
    """Generate cache key for pattern match result"""
    return f"{CACHE_KEY_PREFIXES['pattern']}:{pattern_hash}"


def get_url_cache_key(url_hash: str) -> str:
    """Generate cache key for URL analysis result"""
    return f"{CACHE_KEY_PREFIXES['url']}:{url_hash}"

