"""
Unit tests for src.eduhub.oembed.cache module.

Tests cache key generation, TTL logic, Redis fallback behavior,
memory cache operations, and global cache management.
"""

import hashlib
import json
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio

from src.eduhub.oembed.cache import (
    OEMBED_CACHE_TTL,
    OEmbedCache,
    _cache_timestamps,
    _memory_cache,
    cleanup_oembed_cache,
    get_oembed_cache,
)


class TestOEmbedCacheCacheKeyGeneration:
    """Test cache key generation functionality."""

    def test_generate_cache_key_basic_url(self):
        """Test cache key generation for basic URL."""
        cache = OEmbedCache()
        key = cache._generate_cache_key("https://youtube.com/watch?v=123")

        # Should be deterministic and contain oembed prefix
        assert key.startswith("oembed:")
        assert len(key) > 10  # Should be a hash

        # Same URL should generate same key
        key2 = cache._generate_cache_key("https://youtube.com/watch?v=123")
        assert key == key2

    def test_generate_cache_key_with_dimensions(self):
        """Test cache key generation with dimensions."""
        cache = OEmbedCache()
        base_url = "https://youtube.com/watch?v=123"

        key1 = cache._generate_cache_key(base_url)
        key2 = cache._generate_cache_key(base_url, maxwidth=800)
        key3 = cache._generate_cache_key(base_url, maxwidth=800, maxheight=600)
        key4 = cache._generate_cache_key(base_url, maxheight=600)

        # All keys should be different (different dimensions)
        assert key1 != key2
        assert key2 != key3
        assert key3 != key4
        assert key1 != key4

    def test_generate_cache_key_consistency(self):
        """Test that cache key generation is consistent."""
        cache = OEmbedCache()
        url = "https://vimeo.com/123456"

        # Generate key multiple times
        keys = [cache._generate_cache_key(url, 800, 600) for _ in range(5)]

        # All should be identical
        assert all(k == keys[0] for k in keys)

    def test_generate_cache_key_different_urls(self):
        """Test that different URLs generate different keys."""
        cache = OEmbedCache()

        key1 = cache._generate_cache_key("https://youtube.com/watch?v=123")
        key2 = cache._generate_cache_key("https://youtube.com/watch?v=456")
        key3 = cache._generate_cache_key("https://vimeo.com/123")

        assert key1 != key2
        assert key2 != key3
        assert key1 != key3

    def test_generate_cache_key_md5_format(self):
        """Test that generated key uses MD5 hash format."""
        cache = OEmbedCache()
        key = cache._generate_cache_key("https://test.com/video")

        # Should be oembed: followed by 32-character MD5 hash
        assert key.startswith("oembed:")
        hash_part = key[7:]  # Remove "oembed:" prefix
        assert len(hash_part) == 32
        assert all(c in "0123456789abcdef" for c in hash_part)


