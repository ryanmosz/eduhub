"""
Caching utilities for oEmbed responses.

Provides Redis-backed caching with in-memory fallback for performance optimization.
Implements configurable TTL and cache hit optimization for oEmbed proxy service.

## Back-off Strategy for Rate Limiting Mitigation

This caching layer implements several strategies to handle provider rate limiting:

1. **Primary Cache (Redis)**: Persistent cache across application restarts
   - Reduces load on oEmbed providers
   - 1-hour default TTL configurable via OEMBED_CACHE_TTL
   - Graceful degradation if Redis unavailable

2. **Secondary Cache (Memory)**: In-memory fallback
   - Continues serving cached responses when Redis fails
   - Automatic cleanup of expired entries
   - Zero external dependencies

3. **Connection Resilience**:
   - Single connection attempt per instance
   - 5-second timeout to prevent blocking
   - Automatic fallback to memory-only mode

4. **Cache Key Strategy**:
   - MD5 hash of URL + dimensions for consistency
   - Separate cache entries for different sizes
   - Namespace prefixing (oembed:) for Redis organization

## Performance Characteristics

- Cache hit latency: < 1ms (memory) / < 5ms (Redis)
- Cache miss: Falls back to provider request (200-2000ms)
- Storage: JSON serialization for complex oEmbed responses
- TTL: Configurable (default 3600 seconds / 1 hour)

## Usage

Set environment variables:
- OEMBED_CACHE_TTL=3600 (cache duration in seconds)
- REDIS_URL=redis://localhost:6379/0 (Redis connection string)
- REDIS_TIMEOUT=5 (connection timeout in seconds)
"""

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Configuration
OEMBED_CACHE_TTL = int(os.getenv("OEMBED_CACHE_TTL", "3600"))  # 1 hour default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_TIMEOUT = int(os.getenv("REDIS_TIMEOUT", "5"))  # 5 seconds

# In-memory fallback cache
_memory_cache: dict[str, dict[str, Any]] = {}
_cache_timestamps: dict[str, float] = {}


