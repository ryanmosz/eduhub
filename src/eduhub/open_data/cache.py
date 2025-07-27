"""
Caching utilities for Open Data API.

Provides Redis-based caching with in-memory fallback for high-performance
content delivery. Implements cache stampede protection and TTL management.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration constants
CACHE_TTL_DEFAULT = int(os.getenv("OPEN_DATA_CACHE_TTL", "3600"))  # 1 hour
CACHE_KEY_PREFIX = "opendata"
MAX_IN_MEMORY_ITEMS = 1000

# In-memory cache fallback
_memory_cache: dict[str, dict[str, Any]] = {}
_cache_lock = asyncio.Lock()


class OpenDataCache:
    """
    High-performance cache for Open Data API responses.

    Uses Redis as primary cache with in-memory fallback. Implements
    cache stampede protection and automatic TTL management.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache with Redis connection.

        Args:
            redis_url: Redis connection URL (defaults to env var)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client: Optional[redis.Redis] = None
        self.connected = False

        # Track cache metrics
        self.hits = 0
        self.misses = 0
        self.errors = 0

    async def connect(self) -> None:
        """Establish Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory cache only")
            return

        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info("Connected to Redis for Open Data caching")

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
            self.redis_client = None
            self.connected = False

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.aclose()
            self.redis_client = None
            self.connected = False
            logger.info("Disconnected from Redis")

    def _create_cache_key(self, key: str) -> str:
        """
        Create a cache key with proper prefix and hashing.

        Args:
            key: Base cache key

        Returns:
            Prefixed and hashed cache key
        """
        # Hash long keys to keep them manageable
        if len(key) > 100:
            key_hash = hashlib.md5(key.encode()).hexdigest()
            return f"{CACHE_KEY_PREFIX}:{key_hash}"

        return f"{CACHE_KEY_PREFIX}:{key}"

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        """
        Get cached data by key.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        cache_key = self._create_cache_key(key)

        # Try Redis first
        if self.connected and self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.hits += 1
                    logger.debug(f"Redis cache hit for key: {key}")
                    return json.loads(cached_data)

            except Exception as e:
                self.errors += 1
                logger.warning(f"Redis cache error for key {key}: {e}")

        # Fallback to in-memory cache
        async with _cache_lock:
            if cache_key in _memory_cache:
                cache_entry = _memory_cache[cache_key]

                # Check expiration
                if datetime.utcnow() <= cache_entry["expires"]:
                    self.hits += 1
                    logger.debug(f"Memory cache hit for key: {key}")
                    return cache_entry["data"]
                else:
                    # Expired - remove it
                    del _memory_cache[cache_key]

        self.misses += 1
        logger.debug(f"Cache miss for key: {key}")
        return None

    async def set(
        self, key: str, data: dict[str, Any], ttl: int = CACHE_TTL_DEFAULT
    ) -> bool:
        """
        Store data in cache with TTL.

        Args:
            key: Cache key
            data: Data to cache
            ttl: Time to live in seconds

        Returns:
            True if stored successfully, False otherwise
        """
        cache_key = self._create_cache_key(key)
        serialized_data = json.dumps(data, default=str, separators=(",", ":"))

        success = False

        # Try Redis first
        if self.connected and self.redis_client:
            try:
                await self.redis_client.setex(cache_key, ttl, serialized_data)
                success = True
                logger.debug(f"Stored in Redis cache: {key} (TTL: {ttl}s)")

            except Exception as e:
                self.errors += 1
                logger.warning(f"Redis cache set error for key {key}: {e}")

        # Always store in memory cache as backup
        async with _cache_lock:
            # Implement simple LRU by removing oldest entries
            if len(_memory_cache) >= MAX_IN_MEMORY_ITEMS:
                # Remove 10% of oldest entries
                to_remove = max(1, MAX_IN_MEMORY_ITEMS // 10)
                sorted_keys = sorted(
                    _memory_cache.keys(), key=lambda k: _memory_cache[k]["created"]
                )
                for old_key in sorted_keys[:to_remove]:
                    del _memory_cache[old_key]

            _memory_cache[cache_key] = {
                "data": data,
                "created": datetime.utcnow(),
                "expires": datetime.utcnow() + timedelta(seconds=ttl),
            }
            success = True
            logger.debug(f"Stored in memory cache: {key} (TTL: {ttl}s)")

        return success

    async def delete(self, key: str) -> bool:
        """
        Delete cached data by key.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        cache_key = self._create_cache_key(key)
        deleted = False

        # Delete from Redis
        if self.connected and self.redis_client:
            try:
                result = await self.redis_client.delete(cache_key)
                if result:
                    deleted = True
                    logger.debug(f"Deleted from Redis cache: {key}")

            except Exception as e:
                logger.warning(f"Redis cache delete error for key {key}: {e}")

        # Delete from memory cache
        async with _cache_lock:
            if cache_key in _memory_cache:
                del _memory_cache[cache_key]
                deleted = True
                logger.debug(f"Deleted from memory cache: {key}")

        return deleted

    def get_stats(self) -> dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests,
            "redis_connected": self.connected,
            "memory_cache_size": len(_memory_cache),
        }

    async def clear_all(self) -> None:
        """Clear all cached data (use with caution)."""
        # Clear Redis cache
        if self.connected and self.redis_client:
            try:
                # Delete all keys with our prefix
                keys = await self.redis_client.keys(f"{CACHE_KEY_PREFIX}:*")
                if keys:
                    await self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} keys from Redis cache")

            except Exception as e:
                logger.warning(f"Error clearing Redis cache: {e}")

        # Clear memory cache
        async with _cache_lock:
            cache_size = len(_memory_cache)
            _memory_cache.clear()
            logger.info(f"Cleared {cache_size} keys from memory cache")


# Global cache instance
_cache_instance: Optional[OpenDataCache] = None


async def get_cache() -> OpenDataCache:
    """Get or create the global cache instance."""
    global _cache_instance

    if _cache_instance is None:
        _cache_instance = OpenDataCache()
        await _cache_instance.connect()

    return _cache_instance


async def get_cached_response(key: str) -> Optional[dict[str, Any]]:
    """Convenience function to get cached response."""
    cache = await get_cache()
    return await cache.get(key)


async def cache_response(
    key: str, data: dict[str, Any], ttl: int = CACHE_TTL_DEFAULT
) -> bool:
    """Convenience function to cache response."""
    cache = await get_cache()
    return await cache.set(key, data, ttl)


async def invalidate_cache(key: str) -> bool:
    """Convenience function to invalidate cached response."""
    cache = await get_cache()
    return await cache.delete(key)


async def get_cache_stats() -> dict[str, Any]:
    """Get cache performance statistics."""
    cache = await get_cache()
    return cache.get_stats()