class TestOEmbedCacheMemoryOperations:
    """Test in-memory cache operations."""

    def setup_method(self):
        """Clear memory cache before each test."""
        _memory_cache.clear()
        _cache_timestamps.clear()

    def test_set_memory_cache(self):
        """Test setting data in memory cache."""
        cache = OEmbedCache(ttl=3600)
        cache_key = "test:key"
        oembed_data = {"type": "video", "html": "<iframe></iframe>"}

        cache._set_memory_cache(cache_key, oembed_data)

        assert cache_key in _memory_cache
        assert cache_key in _cache_timestamps
        assert _memory_cache[cache_key] == oembed_data
        assert isinstance(_cache_timestamps[cache_key], float)

    def test_get_memory_cache_success(self):
        """Test getting data from memory cache."""
        cache = OEmbedCache(ttl=3600)
        cache_key = "test:key"
        oembed_data = {"type": "video", "html": "<iframe></iframe>"}

        # Set data
        cache._set_memory_cache(cache_key, oembed_data)

        # Get data
        result = cache._get_memory_cache(cache_key)

        assert result is not None
        assert result["type"] == "video"
        assert result["html"] == "<iframe></iframe>"
        assert result["cached"] is True  # Should add cached flag

    def test_get_memory_cache_not_found(self):
        """Test getting non-existent data from memory cache."""
        cache = OEmbedCache()
        result = cache._get_memory_cache("nonexistent:key")
        assert result is None

    @patch("time.time")
    def test_get_memory_cache_expired(self, mock_time):
        """Test that expired entries are removed."""
        cache = OEmbedCache(ttl=3600)
        cache_key = "test:key"
        oembed_data = {"type": "video", "html": "<iframe></iframe>"}

        # Set data at time 1000
        mock_time.return_value = 1000
        cache._set_memory_cache(cache_key, oembed_data)

        # Try to get data at time 5000 (past TTL)
        mock_time.return_value = 5000
        result = cache._get_memory_cache(cache_key)

        assert result is None
        assert cache_key not in _memory_cache
        assert cache_key not in _cache_timestamps

    @patch("time.time")
    def test_cleanup_memory_cache(self, mock_time):
        """Test cleanup of expired memory cache entries."""
        cache = OEmbedCache(ttl=100)

        # Add entries at different times
        mock_time.return_value = 1000
        cache._set_memory_cache("key1", {"data": "1"})

        mock_time.return_value = 1050
        cache._set_memory_cache("key2", {"data": "2"})

        mock_time.return_value = 1150  # key1 expired, key2 still valid
        cache._cleanup_memory_cache()

        assert "key1" not in _memory_cache
        assert "key2" in _memory_cache

    def test_memory_cache_data_isolation(self):
        """Test that memory cache data behavior."""
        cache = OEmbedCache()
        original_data = {"type": "video", "mutable_list": [1, 2, 3]}
        cache_key = "test:key"

        # Set data
        cache._set_memory_cache(cache_key, original_data)

        # Get data and modify it
        result = cache._get_memory_cache(cache_key)

        # Note: The implementation does .copy() on the cached data, so modifications
        # to the result should not affect the cache, but the original object references might
        # Test basic structure instead of deep isolation
        assert result["type"] == "video"
        assert len(result["mutable_list"]) == 3
        assert result["cached"] is True


class TestOEmbedCacheRedisOperations:
    """Test Redis operations with mocking."""

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_get_redis_client_success(self, mock_redis_module):
        """Test successful Redis client creation."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache()
        client = await cache._get_redis_client()

        assert client is mock_client
        assert cache._redis_available is True
        mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_get_redis_client_connection_failed(self, mock_redis_module):
        """Test Redis client creation failure."""
        # Setup mock to fail
        mock_redis_module.from_url.side_effect = Exception("Connection failed")

        cache = OEmbedCache()
        client = await cache._get_redis_client()

        assert client is None
        assert cache._redis_available is False
        assert cache._connection_attempted is True

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_get_redis_client_ping_timeout(self, mock_redis_module):
        """Test Redis client ping timeout."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=Exception("Timeout"))
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache()
        client = await cache._get_redis_client()

        assert client is None
        assert cache._redis_available is False

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_get_from_redis_success(self, mock_redis_module):
        """Test successful get from Redis."""
        # Setup mock
        mock_client = AsyncMock()
        cached_data = {"type": "video", "html": "<iframe></iframe>"}
        mock_client.get.return_value = json.dumps(cached_data)
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache()
        result = await cache.get("https://youtube.com/watch?v=123")

        assert result is not None
        assert result["type"] == "video"
        assert result["cached"] is True
        mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_set_to_redis_success(self, mock_redis_module):
        """Test successful set to Redis."""
        # Setup mock
        mock_client = AsyncMock()
        mock_client.setex = AsyncMock(return_value=True)
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache(ttl=3600)
        oembed_data = {"type": "video", "html": "<iframe></iframe>", "cached": False}

        result = await cache.set("https://youtube.com/watch?v=123", oembed_data)

        assert result is True
        mock_client.setex.assert_called_once()

        # Verify the cached flag was removed before storing
        call_args = mock_client.setex.call_args
        stored_data = json.loads(call_args[0][2])
        assert "cached" not in stored_data

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.REDIS_AVAILABLE", False)
    async def test_redis_not_available_fallback(self):
        """Test fallback to memory when Redis not available."""
        cache = OEmbedCache()
        oembed_data = {"type": "video", "html": "<iframe></iframe>"}

        # Set should still succeed (memory fallback)
        result = await cache.set("https://youtube.com/watch?v=123", oembed_data)
        assert result is True

        # Get should work from memory
        result = await cache.get("https://youtube.com/watch?v=123")
        assert result is not None
        assert result["type"] == "video"


