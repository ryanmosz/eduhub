"""
Tests for Plone-FastAPI Integration

This module tests both the PloneClient integration layer and the FastAPI endpoints
that provide modern REST API access to legacy Plone CMS content.
"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eduhub.main import app
from eduhub.plone_integration import (
    PloneAPIError,
    PloneClient,
    PloneConfig,
    PloneContent,
    close_plone_client,
    get_plone_client,
    transform_plone_content,
)


class TestPloneConfig:
    """Test PloneConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PloneConfig()
        assert config.base_url == "http://localhost:8080/Plone"
        assert config.username == "admin"
        assert config.password == "admin"
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_custom_config(self):
        """Test custom configuration values."""
        config = PloneConfig(
            base_url="http://custom.example.com/site",
            username="testuser",
            password="testpass",
            timeout=60,
            max_retries=5,
        )
        assert config.base_url == "http://custom.example.com/site"
        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.timeout == 60
        assert config.max_retries == 5


class TestPloneContent:
    """Test PloneContent model."""

    def test_minimal_content(self):
        """Test minimal content creation."""
        content = PloneContent(
            uid="123456",
            title="Test Content",
            portal_type="Document",
            url="http://example.com/test",
        )
        assert content.uid == "123456"
        assert content.title == "Test Content"
        assert content.portal_type == "Document"
        assert content.url == "http://example.com/test"
        assert content.description is None
        assert content.metadata == {}

    def test_full_content(self):
        """Test content with all fields."""
        content = PloneContent(
            uid="123456",
            title="Test Content",
            description="A test document",
            portal_type="Document",
            url="http://example.com/test",
            created="2024-01-01T00:00:00Z",
            modified="2024-01-02T00:00:00Z",
            state="published",
            text="<p>Content text</p>",
            metadata={"custom_field": "value"},
        )
        assert content.description == "A test document"
        assert content.created == "2024-01-01T00:00:00Z"
        assert content.state == "published"
        assert content.text == "<p>Content text</p>"
        assert content.metadata["custom_field"] == "value"


class TestTransformPloneContent:
    """Test content transformation function."""

    def test_basic_transformation(self):
        """Test basic Plone data transformation."""
        plone_data = {
            "UID": "test-uid-123",
            "title": "Test Document",
            "description": "Test description",
            "@type": "Document",
            "@id": "http://example.com/test",
            "created": "2024-01-01T00:00:00Z",
            "modified": "2024-01-02T00:00:00Z",
            "review_state": "published",
        }

        content = transform_plone_content(plone_data)

        assert content.uid == "test-uid-123"
        assert content.title == "Test Document"
        assert content.description == "Test description"
        assert content.portal_type == "Document"
        assert content.url == "http://example.com/test"
        assert content.created == "2024-01-01T00:00:00Z"
        assert content.modified == "2024-01-02T00:00:00Z"
        assert content.state == "published"

    def test_transformation_with_text(self):
        """Test transformation with text field."""
        plone_data = {
            "UID": "test-uid-123",
            "title": "Test Document",
            "@type": "Document",
            "@id": "http://example.com/test",
            "text": {"data": "<p>Document content</p>", "content-type": "text/html"},
        }

        content = transform_plone_content(plone_data)
        assert content.text == "<p>Document content</p>"

    def test_transformation_with_metadata(self):
        """Test transformation preserves additional metadata."""
        plone_data = {
            "UID": "test-uid-123",
            "title": "Test Document",
            "@type": "Document",
            "@id": "http://example.com/test",
            "custom_field": "custom_value",
            "another_field": 42,
        }

        content = transform_plone_content(plone_data)
        assert content.metadata["custom_field"] == "custom_value"
        assert content.metadata["another_field"] == 42

    def test_transformation_missing_fields(self):
        """Test transformation with missing fields."""
        plone_data = {"title": "Minimal Document"}

        content = transform_plone_content(plone_data)
        assert content.uid == ""
        assert content.title == "Minimal Document"
        assert content.portal_type == ""
        assert content.url == ""


