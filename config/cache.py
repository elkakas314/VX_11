"""
VX11 Cache Layer (Redis)
========================
Centralized caching for gateway endpoints to reduce latency and load.

Features:
- TTL-based cache with automatic expiration
- Per-endpoint configuration
- Cache invalidation hooks
- Health monitoring
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional

try:
    import aioredis

    # Check API version (2.x vs 1.x)
    _AIOREDIS_V2 = hasattr(aioredis, "from_url")
except ImportError:
    aioredis = None  # type: ignore
    _AIOREDIS_V2 = False

logger = logging.getLogger(__name__)


class CacheLayer:
    """Redis-based cache with async support (aioredis 2.x compatible)"""

    def __init__(self):
        self.redis = None
        self.enabled = os.getenv("VX11_CACHE_ENABLED", "true").lower() == "true"
        self.redis_url = os.getenv("VX11_REDIS_URL", "redis://localhost:6379/0")

    async def initialize(self):
        """Initialize Redis connection (compatible with aioredis 2.x)"""
        if not self.enabled:
            logger.info("✓ Cache layer disabled (VX11_CACHE_ENABLED=false)")
            return

        if not aioredis:
            logger.warning("⚠ aioredis not installed; cache disabled")
            self.enabled = False
            return

        try:
            # aioredis 2.x uses from_url; 1.x uses create_redis_pool
            if _AIOREDIS_V2:
                self.redis = await aioredis.from_url(self.redis_url, encoding="utf-8")
            else:
                self.redis = await aioredis.create_redis_pool(
                    self.redis_url,
                    encoding="utf-8",
                    minsize=5,
                    maxsize=10,
                )

            # Test connection
            pong = await self.redis.ping()
            if pong:
                logger.info(
                    f"✓ Redis cache connected: {self.redis_url} (aioredis v2.x)"
                )
            else:
                raise Exception("Redis ping failed")
        except Exception as e:
            logger.error(f"✗ Redis cache init failed: {e}")
            self.redis = None
            self.enabled = False

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            if _AIOREDIS_V2:
                await self.redis.close()
            else:
                self.redis.close()
                await self.redis.wait_closed()
            logger.info("✓ Redis cache closed")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (aioredis 2.x compatible)"""
        if not self.enabled or not self.redis:
            return None

        try:
            if _AIOREDIS_V2:
                value = await self.redis.get(key)
            else:
                value = await self.redis.get(key)

            if value:
                logger.debug(f"cache_hit: {key}")
                return json.loads(value)
            logger.debug(f"cache_miss: {key}")
            return None
        except Exception as e:
            logger.error(f"cache_get error ({key}): {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Set value in cache with TTL (aioredis 2.x compatible)"""
        if not self.enabled or not self.redis:
            return False

        try:
            serialized = json.dumps(value)
            if _AIOREDIS_V2:
                await self.redis.set(key, serialized, ex=ttl)
            else:
                await self.redis.setex(key, ttl, serialized)

            logger.debug(f"cache_set: {key} (ttl={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"cache_set error ({key}): {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from cache (aioredis 2.x compatible)"""
        if not self.enabled or not self.redis:
            return 0

        try:
            count = await self.redis.delete(*keys)
            logger.debug(f"cache_delete: {count} keys removed")
            return count
        except Exception as e:
            logger.error(f"cache_delete error: {e}")
            return 0

    async def clear(self) -> bool:
        """Clear all cache (use cautiously)"""
        if not self.enabled or not self.redis:
            return False

        try:
            await self.redis.flushdb()
            logger.info("cache_clear: All keys removed")
            return True
        except Exception as e:
            logger.error(f"cache_clear error: {e}")
            return False

    async def health_check(self) -> dict:
        """Check Redis health"""
        if not self.enabled:
            return {"status": "disabled", "reason": "VX11_CACHE_ENABLED=false"}

        if not self.redis:
            return {"status": "disconnected", "reason": "Redis pool not initialized"}

        try:
            pong = await self.redis.execute("ping")
            info = await self.redis.execute("info", "stats")
            return {
                "status": "healthy" if pong else "unhealthy",
                "response": pong,
                "info": info[:100] if info else None,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global cache instance
_cache_instance: Optional[CacheLayer] = None


def get_cache() -> CacheLayer:
    """Get or create cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheLayer()
    return _cache_instance


async def cache_startup():
    """Startup hook for FastAPI"""
    cache = get_cache()
    await cache.initialize()


async def cache_shutdown():
    """Shutdown hook for FastAPI"""
    cache = get_cache()
    await cache.close()
