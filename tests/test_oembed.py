"""
Tests for oEmbed functionality.

Tests the Rich Media Embeds feature including URL validation,
provider integration, HTML sanitization, and error handling.
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.eduhub.main import app
from src.eduhub.oembed.client import (
    OEmbedClient,
    cleanup_oembed_client,
    get_oembed_client,
)

# Test client for FastAPI
client = TestClient(app)

# Mock oEmbed responses
MOCK_YOUTUBE_OEMBED_RESPONSE = {
    "type": "video",
    "version": "1.0",
    "title": "Rick Astley - Never Gonna Give You Up (Official Video)",
    "author_name": "Rick Astley",
    "author_url": "https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw",
    "provider_name": "YouTube",
    "provider_url": "https://www.youtube.com/",
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
    "thumbnail_width": 480,
    "thumbnail_height": 360,
    "html": '<iframe width="800" height="450" src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0" allowfullscreen></iframe>',
    "width": 800,
    "height": 450,
}

MOCK_YOUTUBE_OEMBED_WITH_SCRIPT = {
    "type": "video",
    "version": "1.0",
    "title": "Test Video",
    "provider_name": "YouTube",
    "html": '<iframe width="800" height="450" src="https://www.youtube.com/embed/test"></iframe><script>alert("xss")</script>',
    "width": 800,
    "height": 450,
}


class TestOEmbedEndpoints:
    """Test the FastAPI oEmbed endpoints."""

    def test_health_endpoint(self):
        """Test the oEmbed health check endpoint."""
        response = client.get("/embed/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "oembed-proxy"
        assert data["providers_configured"] == 10
        assert data["features"]["validation"] == "enabled"
        assert data["features"]["sanitization"] == "enabled"

    def test_providers_endpoint(self):
        """Test the providers list endpoint."""
        response = client.get("/embed/providers")
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert "youtube.com" in data["providers"]
        assert "vimeo.com" in data["providers"]
        assert data["count"] == 10
        assert "examples" in data

    def test_embed_endpoint_requires_auth(self):
        """Test that embed endpoint requires authentication."""
        response = client.get("/embed/?url=https://youtube.com/watch?v=test")
        assert response.status_code == 401

        data = response.json()
        assert "Authorization token required" in data["message"]

    @respx.mock
    def test_embed_endpoint_with_auth_mock_user(self):
        """Test embed endpoint with mocked authentication and oEmbed response."""
        # Mock the YouTube oEmbed endpoint
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_OEMBED_RESPONSE)
        )

        # Mock authentication to bypass JWT validation
        with patch("src.eduhub.oembed.endpoints.get_current_user") as mock_auth:
            mock_auth.return_value = {"email": "test@eduhub.com", "sub": "test-user-id"}

            response = client.get(
                "/embed/?url=https://youtube.com/watch?v=dQw4w9WgXcQ&maxwidth=800&maxheight=450"
            )
            assert response.status_code == 200

            data = response.json()
            assert (
                data["title"]
                == "Rick Astley - Never Gonna Give You Up (Official Video)"
            )
            assert data["provider_name"] == "YouTube"
            assert data["width"] == 800
            assert data["height"] == 450
            assert "iframe" in data["html"]
            assert data["cached"] == False

    def test_embed_endpoint_invalid_url_format(self):
        """Test embed endpoint with invalid URL format."""
        with patch("src.eduhub.oembed.endpoints.get_current_user") as mock_auth:
            mock_auth.return_value = {"email": "test@eduhub.com", "sub": "test-user-id"}

            response = client.get("/embed/?url=not-a-valid-url")
            assert response.status_code == 422

            data = response.json()
            assert "detail" in data
            # The detail should contain error information about invalid URL format

    def test_embed_endpoint_unsupported_provider(self):
        """Test embed endpoint with unsupported provider domain."""
        with patch("src.eduhub.oembed.endpoints.get_current_user") as mock_auth:
            mock_auth.return_value = {"email": "test@eduhub.com", "sub": "test-user-id"}

            response = client.get("/embed/?url=https://example.com/video")
            assert response.status_code == 422

            data = response.json()
            assert "detail" in data
            detail = data["detail"]

            # Check if it's our structured error response
            if isinstance(detail, dict):
                assert detail["error"] == "Provider not allowed"
                assert "example.com" in detail["message"]
                assert "supported_providers" in detail
            else:
                # Fallback for string error messages
                assert "Provider not allowed" in str(
                    detail
                ) or "not in the list" in str(detail)


class TestOEmbedClient:
    """Test the OEmbedClient class directly."""

    @pytest.fixture
    async def oembed_client(self):
        """Create an OEmbedClient instance for testing."""
        client = OEmbedClient(timeout=5.0)
        yield client
        await client.close()

    def test_get_provider_config_valid_domain(self, oembed_client):
        """Test getting provider config for valid domain."""
        config = oembed_client.get_provider_config("youtube.com")
        assert config["name"] == "YouTube"
        assert config["endpoint"] == "https://www.youtube.com/oembed"
        assert config["supports_https"] == True

    def test_get_provider_config_invalid_domain(self, oembed_client):
        """Test getting provider config for invalid domain raises exception."""
        with pytest.raises(Exception) as exc_info:
            oembed_client.get_provider_config("invalid-domain.com")

        # Should raise HTTPException with 422 status
        assert "422" in str(exc_info.value) or "Unsupported provider" in str(
            exc_info.value
        )

    def test_sanitize_html_basic(self, oembed_client):
        """Test HTML sanitization with basic content."""
        html = '<iframe src="https://youtube.com/embed/test" width="800"></iframe>'
        sanitized = oembed_client.sanitize_html(html)

        assert "<iframe" in sanitized
        assert 'src="https://youtube.com/embed/test"' in sanitized
        assert 'width="800"' in sanitized

    def test_sanitize_html_removes_script_tags(self, oembed_client):
        """Test HTML sanitization removes dangerous script tags."""
        html = '<iframe src="https://youtube.com/embed/test"></iframe><script>alert("xss")</script>'
        sanitized = oembed_client.sanitize_html(html)

        assert "<iframe" in sanitized
        assert "<script" not in sanitized
        assert "alert" not in sanitized

    def test_sanitize_html_removes_dangerous_attributes(self, oembed_client):
        """Test HTML sanitization removes dangerous attributes."""
        html = (
            '<iframe src="https://youtube.com/embed/test" onload="alert(1)"></iframe>'
        )
        sanitized = oembed_client.sanitize_html(html)

        assert "<iframe" in sanitized
        assert "onload" not in sanitized
        assert "alert" not in sanitized

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_embed_success(self, oembed_client):
        """Test successful oEmbed fetch from provider."""
        # Mock the YouTube oEmbed API
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_OEMBED_RESPONSE)
        )

        result = await oembed_client.fetch_embed(
            "https://youtube.com/watch?v=dQw4w9WgXcQ", maxwidth=800, maxheight=450
        )

        assert (
            result["title"] == "Rick Astley - Never Gonna Give You Up (Official Video)"
        )
        assert result["provider_name"] == "YouTube"
        assert result["width"] == 800
        assert result["height"] == 450
        assert "iframe" in result["html"]
        assert result["cached"] == False

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_embed_sanitizes_html(self, oembed_client):
        """Test that fetch_embed sanitizes HTML content."""
        # Mock YouTube response with script tag
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_OEMBED_WITH_SCRIPT)
        )

        result = await oembed_client.fetch_embed("https://youtube.com/watch?v=test")

        assert "<iframe" in result["html"]
        assert "<script" not in result["html"]
        assert "alert" not in result["html"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_embed_provider_timeout(self, oembed_client):
        """Test handling of provider timeout."""
        # Mock timeout response
        respx.get("https://www.youtube.com/oembed").mock(
            side_effect=httpx.TimeoutException("Request timed out")
        )

        with pytest.raises(Exception) as exc_info:
            await oembed_client.fetch_embed("https://youtube.com/watch?v=test")

        # Should raise HTTPException with 504 status
        assert "504" in str(exc_info.value) or "timeout" in str(exc_info.value).lower()

    @respx.mock
    @pytest.mark.asyncio
    async def test_fetch_embed_provider_error(self, oembed_client):
        """Test handling of provider HTTP error."""
        # Mock 404 response
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        with pytest.raises(Exception) as exc_info:
            await oembed_client.fetch_embed("https://youtube.com/watch?v=test")

        # Should raise HTTPException with 502 status
        assert "502" in str(exc_info.value) or "404" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_embed_unsupported_provider(self, oembed_client):
        """Test fetch_embed with unsupported provider."""
        with pytest.raises(Exception) as exc_info:
            await oembed_client.fetch_embed("https://unsupported-site.com/video")

        assert "422" in str(exc_info.value) or "Unsupported provider" in str(
            exc_info.value
        )


class TestOEmbedIntegration:
    """Integration tests for the complete oEmbed flow."""

    @respx.mock
    def test_test_endpoint_success(self):
        """Test the /embed/test endpoint (no auth required)."""
        # Mock the YouTube oEmbed endpoint
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_OEMBED_RESPONSE)
        )

        response = client.get("/embed/test")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["domain"] == "youtube.com"
        assert (
            data["oembed_response"]["title"]
            == "Rick Astley - Never Gonna Give You Up (Official Video)"
        )
        assert data["oembed_response"]["html_sanitized"] == True
        assert data["oembed_response"]["html_length"] > 0
        assert "Task 5.1.3 Complete" in data["message"]

    @respx.mock
    def test_test_endpoint_provider_error(self):
        """Test the /embed/test endpoint with provider error."""
        # Mock provider error
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        response = client.get("/embed/test")
        assert response.status_code == 200  # Test endpoint catches errors

        data = response.json()
        assert data["status"] == "error"
        assert "404" in str(data["error"]) or "502" in str(data["error"])


# Cleanup function to reset global client state between tests
@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Clean up oEmbed client after each test."""
    yield
    await cleanup_oembed_client()