@pytest.mark.asyncio
class TestPloneClient:
    """Test PloneClient functionality with mocked HTTP requests."""

    @pytest.fixture
    def mock_config(self):
        """Fixture providing test configuration."""
        return PloneConfig(
            base_url="http://test.example.com/Plone",
            username="testuser",
            password="testpass",
            timeout=10,
        )

    @pytest.fixture
    def plone_client(self, mock_config):
        """Fixture providing PloneClient instance."""
        return PloneClient(mock_config)

    async def test_client_init(self, plone_client):
        """Test client initialization."""
        assert plone_client.config.base_url == "http://test.example.com/Plone"
        assert plone_client._client is None
        assert plone_client._auth_token is None

    @patch("httpx.AsyncClient")
    async def test_client_connect_success(self, mock_client_class, plone_client):
        """Test successful client connection and authentication."""
        # Mock the HTTP client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock authentication response
        mock_auth_response = AsyncMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json = AsyncMock(return_value={"token": "test-jwt-token"})
        mock_client.post.return_value = mock_auth_response

        await plone_client.connect()

        assert plone_client._client is not None
        assert plone_client._auth_token == "test-jwt-token"

        # Verify authentication call was made
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/@login" in call_args[0][0]
        assert call_args[1]["json"]["login"] == "testuser"
        assert call_args[1]["json"]["password"] == "testpass"

    @patch("httpx.AsyncClient")
    async def test_client_connect_auth_failure(self, mock_client_class, plone_client):
        """Test client connection with authentication failure."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock failed authentication response
        mock_auth_response = AsyncMock()
        mock_auth_response.status_code = 401
        mock_auth_response.text = "Authentication failed"
        mock_auth_response.json.return_value = {"error": "Invalid credentials"}
        mock_auth_response.content = b'{"error": "Invalid credentials"}'
        mock_client.post.return_value = mock_auth_response

        with pytest.raises(PloneAPIError) as exc_info:
            await plone_client.connect()

        assert "Authentication failed: 401" in str(exc_info.value)
        assert exc_info.value.status_code == 401

    @patch("httpx.AsyncClient")
    async def test_get_content(self, mock_client_class, plone_client):
        """Test getting content from Plone."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        plone_client._client = mock_client

        # Mock content response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value={
                "UID": "content-123",
                "title": "Test Content",
                "@type": "Document",
                "@id": "http://test.example.com/Plone/test-content",
            }
        )
        mock_response.raise_for_status = AsyncMock()
        mock_client.request.return_value = mock_response

        content_data = await plone_client.get_content("test-content")

        assert content_data["UID"] == "content-123"
        assert content_data["title"] == "Test Content"

        # Verify the request was made correctly
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "GET"
        assert "test-content" in call_args[1]["url"]

    @patch("httpx.AsyncClient")
    async def test_search_content(self, mock_client_class, plone_client):
        """Test searching content in Plone."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        plone_client._client = mock_client

        # Mock search response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = AsyncMock(
            return_value={
                "items": [
                    {"UID": "item-1", "title": "First Item", "@type": "Document"},
                    {"UID": "item-2", "title": "Second Item", "@type": "News Item"},
                ],
                "items_total": 2,
            }
        )
        mock_response.raise_for_status = AsyncMock()
        mock_client.request.return_value = mock_response

        results = await plone_client.search_content(
            query="test", portal_type="Document", limit=10
        )

        assert len(results["items"]) == 2
        assert results["items"][0]["title"] == "First Item"

        # Verify search parameters
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        params = call_args[1]["params"]
        assert params["SearchableText"] == "test"
        assert params["portal_type"] == ["Document"]
        assert params["b_size"] == 10

    async def test_client_close(self, plone_client):
        """Test client cleanup."""
        mock_client = AsyncMock()
        plone_client._client = mock_client
        plone_client._auth_token = "test-token"

        await plone_client.close()

        assert plone_client._client is None
        assert plone_client._auth_token is None
        mock_client.aclose.assert_called_once()


class TestFastAPIEndpoints:
    """Test FastAPI endpoints for Plone integration."""

    @pytest.fixture
    def client(self):
        """Fixture providing FastAPI test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Welcome to EduHub API"
        assert "endpoints" in data
        assert "plone" in data["endpoints"]

    def test_health_check_without_plone(self, client):
        """Test health check when Plone is unavailable."""
        response = client.get("/health")

        # Health check should work even if Plone is unavailable
        assert response.status_code in [200, 503]  # Could be degraded

        data = response.json()
        assert data["service"] == "eduhub-api"
        assert "components" in data

    @patch("eduhub.main.get_plone_client")
    def test_plone_info_success(self, mock_get_client, client):
        """Test Plone info endpoint with successful connection."""
        # Mock Plone client
        mock_client = AsyncMock()
        mock_client.get_site_info.return_value = {
            "title": "Test Plone Site",
            "description": "A test site",
            "plone_version": "6.1.0",
            "@id": "http://test.example.com/Plone",
        }
        mock_get_client.return_value = mock_client

        response = client.get("/plone/info")
        assert response.status_code == 200

        data = response.json()
        assert data["plone_site"] == "Test Plone Site"
        assert data["plone_version"] == "6.1.0"
        assert data["available"] is True

    @patch("eduhub.main.get_plone_client")
    def test_plone_info_error(self, mock_get_client, client):
        """Test Plone info endpoint with connection error."""
        # Mock Plone client that raises an error
        mock_get_client.side_effect = PloneAPIError("Connection failed")

        response = client.get("/plone/info")
        assert response.status_code == 502

        data = response.json()
        assert "Plone API error" in data["detail"]

    @patch("eduhub.main.get_plone_client")
    def test_list_content_success(self, mock_get_client, client):
        """Test content listing endpoint."""
        # Mock Plone client
        mock_client = AsyncMock()
        mock_client.search_content.return_value = {
            "items": [
                {
                    "UID": "item-1",
                    "title": "Test Document",
                    "@type": "Document",
                    "@id": "http://test.example.com/Plone/test-doc",
                    "description": "A test document",
                }
            ]
        }
        mock_get_client.return_value = mock_client

        response = client.get("/content/")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Document"
        assert data[0]["portal_type"] == "Document"

    @patch("eduhub.main.get_plone_client")
    def test_list_content_with_filters(self, mock_get_client, client):
        """Test content listing with search filters."""
        mock_client = AsyncMock()
        mock_client.search_content.return_value = {"items": []}
        mock_get_client.return_value = mock_client

        response = client.get("/content/?query=test&content_type=Document&limit=10")
        assert response.status_code == 200

        # Verify search was called with correct parameters
        mock_client.search_content.assert_called_once()
        call_args = mock_client.search_content.call_args
        kwargs = call_args[1]
        assert kwargs["query"] == "test"
        assert kwargs["portal_type"] == "Document"
        assert kwargs["limit"] == 10

    @patch("eduhub.main.get_plone_client")
    def test_get_content_by_path_success(self, mock_get_client, client):
        """Test getting specific content by path."""
        mock_client = AsyncMock()
        mock_client.get_content.return_value = {
            "UID": "content-123",
            "title": "Specific Content",
            "@type": "Document",
            "@id": "http://test.example.com/Plone/specific-content",
        }
        mock_get_client.return_value = mock_client

        response = client.get("/content/specific-content")
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Specific Content"
        assert data["uid"] == "content-123"

    @patch("eduhub.main.get_plone_client")
    def test_get_content_by_path_not_found(self, mock_get_client, client):
        """Test getting content that doesn't exist."""
        mock_client = AsyncMock()
        mock_client.get_content.side_effect = PloneAPIError(
            "Not found", status_code=404
        )
        mock_get_client.return_value = mock_client

        response = client.get("/content/nonexistent")
        assert response.status_code == 404

        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
