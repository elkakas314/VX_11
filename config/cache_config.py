"""
Cache Configuration & Patterns
==============================
Centralized cache patterns and TTL configuration for VX11 endpoints.
"""

# Cache key patterns and their TTL (seconds)
CACHE_PATTERNS = {
    # Health endpoints (fast-changing, frequent access)
    "shub:health": {
        "ttl": 60,
        "description": "Shubniggurath audio engine health check",
        "invalidate_on": ["shub_restart", "config_change"],
    },
    "shub:ready": {
        "ttl": 60,
        "description": "Shubniggurath readiness probe",
        "invalidate_on": ["shub_restart", "config_change"],
    },
    # API endpoints (moderate-changing)
    "shub:openapi": {
        "ttl": 300,  # 5 minutes
        "description": "Shubniggurath OpenAPI schema",
        "invalidate_on": ["shub_deploy", "version_upgrade"],
    },
    # Config endpoints (slow-changing)
    "shub:config": {
        "ttl": 3600,  # 1 hour
        "description": "Shubniggurath configuration",
        "invalidate_on": ["config_change"],
    },
}

# Cache groups for bulk operations
CACHE_GROUPS = {
    "health": ["shub:health", "shub:ready"],  # All health checks
    "api": ["shub:openapi", "shub:config"],  # All API metadata
    "all": list(CACHE_PATTERNS.keys()),  # All cached items
}

# Invalidation strategies
INVALIDATION_STRATEGIES = {
    "shub_restart": ["health", "api"],  # Restart invalidates all
    "config_change": ["health", "config"],  # Config change invalidates health + config
    "version_upgrade": ["api", "health"],  # Upgrade invalidates all
}

# Cache metrics thresholds
CACHE_THRESHOLDS = {
    "hit_rate_target": 0.85,  # 85% target hit rate
    "low_hit_rate_alert": 0.5,  # Alert if < 50%
    "high_miss_rate_alert": 0.4,  # Alert if > 40%
}


def get_ttl(key: str) -> int:
    """Get TTL for a cache key"""
    if key in CACHE_PATTERNS:
        return CACHE_PATTERNS[key]["ttl"]
    return 60  # Default 60 seconds


def get_invalidation_group(event: str) -> list:
    """Get cache keys to invalidate for an event"""
    strategy = INVALIDATION_STRATEGIES.get(event, [])
    keys = []
    for group in strategy:
        keys.extend(CACHE_GROUPS.get(group, []))
    return list(set(keys))  # Remove duplicates


def cache_decorator(key: str, ttl: int = None):
    """
    Decorator for caching async functions

    Usage:
        @cache_decorator("shub:health", ttl=60)
        async def get_shub_health():
            return await proxy_shub_health()
    """
    from functools import wraps
    from config.cache import get_cache

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()
            cache_ttl = ttl or get_ttl(key)

            # Try cache first
            cached = await cache.get(key)
            if cached:
                return cached

            # Cache miss: call function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(key, result, ttl=cache_ttl)

            return result

        return wrapper

    return decorator
