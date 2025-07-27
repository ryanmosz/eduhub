"""
Tests for oEmbed caching functionality.

Tests Tasks 5.2.4 and 5.2.5:
- Verify cache hit avoids outbound HTTP (respx assertion)
- Benchmark cache-hit path completes < 10ms
"""

import asyncio
import os
import sys
import time

import httpx
import pytest
import respx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.eduhub.oembed.cache import OEmbedCache, cleanup_oembed_cache, get_oembed_cache
from src.eduhub.oembed.client import OEmbedClient

# Mock oEmbed response
MOCK_YOUTUBE_RESPONSE = {
    "type": "video",
    "version": "1.0",
    "title": "Test Video",
    "provider_name": "YouTube",
    "html": '<iframe width="800" height="450" src="https://www.youtube.com/embed/test" frameborder="0"></iframe>',
    "width": 800,
    "height": 450,
}


class TestOEmbedCaching:
    """Test oEmbed caching functionality."""

    @pytest.fixture
    async def cache(self):
        """Create cache instance for testing."""
        cache = OEmbedCache(ttl=3600)  # 1 hour TTL
        yield cache
        await cache.close()

    @pytest.fixture
    async def oembed_client(self):
        """Create oEmbed client for testing."""
        client = OEmbedClient(timeout=5.0)
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_cache_get_set_basic(self, cache):
        """Test basic cache get/set functionality."""
        url = "https://youtube.com/watch?v=test"

        # Initially empty
        result = await cache.get(url, 800, 450)
        assert result is None

        # Set cache
        success = await cache.set(url, MOCK_YOUTUBE_RESPONSE, 800, 450)
        assert success  # Should succeed with memory cache

        # Get from cache
        cached_result = await cache.get(url, 800, 450)
        assert cached_result is not None
        assert cached_result["title"] == "Test Video"
        assert cached_result["cached"] == True  # Cache flag should be set

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, cache):
        """Test cache key generation with different parameters."""
        url = "https://youtube.com/watch?v=test"

        # Set cache with specific dimensions
        await cache.set(url, MOCK_YOUTUBE_RESPONSE, 800, 450)

        # Same URL and dimensions should hit cache
        result1 = await cache.get(url, 800, 450)
        assert result1 is not None
        assert result1["cached"] == True

        # Different dimensions should miss cache
        result2 = await cache.get(url, 1200, 600)
        assert result2 is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_5_2_4_cache_hit_avoids_outbound_http(self, oembed_client):
        """
        Task 5.2.4: TEST (pytest-asyncio + respx):
        verify cache hit avoids outbound HTTP (respx assertion)
        """
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"

        # Mock the YouTube oEmbed endpoint
        youtube_mock = respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_RESPONSE)
        )

        # First call - should hit the mock (cache miss)
        result1 = await oembed_client.fetch_embed(url, 800, 450)
        assert result1["title"] == "Test Video"
        assert result1["cached"] == False  # Fresh from provider
        assert youtube_mock.called  # Verify HTTP call was made
        assert youtube_mock.call_count == 1

        # Second call - should hit cache (no HTTP call)
        result2 = await oembed_client.fetch_embed(url, 800, 450)
        assert result2["title"] == "Test Video"
        assert result2["cached"] == True  # From cache
        assert youtube_mock.call_count == 1  # No additional HTTP calls

        # Third call - should still hit cache
        result3 = await oembed_client.fetch_embed(url, 800, 450)
        assert result3["cached"] == True
        assert youtube_mock.call_count == 1  # Still no additional calls

        print(
            "✅ Task 5.2.4: Cache hit avoids outbound HTTP - verified with respx assertions"
        )

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_5_2_5_cache_hit_performance_benchmark(
        self, oembed_client, benchmark
    ):
        """
        Task 5.2.5: TEST (benchmark):
        cache-hit path completes < 10 ms (pytest-benchmark)
        """
        url = "https://youtube.com/watch?v=benchmark_test"

        # Mock the YouTube oEmbed endpoint
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_RESPONSE)
        )

        # Populate cache with first call
        await oembed_client.fetch_embed(url, 800, 450)

        # Benchmark the cache hit performance
        async def cached_fetch():
            return await oembed_client.fetch_embed(url, 800, 450)

        # Run benchmark
        result = benchmark(cached_fetch)

        # Verify the result is cached
        assert result["cached"] == True
        assert result["title"] == "Test Video"

        # The benchmark stats will be displayed by pytest-benchmark
        # We can also check manually that it's under 10ms
        start_time = time.time()
        await oembed_client.fetch_embed(url, 800, 450)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 10.0, f"Cache hit took {elapsed_ms:.2f}ms, should be < 10ms"
        print(f"✅ Task 5.2.5: Cache hit completed in {elapsed_ms:.2f}ms (< 10ms)")

    @pytest.mark.asyncio
    async def test_cache_stats_functionality(self):
        """Test cache statistics endpoint functionality."""
        cache = await get_oembed_cache()

        # Get initial stats
        stats = await cache.stats()
        initial_size = stats["memory_cache_size"]

        # Add an entry
        await cache.set("https://test.com/video", MOCK_YOUTUBE_RESPONSE)

        # Check stats again
        stats_after = await cache.stats()
        assert stats_after["memory_cache_size"] == initial_size + 1
        assert stats_after["ttl_seconds"] == 3600  # Default TTL
        assert "cache_type" in str(
            stats_after
        )  # Should be memory_only or redis_with_memory_fallback

    @pytest.mark.asyncio
    async def test_cache_clear_functionality(self, cache):
        """Test cache clearing functionality."""
        # Add some entries
        await cache.set("https://test1.com/video", MOCK_YOUTUBE_RESPONSE)
        await cache.set("https://test2.com/video", MOCK_YOUTUBE_RESPONSE)

        # Verify entries exist
        stats = await cache.stats()
        assert stats["memory_cache_size"] >= 2

        # Clear cache
        success = await cache.clear()
        assert success

        # Verify cache is empty
        stats_after = await cache.stats()
        assert stats_after["memory_cache_size"] == 0

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self):
        """Test cache TTL expiration with short TTL."""
        # Create cache with very short TTL for testing
        cache = OEmbedCache(ttl=1)  # 1 second TTL

        url = "https://youtube.com/watch?v=ttl_test"

        # Set cache entry
        await cache.set(url, MOCK_YOUTUBE_RESPONSE)

        # Should be available immediately
        result = await cache.get(url)
        assert result is not None
        assert result["cached"] == True

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired and return None
        expired_result = await cache.get(url)
        assert expired_result is None

        await cache.close()


# Additional performance test without benchmark fixture
class TestCachePerformance:
    """Additional performance tests for cache functionality."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_multiple_cache_hits_performance(self):
        """Test performance of multiple consecutive cache hits."""
        url = "https://youtube.com/watch?v=perf_test"

        # Mock provider
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_RESPONSE)
        )

        client = OEmbedClient()

        # First call to populate cache
        await client.fetch_embed(url)

        # Time multiple cache hits
        start_time = time.time()
        for _ in range(100):  # 100 cache hits
            result = await client.fetch_embed(url)
            assert result["cached"] == True

        total_time = (time.time() - start_time) * 1000  # Convert to ms
        avg_time = total_time / 100

        assert (
            avg_time < 5.0
        ), f"Average cache hit time {avg_time:.2f}ms should be < 5ms"
        print(f"✅ Performance test: 100 cache hits averaged {avg_time:.2f}ms each")

        await client.close()


# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Clean up cache after each test."""
    yield
    await cleanup_oembed_cache()


if __name__ == "__main__":
    # Quick test runner
    import subprocess

    subprocess.run(["pytest", __file__, "-v", "--benchmark-only"])
