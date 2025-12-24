"""
VX11 Rate Limiting Layer
=========================
Token bucket rate limiting for gateway endpoints.
Protects against abuse and ensures fair resource distribution.

Strategies:
- Per-user (token-based): 1000 req/min default
- Per-IP: 5000 req/min default
- Protected endpoints: 100 req/min slowdown (strategic)
"""

import logging
import os
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter with Redis backend"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.enabled = os.getenv("VX11_RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.default_limit = int(os.getenv("VX11_RATE_LIMIT_DEFAULT", "5000"))
        self.user_limit = int(os.getenv("VX11_RATE_LIMIT_USER", "1000"))
        self.protected_limit = int(os.getenv("VX11_RATE_LIMIT_PROTECTED", "100"))

    async def check_limit(
        self,
        identifier: str,
        limit: int = None,
        window: int = 60,
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Key (e.g., "user:token123", "ip:192.168.1.1")
            limit: Request limit per window (default: self.default_limit)
            window: Time window in seconds (default: 60)

        Returns:
            (is_allowed, info_dict)
            info_dict contains: remaining, limit, reset_at, retry_after
        """
        if not self.enabled or not self.redis:
            return True, {
                "remaining": limit or self.default_limit,
                "limit": limit or self.default_limit,
                "rate_limit_enabled": False,
            }

        if limit is None:
            limit = self.default_limit

        try:
            key = f"rate_limit:{identifier}"
            now = time.time()

            # Get current count + TTL
            count = await self.redis.get(key)
            ttl = await self.redis.ttl(key)

            if count is None:
                # First request in window
                await self.redis.setex(key, window, 1)
                return True, {
                    "remaining": limit - 1,
                    "limit": limit,
                    "reset_at": now + window,
                    "retry_after": None,
                }

            count = int(count)

            if count < limit:
                # Increment counter
                new_count = await self.redis.incr(key)
                reset_at = now + (ttl if ttl > 0 else window)
                return True, {
                    "remaining": limit - new_count,
                    "limit": limit,
                    "reset_at": reset_at,
                    "retry_after": None,
                }
            else:
                # Rate limit exceeded
                reset_at = now + (ttl if ttl > 0 else window)
                retry_after = max(1, ttl if ttl > 0 else window)
                return False, {
                    "remaining": 0,
                    "limit": limit,
                    "reset_at": reset_at,
                    "retry_after": retry_after,
                }

        except Exception as e:
            logger.error(f"rate_limit check error ({identifier}): {e}")
            # Fail open: allow request on error
            return True, {"error": str(e), "rate_limit_enabled": False}

    async def get_status(self, identifier: str) -> dict:
        """Get current rate limit status for identifier"""
        if not self.redis:
            return {"enabled": False}

        try:
            key = f"rate_limit:{identifier}"
            count = await self.redis.get(key)
            ttl = await self.redis.ttl(key)
            return {
                "identifier": identifier,
                "requests_in_window": int(count) if count else 0,
                "ttl_seconds": ttl if ttl > 0 else 0,
            }
        except Exception as e:
            logger.error(f"get_status error: {e}")
            return {"error": str(e)}

    async def reset(self, identifier: str) -> bool:
        """Reset rate limit for identifier (admin only)"""
        if not self.redis:
            return False

        try:
            key = f"rate_limit:{identifier}"
            await self.redis.delete(key)
            logger.info(f"rate_limit reset: {identifier}")
            return True
        except Exception as e:
            logger.error(f"reset error: {e}")
            return False

    async def health_check(self) -> dict:
        """Check rate limiter health"""
        if not self.enabled:
            return {"status": "disabled", "reason": "VX11_RATE_LIMIT_ENABLED=false"}

        if not self.redis:
            return {"status": "disconnected", "reason": "Redis not initialized"}

        try:
            test_key = "rate_limit:health_check"
            await self.redis.setex(test_key, 10, 1)
            value = await self.redis.get(test_key)
            if value:
                await self.redis.delete(test_key)
                return {"status": "healthy"}
            return {"status": "unhealthy", "reason": "Set/get test failed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global rate limiter instance
_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = RateLimiter()
    return _limiter_instance


def set_redis_for_limiter(redis_client):
    """Set Redis client for rate limiter"""
    limiter = get_rate_limiter()
    limiter.redis = redis_client