class TestIntegrationFlow:
    """Integration tests for the complete Plone-FastAPI flow."""

    @patch("httpx.AsyncClient")
    async def test_complete_integration_flow(self, mock_client_class):
        """Test complete flow from client creation to content access."""
        # Mock HTTP client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock authentication
        mock_auth_response = AsyncMock()
        mock_auth_response.status_code = 200
        mock_auth_response.json = AsyncMock(return_value={"token": "test-token"})

        # Mock content response
        mock_content_response = AsyncMock()
        mock_content_response.status_code = 200
        mock_content_response.json = AsyncMock(
            return_value={
                "UID": "test-123",
                "title": "Integration Test Content",
                "@type": "Document",
                "@id": "http://test.example.com/Plone/test-content",
                "description": "Content for integration testing",
            }
        )
        mock_content_response.raise_for_status = AsyncMock()

        # Configure mock responses
        mock_client.post.return_value = mock_auth_response
        mock_client.request.return_value = mock_content_response

        # Test the integration
        config = PloneConfig(base_url="http://test.example.com/Plone")
        client = PloneClient(config)

        try:
            await client.connect()
            content_data = await client.get_content("test-content")
            content_obj = transform_plone_content(content_data)

            # Verify the complete flow worked
            assert content_obj.title == "Integration Test Content"
            assert content_obj.portal_type == "Document"
            assert content_obj.description == "Content for integration testing"

        finally:
            await client.close()

    async def test_singleton_client_management(self):
        """Test singleton client management functions."""
        # Initially no client should exist
        assert get_plone_client is not None

        # Test cleanup
        await close_plone_client()  # Should not error even if no client exists


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