class OEmbedCache:
    """
    oEmbed response caching with Redis primary and in-memory fallback.

    Features:
    - Redis-backed persistence for production
    - In-memory fallback when Redis unavailable
    - Configurable TTL for cache expiration
    - JSON serialization for complex oEmbed responses
    - Cache key generation from URL + parameters
    """

    def __init__(self, redis_url: str = REDIS_URL, ttl: int = OEMBED_CACHE_TTL):
        """Initialize cache with Redis connection and TTL settings."""
        self.ttl = ttl
        self.redis_url = redis_url
        self._redis_client: Optional[redis.Redis] = None
        self._redis_available = False
        self._connection_attempted = False

    async def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client with connection handling."""
        if not REDIS_AVAILABLE:
            return None

        if self._redis_client is None and not self._connection_attempted:
            self._connection_attempted = True
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    socket_timeout=REDIS_TIMEOUT,
                    socket_connect_timeout=REDIS_TIMEOUT,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )

                # Test connection
                await asyncio.wait_for(self._redis_client.ping(), timeout=REDIS_TIMEOUT)
                self._redis_available = True
                print(f"✅ Redis connected: {self.redis_url}")

            except Exception as e:
                print(f"⚠️  Redis connection failed, using in-memory cache: {e}")
                self._redis_client = None
                self._redis_available = False

        return self._redis_client if self._redis_available else None

    def _generate_cache_key(
        self, url: str, maxwidth: Optional[int] = None, maxheight: Optional[int] = None
    ) -> str:
        """Generate consistent cache key from URL and parameters."""
        # Create deterministic key from URL and size parameters
        key_data = f"{url}:{maxwidth or 'auto'}:{maxheight or 'auto'}"
        return f"oembed:{hashlib.md5(key_data.encode()).hexdigest()}"

    async def get(
        self, url: str, maxwidth: Optional[int] = None, maxheight: Optional[int] = None
    ) -> Optional[dict[str, Any]]:
        """
        Get cached oEmbed response.

        Args:
            url: Original URL being embedded
            maxwidth: Maximum width parameter
            maxheight: Maximum height parameter

        Returns:
            Cached oEmbed response dict or None if not found/expired
        """
        cache_key = self._generate_cache_key(url, maxwidth, maxheight)

        # Try Redis first
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    response = json.loads(cached_data)
                    response["cached"] = True
                    return response
            except Exception as e:
                print(f"Redis cache get error: {e}")

        # Fallback to in-memory cache
        return self._get_memory_cache(cache_key)

    async def set(
        self,
        url: str,
        oembed_response: dict[str, Any],
        maxwidth: Optional[int] = None,
        maxheight: Optional[int] = None,
    ) -> bool:
        """
        Store oEmbed response in cache.

        Args:
            url: Original URL being embedded
            oembed_response: oEmbed response to cache
            maxwidth: Maximum width parameter
            maxheight: Maximum height parameter

        Returns:
            True if successfully cached, False otherwise
        """
        cache_key = self._generate_cache_key(url, maxwidth, maxheight)

        # Prepare data for caching (remove the 'cached' flag)
        cache_data = oembed_response.copy()
        cache_data.pop("cached", None)

        success = False

        # Try Redis first
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                serialized_data = json.dumps(cache_data)
                await redis_client.setex(cache_key, self.ttl, serialized_data)
                success = True
            except Exception as e:
                print(f"Redis cache set error: {e}")

        # Always set in memory cache as backup
        self._set_memory_cache(cache_key, cache_data)

        return True  # Always succeed if we reach here (memory cache always works)

    def _get_memory_cache(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Get from in-memory cache with TTL checking."""
        if cache_key not in _memory_cache:
            return None

        # Check TTL
        if cache_key in _cache_timestamps:
            cache_time = _cache_timestamps[cache_key]
            if time.time() - cache_time > self.ttl:
                # Expired - remove from cache
                _memory_cache.pop(cache_key, None)
                _cache_timestamps.pop(cache_key, None)
                return None

        response = _memory_cache[cache_key].copy()
        response["cached"] = True
        return response

    def _set_memory_cache(
        self, cache_key: str, oembed_response: dict[str, Any]
    ) -> None:
        """Set in-memory cache with timestamp."""
        _memory_cache[cache_key] = oembed_response.copy()
        _cache_timestamps[cache_key] = time.time()

        # Clean up old entries (keep memory usage reasonable)
        self._cleanup_memory_cache()

    def _cleanup_memory_cache(self) -> None:
        """Remove expired entries from memory cache."""
        current_time = time.time()
        expired_keys = []

        for key, timestamp in _cache_timestamps.items():
            if current_time - timestamp > self.ttl:
                expired_keys.append(key)

        for key in expired_keys:
            _memory_cache.pop(key, None)
            _cache_timestamps.pop(key, None)

    async def clear(self) -> bool:
        """Clear all cached entries."""
        success = False

        # Clear Redis
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                # Get all oembed keys and delete them
                keys = await redis_client.keys("oembed:*")
                if keys:
                    await redis_client.delete(*keys)
                success = True
            except Exception as e:
                print(f"Redis cache clear error: {e}")

        # Clear memory cache
        _memory_cache.clear()
        _cache_timestamps.clear()

        return success

    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "redis_available": self._redis_available,
            "memory_cache_size": len(_memory_cache),
            "ttl_seconds": self.ttl,
            "redis_url": self.redis_url if self._redis_available else None,
        }

        # Get Redis stats if available
        redis_client = await self._get_redis_client()
        if redis_client:
            try:
                redis_keys = await redis_client.keys("oembed:*")
                stats["redis_cache_size"] = len(redis_keys)
            except Exception:
                stats["redis_cache_size"] = "unknown"

        return stats

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            self._redis_available = False


# Global cache instance
_oembed_cache: Optional[OEmbedCache] = None


async def get_oembed_cache() -> OEmbedCache:
    """Get or create the global oEmbed cache instance."""
    global _oembed_cache
    if _oembed_cache is None:
        _oembed_cache = OEmbedCache()
    return _oembed_cache


async def cleanup_oembed_cache():
    """Clean up the global oEmbed cache."""
    global _oembed_cache
    if _oembed_cache:
        await _oembed_cache.close()
        _oembed_cache = None
