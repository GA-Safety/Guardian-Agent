"""
Redis connection pool management
"""
import redis.asyncio as redis
from typing import Optional
from .config import settings


class RedisClient:
    """Redis client with connection pooling"""
    
    _client: Optional[redis.Redis] = None
    
    @classmethod
    async def get_client(cls) -> redis.Redis:
        """Get or create Redis client"""
        if cls._client is None:
            cls._client = redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                password=settings.REDIS_PASSWORD,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
        return cls._client
    
    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._client:
            await cls._client.close()
            cls._client = None


async def get_redis() -> redis.Redis:
    """Dependency for getting Redis client"""
    return await RedisClient.get_client()

