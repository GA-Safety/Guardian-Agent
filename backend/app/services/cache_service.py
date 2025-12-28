"""
Redis caching service for analysis results

Caches ML model predictions, pattern matches, and URL analysis results
to avoid reprocessing similar messages.
"""
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import redis.asyncio as redis

from ..redis_client import RedisClient
from ..config.cache_config import (
    CACHE_TTL,
    get_message_cache_key,
    get_pattern_cache_key,
    get_url_cache_key,
)

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service for caching analysis results in Redis.
    
    Handles:
    - Message content hashing (SHA-256)
    - Caching ML model predictions
    - Caching pattern match results
    - Caching URL analysis results
    - Graceful degradation when Redis is unavailable
    """
    
    def __init__(self):
        """Initialize cache service"""
        self._redis_client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> Optional[redis.Redis]:
        """
        Get Redis client, handling connection failures gracefully.
        
        Returns:
            Redis client or None if unavailable
        """
        if self._redis_client is None:
            try:
                self._redis_client = await RedisClient.get_client()
                # Test connection
                await self._redis_client.ping()
            except Exception as e:
                logger.debug(f"Redis client unavailable: {e}")
                return None
        return self._redis_client
    
    def _hash_content(self, content: str) -> str:
        """
        Generate SHA-256 hash of message content.
        
        Args:
            content: Message content to hash
            
        Returns:
            Hexadecimal hash string
        """
        # Normalize content: lowercase, strip whitespace
        normalized = content.lower().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    
    async def get_cached_analysis(
        self, message_content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result for a message.
        
        Args:
            message_content: The SMS message text
            
        Returns:
            Cached analysis result dict or None if not found/cache unavailable
        """
        client = await self._get_client()
        if client is None:
            return None
        
        try:
            message_hash = self._hash_content(message_content)
            cache_key = get_message_cache_key(message_hash)
            
            cached_data = await client.get(cache_key)
            if cached_data is None:
                logger.debug(f"Cache miss for message hash: {message_hash[:8]}...")
                return None
            
            # Parse JSON data
            result = json.loads(cached_data)
            logger.debug(f"Cache hit for message hash: {message_hash[:8]}...")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to decode cached analysis: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error retrieving cached analysis: {e}")
            return None
    
    async def cache_analysis_result(
        self,
        message_content: str,
        ml_score: float,
        rule_matches: List[Dict[str, Any]],
        risk_level: str,
        warning_signs: List[str],
        **extra_data: Any,
    ) -> bool:
        """
        Cache analysis result for a message.
        
        Args:
            message_content: The SMS message text
            ml_score: ML model score (0.0-1.0)
            rule_matches: List of rule match dictionaries
            risk_level: Final risk level (SAFE, MEDIUM_RISK, HIGH_RISK)
            warning_signs: List of warning sign descriptions
            **extra_data: Additional data to cache (e.g., url_scores, model_scores)
            
        Returns:
            True if cached successfully, False otherwise
        """
        client = await self._get_client()
        if client is None:
            return False
        
        try:
            message_hash = self._hash_content(message_content)
            cache_key = get_message_cache_key(message_hash)
            
            # Prepare cache data
            cache_data = {
                "ml_score": ml_score,
                "rule_matches": rule_matches,
                "risk_level": risk_level,
                "warning_signs": warning_signs,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                **extra_data,
            }
            
            # Store with TTL
            await client.setex(
                cache_key,
                CACHE_TTL["ml_result"],
                json.dumps(cache_data),
            )
            
            logger.debug(f"Cached analysis for message hash: {message_hash[:8]}...")
            return True
            
        except Exception as e:
            logger.warning(f"Error caching analysis result: {e}")
            return False
    
    async def get_cached_url_analysis(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached URL analysis result.
        
        Args:
            url: URL to check
            
        Returns:
            Cached URL analysis result or None if not found
        """
        client = await self._get_client()
        if client is None:
            return None
        
        try:
            url_hash = self._hash_content(url)
            cache_key = get_url_cache_key(url_hash)
            
            cached_data = await client.get(cache_key)
            if cached_data is None:
                return None
            
            result = json.loads(cached_data)
            logger.debug(f"Cache hit for URL: {url[:50]}...")
            return result
            
        except Exception as e:
            logger.debug(f"Error retrieving cached URL analysis: {e}")
            return None
    
    async def cache_url_analysis(
        self, url: str, risk_score: float, label: str, **extra_data: Any
    ) -> bool:
        """
        Cache URL analysis result.
        
        Args:
            url: URL that was analyzed
            risk_score: Risk score (0.0-1.0)
            label: Classification label
            **extra_data: Additional data to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        client = await self._get_client()
        if client is None:
            return False
        
        try:
            url_hash = self._hash_content(url)
            cache_key = get_url_cache_key(url_hash)
            
            cache_data = {
                "risk_score": risk_score,
                "label": label,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                **extra_data,
            }
            
            await client.setex(
                cache_key,
                CACHE_TTL["url_analysis"],
                json.dumps(cache_data),
            )
            
            logger.debug(f"Cached URL analysis for: {url[:50]}...")
            return True
            
        except Exception as e:
            logger.warning(f"Error caching URL analysis: {e}")
            return False
    
    async def get_cached_pattern(self, pattern: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached pattern match result.
        
        Args:
            pattern: Pattern string to check
            
        Returns:
            Cached pattern result or None if not found
        """
        client = await self._get_client()
        if client is None:
            return None
        
        try:
            pattern_hash = self._hash_content(pattern)
            cache_key = get_pattern_cache_key(pattern_hash)
            
            cached_data = await client.get(cache_key)
            if cached_data is None:
                return None
            
            result = json.loads(cached_data)
            return result
            
        except Exception as e:
            logger.debug(f"Error retrieving cached pattern: {e}")
            return None
    
    async def cache_pattern(
        self, pattern: str, matches: List[Dict[str, Any]], **extra_data: Any
    ) -> bool:
        """
        Cache pattern match result.
        
        Args:
            pattern: Pattern string
            matches: List of pattern matches
            **extra_data: Additional data to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        client = await self._get_client()
        if client is None:
            return False
        
        try:
            pattern_hash = self._hash_content(pattern)
            cache_key = get_pattern_cache_key(pattern_hash)
            
            cache_data = {
                "matches": matches,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                **extra_data,
            }
            
            await client.setex(
                cache_key,
                CACHE_TTL["pattern"],
                json.dumps(cache_data),
            )
            
            return True
            
        except Exception as e:
            logger.warning(f"Error caching pattern: {e}")
            return False
    
    async def invalidate_message_cache(self, message_content: str) -> bool:
        """
        Invalidate cached analysis for a message.
        
        Args:
            message_content: Message content to invalidate
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        client = await self._get_client()
        if client is None:
            return False
        
        try:
            message_hash = self._hash_content(message_content)
            cache_key = get_message_cache_key(message_hash)
            
            deleted = await client.delete(cache_key)
            if deleted:
                logger.debug(f"Invalidated cache for message hash: {message_hash[:8]}...")
            
            return bool(deleted)
            
        except Exception as e:
            logger.warning(f"Error invalidating cache: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics (for monitoring/debugging).
        
        Returns:
            Dictionary with cache statistics
        """
        client = await self._get_client()
        if client is None:
            return {"status": "unavailable"}
        
        try:
            info = await client.info("stats")
            return {
                "status": "available",
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}


# Singleton instance
_cache_service: Optional[CacheService] = None


async def get_cache_service() -> CacheService:
    """
    Get or create cache service instance.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