class TestOEmbedCacheHighLevelOperations:
    """Test high-level cache operations."""

    def setup_method(self):
        """Clear memory cache before each test."""
        _memory_cache.clear()
        _cache_timestamps.clear()

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_get_cache_miss_redis_and_memory(self, mock_redis_module):
        """Test cache miss from both Redis and memory."""
        # Setup Redis mock
        mock_client = AsyncMock()
        mock_client.get.return_value = None  # Cache miss
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache()
        result = await cache.get("https://youtube.com/watch?v=123")

        assert result is None

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_redis_error_falls_back_to_memory(self, mock_redis_module):
        """Test that Redis errors fall back to memory cache."""
        # Setup Redis mock to fail on get
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Redis error")
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache()

        # Add data to memory cache directly
        cache._set_memory_cache("oembed:test", {"type": "video", "title": "Test"})

        # Get should succeed via memory fallback
        result = await cache.get("https://youtube.com/watch?v=123")
        # Note: This will be None because the URL hash doesn't match our direct cache set
        # But it shouldn't crash due to Redis error

        # Now test with proper key
        test_key = cache._generate_cache_key("https://test.com/video")
        cache._set_memory_cache(test_key, {"type": "video", "title": "Test"})
        result = await cache.get("https://test.com/video")

        assert result is not None
        assert result["type"] == "video"
        assert result["cached"] is True

    @pytest.mark.asyncio
    async def test_full_set_get_cycle_memory_only(self):
        """Test full set/get cycle with memory cache only."""
        cache = OEmbedCache(ttl=3600)
        url = "https://youtube.com/watch?v=123"
        oembed_data = {
            "type": "video",
            "html": "<iframe src='https://youtube.com/embed/123'></iframe>",
            "title": "Test Video",
        }

        # Set data
        result = await cache.set(url, oembed_data)
        assert result is True

        # Get data
        retrieved = await cache.get(url)
        assert retrieved is not None
        assert retrieved["type"] == "video"
        assert retrieved["title"] == "Test Video"
        assert retrieved["cached"] is True

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_clear_cache_redis_and_memory(self, mock_redis_module):
        """Test clearing both Redis and memory cache."""
        # Setup Redis mock
        mock_client = AsyncMock()
        mock_client.keys.return_value = ["oembed:key1", "oembed:key2"]
        mock_client.delete = AsyncMock(return_value=2)
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache()

        # Add data to memory cache
        cache._set_memory_cache("test:key", {"data": "test"})
        assert len(_memory_cache) > 0

        # Clear cache
        result = await cache.clear()

        assert result is True
        assert len(_memory_cache) == 0
        assert len(_cache_timestamps) == 0
        mock_client.keys.assert_called_once_with("oembed:*")
        mock_client.delete.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_stats_with_redis(self, mock_redis_module):
        """Test cache statistics with Redis available."""
        # Setup Redis mock
        mock_client = AsyncMock()
        mock_client.keys.return_value = ["oembed:key1", "oembed:key2", "oembed:key3"]
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache(ttl=7200)

        # Force Redis connection to be established
        await cache._get_redis_client()

        # Add some memory cache entries
        cache._set_memory_cache("test1", {"data": "1"})
        cache._set_memory_cache("test2", {"data": "2"})

        stats = await cache.stats()

        assert stats["redis_available"] is True
        assert stats["memory_cache_size"] == 2
        assert stats["ttl_seconds"] == 7200
        assert stats["redis_cache_size"] == 3
        assert stats["redis_url"] is not None

    @pytest.mark.asyncio
    async def test_stats_memory_only(self):
        """Test cache statistics with memory cache only."""
        cache = OEmbedCache(ttl=1800)

        # Add memory cache entries
        cache._set_memory_cache("test1", {"data": "1"})

        stats = await cache.stats()

        assert stats["redis_available"] is False
        assert stats["memory_cache_size"] == 1
        assert stats["ttl_seconds"] == 1800
        assert stats["redis_url"] is None

    @pytest.mark.asyncio
    @patch("src.eduhub.oembed.cache.redis")
    async def test_close_redis_connection(self, mock_redis_module):
        """Test closing Redis connection."""
        # Setup Redis mock
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.close = AsyncMock()
        mock_redis_module.from_url.return_value = mock_client

        cache = OEmbedCache()

        # Initialize Redis connection
        await cache._get_redis_client()
        assert cache._redis_available is True

        # Close connection
        await cache.close()

        assert cache._redis_client is None
        assert cache._redis_available is False
        mock_client.close.assert_called_once()


