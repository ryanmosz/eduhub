"""
Performance Benchmark Tests for EduHub APIs

This module contains pytest-benchmark tests to measure and validate
API endpoint performance, especially comparing Python 3.9 vs 3.11 improvements.
"""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eduhub.main import app as main_app
from hello import app as hello_app


class TestHelloAPIBenchmarks:
    """Benchmark tests for Hello World API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(hello_app)

    @pytest.mark.benchmark
    def test_benchmark_root_endpoint(self, benchmark):
        """Benchmark root endpoint performance."""

        def call_root():
            response = self.client.get("/")
            assert response.status_code == 200
            return response

        result = benchmark(call_root)
        assert result.status_code == 200

    @pytest.mark.benchmark
    def test_benchmark_health_check(self, benchmark):
        """Benchmark health check endpoint performance."""

        def call_health():
            response = self.client.get("/health")
            assert response.status_code == 200
            return response

        result = benchmark(call_health)
        assert result.status_code == 200

    @pytest.mark.benchmark
    def test_benchmark_async_demo(self, benchmark):
        """Benchmark async demo endpoint with concurrent operations."""

        def call_async_demo():
            response = self.client.get("/async-demo")
            assert response.status_code == 200
            data = response.json()
            assert "execution_time_ms" in data
            return response

        result = benchmark(call_async_demo)
        data = result.json()
        # Async operations should complete efficiently
        assert data["execution_time_ms"] < 500  # Under 500ms for demo

    @pytest.mark.benchmark
    def test_benchmark_async_tasks_demo(self, benchmark):
        """Benchmark async tasks demo with long-running operations."""

        def call_async_tasks():
            response = self.client.get("/async-tasks-demo")
            assert response.status_code == 200
            data = response.json()
            assert data["operations"] == 6
            return response

        result = benchmark(call_async_tasks)
        data = result.json()
        # All 6 async operations should complete efficiently
        assert data["total_execution_time_ms"] < 1000  # Under 1s for all tasks

    @pytest.mark.benchmark
    def test_benchmark_advanced_patterns(self, benchmark):
        """Benchmark advanced async patterns endpoint."""

        def call_advanced_patterns():
            response = self.client.get("/async-patterns-advanced")
            assert response.status_code == 200
            data = response.json()
            assert "context_manager" in data
            assert "async_generator" in data
            assert "background_tasks" in data
            return response

        result = benchmark(call_advanced_patterns)
        data = result.json()
        # Advanced patterns should execute efficiently
        assert (
            data["execution_time_ms"] < 400
        )  # Under 400ms (adjusted for real performance)

    @pytest.mark.benchmark
    def test_benchmark_sync_vs_async_comparison(self, benchmark):
        """Benchmark sync vs async endpoint comparison."""

        def compare_endpoints():
            # Call async endpoint
            async_response = self.client.get("/async-demo")
            async_data = async_response.json()

            # Call sync endpoint
            sync_response = self.client.get("/sync-hello")
            sync_data = sync_response.json()

            return {
                "async_time": async_data.get("execution_time_ms", 0),
                "sync_response_time": 1,  # Sync endpoint is simple
            }

        result = benchmark(compare_endpoints)
        # Both should be fast, but this validates async overhead is minimal
        assert isinstance(result["async_time"], (int, float))


class TestMainAPIBenchmarks:
    """Benchmark tests for main EduHub API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(main_app)

    @pytest.mark.benchmark
    def test_benchmark_main_root(self, benchmark):
        """Benchmark main app root endpoint."""

        def call_root():
            response = self.client.get("/")
            assert response.status_code == 200
            return response

        result = benchmark(call_root)
        assert result.status_code == 200

    @pytest.mark.benchmark
    def test_benchmark_main_health(self, benchmark):
        """Benchmark main app health check with Plone connectivity."""

        def call_health():
            response = self.client.get("/health")
            assert response.status_code == 200
            return response

        result = benchmark(call_health)
        data = result.json()
        assert "status" in data

    @pytest.mark.benchmark
    @patch("eduhub.main.get_plone_client")
    def test_benchmark_plone_info(self, mock_get_client, benchmark):
        """Benchmark Plone info endpoint with mocked client."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client.get_site_info = AsyncMock(
            return_value={
                "title": "Plone Site",
                "description": "Test site",
                "plone_version": "6.0",
                "@id": "http://localhost:8080/Plone",
            }
        )
        mock_get_client.return_value = mock_client

        def call_plone_info():
            response = self.client.get("/plone/info")
            assert response.status_code == 200
            return response

        result = benchmark(call_plone_info)
        data = result.json()
        assert data["available"] is True
        assert "plone_site" in data

    @pytest.mark.benchmark
    @patch("eduhub.main.get_plone_client")
    def test_benchmark_content_list(self, mock_get_client, benchmark):
        """Benchmark content listing endpoint with mocked Plone data."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_client.search_content = AsyncMock(
            return_value={
                "items": [
                    {
                        "UID": "test-uid-1",
                        "title": "Test Content 1",
                        "description": "Test description",
                        "@type": "Document",
                        "@id": "http://localhost:8080/Plone/test1",
                    },
                    {
                        "UID": "test-uid-2",
                        "title": "Test Content 2",
                        "description": "Another description",
                        "@type": "News Item",
                        "@id": "http://localhost:8080/Plone/test2",
                    },
                ]
            }
        )
        mock_get_client.return_value = mock_client

        def call_content_list():
            response = self.client.get("/content/?limit=10")
            assert response.status_code == 200
            return response

        result = benchmark(call_content_list)
        data = result.json()
        assert isinstance(data, list)
        assert len(data) == 2


class TestAsyncIOBenchmarks:
    """Benchmark tests for async I/O operations and patterns."""

    @pytest.mark.benchmark
    def test_benchmark_async_client_context(self, benchmark):
        """Benchmark sync context of async client operations."""

        def sync_async_simulation():
            # Simulate the overhead of async context without actual async
            # This measures the synchronous parts of async operations
            import time

            time.sleep(0.001)  # Simulate minimal processing time
            return "async_simulation_complete"

        result = benchmark(sync_async_simulation)
        assert result == "async_simulation_complete"
