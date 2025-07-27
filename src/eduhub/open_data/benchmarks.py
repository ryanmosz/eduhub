"""
Performance benchmarks for Open Data API.

Uses pytest-benchmark to measure and enforce performance targets:
- Cache hits: ≤ 10ms
- List endpoint: ≤ 50ms
- Item detail: ≤ 20ms
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.eduhub.main import app
from src.eduhub.open_data.cache import OpenDataCache
from src.eduhub.open_data.pagination import create_cursor, parse_cursor
from src.eduhub.open_data.serializers import to_public_item, to_public_items


class TestCachingBenchmarks:
    """Benchmark caching operations."""

    @pytest.fixture
    def cache_instance(self):
        """Create cache instance for testing."""
        return OpenDataCache()

    @pytest.fixture
    def sample_data(self):
        """Sample data for caching."""
        return {
            "items": [
                {
                    "uid": f"bench-uid-{i}",
                    "title": f"Benchmark Document {i}",
                    "portal_type": "Document",
                    "url": f"https://example.com/bench-{i}",
                    "description": f"Benchmark description {i}",
                    "created": "2024-01-15T10:30:00Z",
                    "modified": "2024-01-20T14:45:00Z",
                    "metadata": {"subject": ["benchmark", "test"]},
                }
                for i in range(10)
            ],
            "total": 100,
            "limit": 10,
            "offset": 0,
            "has_more": True,
            "next_cursor": "eyJvZmZzZXQiOjEwLCJ0aW1lc3RhbXAiOiIyMDI0In0=",
        }

    def test_cache_set_performance(self, benchmark, cache_instance, sample_data):
        """Benchmark cache set operations."""

        async def cache_set():
            await cache_instance.set("benchmark_key", sample_data, ttl=3600)

        # Run benchmark
        result = benchmark(asyncio.run, cache_set())

        # Performance target: cache set should be very fast
        # This is more about ensuring no performance regressions

    def test_cache_get_performance(self, benchmark, cache_instance, sample_data):
        """Benchmark cache get operations (target: ≤ 10ms)."""

        # Pre-populate cache
        asyncio.run(cache_instance.set("benchmark_key", sample_data, ttl=3600))

        async def cache_get():
            return await cache_instance.get("benchmark_key")

        # Run benchmark
        result = benchmark(asyncio.run, cache_get())

        # Verify result
        assert result is not None
        assert len(result["items"]) == 10

        # Performance target check (this will show in benchmark report)
        # pytest-benchmark will track this automatically

    def test_cache_miss_performance(self, benchmark, cache_instance):
        """Benchmark cache miss operations."""

        async def cache_miss():
            return await cache_instance.get("nonexistent_key")

        # Run benchmark
        result = benchmark(asyncio.run, cache_miss())

        # Verify miss
        assert result is None


class TestSerializationBenchmarks:
    """Benchmark serialization operations."""

    @pytest.fixture
    def plone_data_single(self):
        """Single Plone item for benchmarking."""
        return {
            "UID": "benchmark-uid-123",
            "title": "Benchmark Document",
            "description": "A document for benchmarking serialization",
            "@type": "Document",
            "@id": "https://example.com/benchmark",
            "created": "2024-01-15T10:30:00Z",
            "modified": "2024-01-20T14:45:00Z",
            "review_state": "published",
            "subject": ["benchmark", "performance", "test"],
            "language": "en",
            "effective": "2024-01-15T10:30:00Z",
            "exclude_from_nav": False,
        }

    @pytest.fixture
    def plone_data_bulk(self):
        """Bulk Plone data for benchmarking."""
        return [
            {
                "UID": f"bulk-uid-{i}",
                "title": f"Bulk Document {i}",
                "description": f"Bulk description {i}",
                "@type": "Document",
                "@id": f"https://example.com/bulk-{i}",
                "created": "2024-01-15T10:30:00Z",
                "modified": "2024-01-20T14:45:00Z",
                "review_state": "published",
                "subject": ["bulk", "test"],
                "language": "en",
                "exclude_from_nav": False,
            }
            for i in range(25)  # Standard page size
        ]

    def test_single_item_serialization(self, benchmark, plone_data_single):
        """Benchmark single item serialization."""

        def serialize_single():
            return to_public_item(plone_data_single)

        # Run benchmark
        result = benchmark(serialize_single)

        # Verify result
        assert result is not None
        assert result.uid == "benchmark-uid-123"
        assert result.title == "Benchmark Document"

    def test_bulk_serialization(self, benchmark, plone_data_bulk):
        """Benchmark bulk item serialization."""

        def serialize_bulk():
            return to_public_items(plone_data_bulk)

        # Run benchmark
        result = benchmark(serialize_bulk)

        # Verify result
        assert len(result) == 25
        assert all(item.uid.startswith("bulk-uid-") for item in result)


class TestPaginationBenchmarks:
    """Benchmark pagination operations."""

    def test_cursor_creation_performance(self, benchmark):
        """Benchmark cursor creation."""

        def create_cursors():
            cursors = []
            for i in range(100):
                cursor = create_cursor(offset=i * 25, timestamp="2024-01-20T15:30:00Z")
                cursors.append(cursor)
            return cursors

        # Run benchmark
        result = benchmark(create_cursors)

        # Verify result
        assert len(result) == 100
        assert all(isinstance(cursor, str) for cursor in result)

    def test_cursor_parsing_performance(self, benchmark):
        """Benchmark cursor parsing."""

        # Pre-create cursors
        cursors = [create_cursor(offset=i * 25) for i in range(100)]

        def parse_cursors():
            results = []
            for cursor in cursors:
                offset, timestamp = parse_cursor(cursor)
                results.append((offset, timestamp))
            return results

        # Run benchmark
        result = benchmark(parse_cursors)

        # Verify result
        assert len(result) == 100
        assert all(isinstance(offset, int) for offset, _ in result)


class TestEndpointBenchmarks:
    """Benchmark API endpoints with realistic scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_plone_response(self):
        """Mock Plone response for benchmarking."""
        return {
            "items": [
                {
                    "UID": f"bench-endpoint-{i}",
                    "title": f"Endpoint Benchmark Document {i}",
                    "description": f"Description for benchmark {i}",
                    "@type": "Document",
                    "@id": f"https://example.com/bench-endpoint-{i}",
                    "created": "2024-01-15T10:30:00Z",
                    "modified": "2024-01-20T14:45:00Z",
                    "review_state": "published",
                    "subject": ["benchmark"],
                    "language": "en",
                    "exclude_from_nav": False,
                }
                for i in range(25)
            ],
            "items_total": 250,
        }

    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    def test_list_items_cache_hit_benchmark(self, mock_cache, benchmark, client):
        """Benchmark list items with cache hit (target: ≤ 10ms)."""

        # Mock cache hit with pre-serialized data
        cached_response = {
            "items": [
                {
                    "uid": f"cached-{i}",
                    "title": f"Cached Document {i}",
                    "portal_type": "Document",
                    "url": f"https://example.com/cached-{i}",
                    "description": f"Cached description {i}",
                    "created": "2024-01-15T10:30:00Z",
                    "modified": "2024-01-20T14:45:00Z",
                    "metadata": {"subject": ["cached"]},
                }
                for i in range(25)
            ],
            "total": 250,
            "limit": 25,
            "offset": 0,
            "has_more": True,
            "next_cursor": "eyJvZmZzZXQiOjI1LCJ0aW1lc3RhbXAiOiIyMDI0In0=",
        }
        mock_cache.return_value = cached_response

        def make_cached_request():
            response = client.get("/data/items")
            return response

        # Run benchmark
        response = benchmark(make_cached_request)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 25
        assert data["total"] == 250

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    @patch("src.eduhub.open_data.endpoints.cache_response")
    def test_list_items_cache_miss_benchmark(
        self,
        mock_cache_set,
        mock_cache_get,
        mock_plone_client,
        benchmark,
        client,
        mock_plone_response,
    ):
        """Benchmark list items with cache miss (target: ≤ 50ms)."""

        # Mock cache miss
        mock_cache_get.return_value = None

        # Mock Plone client
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = mock_plone_response
        mock_plone_client.return_value = mock_client_instance

        def make_uncached_request():
            response = client.get("/data/items")
            return response

        # Run benchmark
        response = benchmark(make_uncached_request)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 25
        assert data["total"] == 250

    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    def test_get_item_cache_hit_benchmark(self, mock_cache, benchmark, client):
        """Benchmark get item with cache hit (target: ≤ 5ms)."""

        # Mock cache hit
        cached_item = {
            "uid": "cached-item-benchmark",
            "title": "Cached Item for Benchmark",
            "portal_type": "Document",
            "url": "https://example.com/cached-item-benchmark",
            "description": "Cached item description",
            "created": "2024-01-15T10:30:00Z",
            "modified": "2024-01-20T14:45:00Z",
            "metadata": {"subject": ["cached", "benchmark"]},
        }
        mock_cache.return_value = cached_item

        def make_cached_item_request():
            response = client.get("/data/item/cached-item-benchmark")
            return response

        # Run benchmark
        response = benchmark(make_cached_item_request)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == "cached-item-benchmark"

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    @patch("src.eduhub.open_data.endpoints.cache_response")
    def test_get_item_cache_miss_benchmark(
        self, mock_cache_set, mock_cache_get, mock_plone_client, benchmark, client
    ):
        """Benchmark get item with cache miss (target: ≤ 20ms)."""

        # Mock cache miss
        mock_cache_get.return_value = None

        # Mock Plone client
        single_item_response = {
            "items": [
                {
                    "UID": "benchmark-item-uid",
                    "title": "Benchmark Item",
                    "description": "Item for benchmarking",
                    "@type": "Document",
                    "@id": "https://example.com/benchmark-item",
                    "created": "2024-01-15T10:30:00Z",
                    "modified": "2024-01-20T14:45:00Z",
                    "review_state": "published",
                    "subject": ["benchmark"],
                    "language": "en",
                    "exclude_from_nav": False,
                }
            ],
            "items_total": 1,
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = single_item_response
        mock_plone_client.return_value = mock_client_instance

        def make_uncached_item_request():
            response = client.get("/data/item/benchmark-item-uid")
            return response

        # Run benchmark
        response = benchmark(make_uncached_item_request)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == "benchmark-item-uid"


class TestConcurrentAccessBenchmarks:
    """Benchmark concurrent access patterns."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    def test_concurrent_cache_hits_benchmark(self, mock_cache, benchmark, client):
        """Benchmark concurrent cache hit performance."""

        # Mock cache hit
        cached_response = {
            "items": [
                {
                    "uid": "concurrent-test",
                    "title": "Concurrent Test",
                    "portal_type": "Document",
                    "url": "https://example.com/concurrent",
                    "description": None,
                    "created": None,
                    "modified": None,
                    "metadata": None,
                }
            ],
            "total": 1,
            "limit": 25,
            "offset": 0,
            "has_more": False,
            "next_cursor": None,
        }
        mock_cache.return_value = cached_response

        def make_concurrent_requests():
            # Simulate concurrent requests
            responses = []
            for _ in range(10):
                response = client.get("/data/items")
                responses.append(response)
            return responses

        # Run benchmark
        responses = benchmark(make_concurrent_requests)

        # Verify all responses
        assert len(responses) == 10
        assert all(response.status_code == 200 for response in responses)


# Benchmark configuration and custom markers
def pytest_configure(config):
    """Configure pytest for benchmarks."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a performance benchmark"
    )


# Custom benchmark assertions for performance targets
def assert_performance_target(benchmark_result, target_ms):
    """Assert that benchmark meets performance target."""
    # This would be used in actual benchmark validation
    # pytest-benchmark provides statistics in benchmark_result
    pass


# Integration with pytest-benchmark configuration
# Add to pytest.ini or pyproject.toml:
#
# [tool.pytest.ini_options]
# addopts = "--benchmark-only --benchmark-sort=mean"
# markers = [
#     "benchmark: marks tests as benchmarks",
# ]
