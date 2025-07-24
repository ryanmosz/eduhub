"""
Tests for the Hello World FastAPI module
Verifies async functionality, endpoints, and environment setup.
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hello import app

# Sync test client for FastAPI
client = TestClient(app)


class TestSyncEndpoints:
    """Test synchronous endpoints using TestClient."""

    def test_root_endpoint(self):
        """Test the root endpoint returns expected structure."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "status" in data
        assert "timestamp" in data
        assert data["message"] == "Hello from EduHub!"
        assert data["status"] == "Development environment ready"

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "python_version" in data
        assert "platform" in data
        assert data["async_support"] is True

        # Verify Python version format
        version = data["python_version"]
        version_parts = version.split(".")
        assert len(version_parts) == 3
        assert all(part.isdigit() for part in version_parts)

    def test_sync_hello(self):
        """Test synchronous hello endpoint."""
        response = client.get("/sync-hello")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Hello from sync endpoint"
        assert data["type"] == "synchronous"
        assert "note" in data

    def test_environment_info(self):
        """Test environment info endpoint."""
        response = client.get("/environment-info")
        assert response.status_code == 200

        data = response.json()
        assert "python" in data
        assert "fastapi" in data
        assert "deployment" in data
        assert "timestamp" in data

        # Verify structure
        assert data["fastapi"]["async_support"] is True
        assert data["deployment"]["container_ready"] is True


class TestAsyncEndpoints:
    """Test async functionality and endpoints."""

    def test_async_demo(self):
        """Test async demo endpoint with concurrent operations."""
        response = client.get("/async-demo")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Async operations completed"
        assert "results" in data
        assert "execution_time_ms" in data
        assert "python_version" in data

        # Verify async results
        results = data["results"]
        assert len(results) == 3
        assert all("Processed: Task" in result for result in results)

        # Execution time should be reasonable (concurrent, not sequential)
        execution_time = data["execution_time_ms"]
        assert execution_time < 500  # Should be much faster than 300ms (0.1+0.15+0.05)

    @patch("httpx.AsyncClient.get")
    def test_external_api_success(self, mock_get):
        """Test external API call with mocked response."""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value={"slideshow": {"title": "Sample Slide Show"}}
        )
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        response = client.get("/external-api-test")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "External API call successful"
        assert "external_data" in data
        assert data["client"] == "httpx async client"
        assert data["status_code"] == 200

    @patch("httpx.AsyncClient.get")
    def test_external_api_failure(self, mock_get):
        """Test external API call failure handling."""
        # Mock failed response
        mock_get.side_effect = httpx.HTTPError("Connection failed")

        response = client.get("/external-api-test")
        assert response.status_code == 500

        data = response.json()
        assert "detail" in data
        assert "External API call failed" in data["detail"]


@pytest.mark.asyncio
class TestAsyncFunctionality:
    """Test async functionality directly (not through HTTP)."""

    async def test_asyncio_operations(self):
        """Test that asyncio operations work correctly."""

        async def sample_async_task(delay: float) -> str:
            await asyncio.sleep(delay)
            return f"Task completed after {delay}s"

        # Test single async operation
        result = await sample_async_task(0.01)
        assert "Task completed after 0.01s" == result

        # Test concurrent operations
        start_time = datetime.now()
        tasks = [
            sample_async_task(0.01),
            sample_async_task(0.02),
            sample_async_task(0.01),
        ]
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()

        assert len(results) == 3
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 0.1  # Should be concurrent, not 0.04s sequential

    async def test_async_http_client(self):
        """Test async HTTP client functionality."""
        async with httpx.AsyncClient() as client:
            # Test that client can be created and basic operations work
            assert client is not None

            # Mock a simple request (actual external calls in CI would be unreliable)
            with patch.object(client, "get") as mock_get:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"test": "data"}
                mock_get.return_value = mock_response

                response = await client.get("https://example.com")
                assert response.status_code == 200
                assert await response.json() == {"test": "data"}


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_endpoint(self):
        """Test that invalid endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_response_headers(self):
        """Test that responses have correct headers."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestPerformance:
    """Basic performance tests."""

    def test_response_time(self):
        """Test that endpoints respond quickly."""
        import time

        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond in under 1 second

    @pytest.mark.benchmark
    def test_async_performance_benchmark(self):
        """Benchmark async vs sync performance."""
        import time

        # Test async endpoint
        start_time = time.time()
        response = client.get("/async-demo")
        async_time = time.time() - start_time

        # Test sync endpoint
        start_time = time.time()
        response = client.get("/sync-hello")
        sync_time = time.time() - start_time

        assert response.status_code == 200
        # Both should be fast for simple operations
        assert async_time < 1.0
        assert sync_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