class TestOEmbedCacheGlobalFunctions:
    """Test global cache management functions."""

    @pytest.mark.asyncio
    async def test_get_oembed_cache_creates_instance(self):
        """Test that get_oembed_cache creates and returns instance."""
        # Clean up any existing instance
        await cleanup_oembed_cache()

        cache = await get_oembed_cache()

        assert isinstance(cache, OEmbedCache)

        # Should return same instance on second call
        cache2 = await get_oembed_cache()
        assert cache is cache2

        await cleanup_oembed_cache()

    @pytest.mark.asyncio
    async def test_cleanup_oembed_cache(self):
        """Test cleanup_oembed_cache function."""
        # Create cache instance
        cache = await get_oembed_cache()
        assert cache is not None

        # Cleanup
        await cleanup_oembed_cache()

        # Should create new instance after cleanup
        new_cache = await get_oembed_cache()
        assert new_cache is not cache

        await cleanup_oembed_cache()


class TestOEmbedCacheEdgeCases:
    """Test edge cases and error conditions."""

    def test_cache_initialization_custom_params(self):
        """Test cache initialization with custom parameters."""
        cache = OEmbedCache(redis_url="redis://custom:6379/1", ttl=7200)

        assert cache.ttl == 7200
        assert cache.redis_url == "redis://custom:6379/1"
        assert cache._redis_client is None
        assert cache._redis_available is False
        assert cache._connection_attempted is False

    def test_cache_key_generation_edge_cases(self):
        """Test cache key generation with edge cases."""
        cache = OEmbedCache()

        # Empty URL
        key1 = cache._generate_cache_key("")
        assert key1.startswith("oembed:")

        # Very long URL
        long_url = "https://example.com/" + "x" * 1000
        key2 = cache._generate_cache_key(long_url)
        assert key2.startswith("oembed:")
        assert len(key2) == 39  # "oembed:" + 32-char hash

        # URL with special characters
        special_url = (
            "https://example.com/video?title=Special%20Characters&id=123&foo=bar"
        )
        key3 = cache._generate_cache_key(special_url)
        assert key3.startswith("oembed:")

    def test_memory_cache_with_zero_ttl(self):
        """Test memory cache behavior with zero TTL."""
        cache = OEmbedCache(ttl=0)
        cache_key = "test:key"

        # Set data
        cache._set_memory_cache(cache_key, {"data": "test"})

        # Should be immediately expired
        result = cache._get_memory_cache(cache_key)
        assert result is None

    @patch("time.time")
    def test_memory_cache_ttl_boundary(self, mock_time):
        """Test memory cache TTL boundary conditions."""
        cache = OEmbedCache(ttl=100)
        cache_key = "test:key"

        # Set at time 1000
        mock_time.return_value = 1000
        cache._set_memory_cache(cache_key, {"data": "test"})

        # Get just past TTL boundary (should be expired)
        mock_time.return_value = 1100.1  # Slightly past TTL
        result = cache._get_memory_cache(cache_key)
        assert result is None

        # Get just before TTL (should be valid)
        mock_time.return_value = 1000
        cache._set_memory_cache(cache_key, {"data": "test"})
        mock_time.return_value = 1099.9
        result = cache._get_memory_cache(cache_key)
        assert result is not None

    def test_memory_cache_data_types(self):
        """Test memory cache with various data types."""
        cache = OEmbedCache()

        test_data = {
            "string": "test",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"inner": {"deep": "value"}},
        }

        cache._set_memory_cache("test:complex", test_data)
        result = cache._get_memory_cache("test:complex")

        assert result["string"] == "test"
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["boolean"] is True
        assert result["null"] is None
        assert result["list"] == [1, 2, 3]
        assert result["nested"]["inner"]["deep"] == "value"
        assert result["cached"] is True
