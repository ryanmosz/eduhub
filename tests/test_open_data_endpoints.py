"""
Integration tests for Open Data API endpoints.

Tests the FastAPI endpoints with mocked Plone backend integration.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.eduhub.main import app
from src.eduhub.open_data.models import ItemListResponse, ItemPublic


class TestOpenDataEndpoints:
    """Test Open Data API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_plone_response(self):
        """Sample Plone API response."""
        return {
            "items": [
                {
                    "UID": "test-uid-1",
                    "title": "Sample Document",
                    "description": "A sample document for testing",
                    "@type": "Document",
                    "@id": "https://example.com/sample",
                    "created": "2024-01-15T10:30:00Z",
                    "modified": "2024-01-20T14:45:00Z",
                    "review_state": "published",
                    "subject": ["testing", "sample"],
                    "language": "en",
                    "exclude_from_nav": False,
                },
                {
                    "UID": "test-uid-2",
                    "title": "Another Document",
                    "description": "Another document for testing",
                    "@type": "News Item",
                    "@id": "https://example.com/another",
                    "created": "2024-01-16T11:00:00Z",
                    "modified": "2024-01-21T15:30:00Z",
                    "review_state": "published",
                    "subject": ["news", "testing"],
                    "language": "en",
                    "exclude_from_nav": False,
                },
            ],
            "items_total": 25,
        }

    @pytest.fixture
    def single_plone_item(self):
        """Single Plone item response."""
        return {
            "items": [
                {
                    "UID": "single-uid-123",
                    "title": "Single Document",
                    "description": "A single document for testing",
                    "@type": "Document",
                    "@id": "https://example.com/single",
                    "created": "2024-01-15T10:30:00Z",
                    "modified": "2024-01-20T14:45:00Z",
                    "review_state": "published",
                    "subject": ["single", "test"],
                    "language": "en",
                    "exclude_from_nav": False,
                }
            ],
            "items_total": 1,
        }


class TestListItemsEndpoint(TestOpenDataEndpoints):
    """Test GET /data/items endpoint."""

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_list_items_success(
        self, mock_cache, mock_plone_client, client, sample_plone_response
    ):
        """Test successful list items request."""
        # Mock cache miss
        mock_cache.return_value = None

        # Mock Plone client
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = sample_plone_response
        mock_plone_client.return_value = mock_client_instance

        # Make request
        response = client.get("/data/items")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        assert len(data["items"]) == 2
        assert data["total"] == 25
        assert data["limit"] == 25
        assert data["offset"] == 0
        assert data["has_more"] is False

        # Check item structure
        item = data["items"][0]
        assert item["uid"] == "test-uid-1"
        assert item["title"] == "Sample Document"
        assert item["portal_type"] == "Document"

    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_list_items_cache_hit(self, mock_cache, client):
        """Test cache hit scenario."""
        # Mock cache hit
        cached_response = {
            "items": [
                {
                    "uid": "cached-uid",
                    "title": "Cached Document",
                    "portal_type": "Document",
                    "url": "https://example.com/cached",
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

        # Make request
        response = client.get("/data/items")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["uid"] == "cached-uid"
        assert data["items"][0]["title"] == "Cached Document"

    async def test_list_items_with_search_params(self, client):
        """Test list items with search parameters."""
        # Mock to avoid actual Plone calls during param validation
        with patch("src.eduhub.open_data.endpoints.PloneClient") as mock_plone_client:
            mock_client_instance = AsyncMock()
            mock_client_instance.search_content.return_value = {
                "items": [],
                "items_total": 0,
            }
            mock_plone_client.return_value = mock_client_instance

            with patch(
                "src.eduhub.open_data.endpoints.get_cached_response"
            ) as mock_cache:
                mock_cache.return_value = None

                # Make request with parameters
                response = client.get(
                    "/data/items?search=python&portal_type=Document&limit=10"
                )

                # Should succeed with valid parameters
                assert response.status_code == 200

    async def test_list_items_invalid_params(self, client):
        """Test list items with invalid parameters."""
        # Invalid search (too short)
        response = client.get("/data/items?search=a")
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        if isinstance(error_detail, list):
            # FastAPI validation error format
            assert any("at least 2 characters" in str(error) for error in error_detail)
        else:
            # Our custom error format
            assert "at least 2 characters" in error_detail["message"]

        # Invalid portal type
        response = client.get("/data/items?portal_type=InvalidType")
        assert response.status_code == 422

        # Invalid limit
        response = client.get("/data/items?limit=0")
        assert response.status_code == 422

        response = client.get("/data/items?limit=101")
        assert response.status_code == 422

    async def test_list_items_pagination(self, client):
        """Test pagination with limit parameter."""
        with patch("src.eduhub.open_data.endpoints.PloneClient") as mock_plone_client:
            mock_client_instance = AsyncMock()
            # Mock response with more items than limit
            mock_response = {
                "items": [
                    {
                        "UID": f"test-uid-{i}",
                        "title": f"Document {i}",
                        "@type": "Document",
                        "@id": f"https://example.com/doc{i}",
                        "review_state": "published",
                        "exclude_from_nav": False,
                    }
                    for i in range(5)  # 5 items
                ],
                "items_total": 25,  # Total available
            }
            mock_client_instance.search_content.return_value = mock_response
            mock_plone_client.return_value = mock_client_instance

            with patch(
                "src.eduhub.open_data.endpoints.get_cached_response"
            ) as mock_cache:
                mock_cache.return_value = None

                # Request 5 items
                response = client.get("/data/items?limit=5")

                assert response.status_code == 200
                data = response.json()

                assert len(data["items"]) == 5
                assert data["limit"] == 5
                assert data["total"] == 25
                assert data["has_more"] is True
                assert data["next_cursor"] is not None

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    async def test_list_items_plone_error(self, mock_plone_client, client):
        """Test handling of Plone client errors."""
        # Mock Plone client to raise exception
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.side_effect = Exception(
            "Plone connection failed"
        )
        mock_plone_client.return_value = mock_client_instance

        with patch("src.eduhub.open_data.endpoints.get_cached_response") as mock_cache:
            mock_cache.return_value = None

            # Make request
            response = client.get("/data/items")

            # Should return 500 error
            assert response.status_code == 500
            assert "internal_error" in response.json()["detail"]["error"]


class TestGetItemEndpoint(TestOpenDataEndpoints):
    """Test GET /data/item/{uid} endpoint."""

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_get_item_success(
        self, mock_cache, mock_plone_client, client, single_plone_item
    ):
        """Test successful get item request."""
        # Mock cache miss
        mock_cache.return_value = None

        # Mock Plone client
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = single_plone_item
        mock_plone_client.return_value = mock_client_instance

        # Make request
        response = client.get("/data/item/single-uid-123")

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["uid"] == "single-uid-123"
        assert data["title"] == "Single Document"
        assert data["portal_type"] == "Document"
        assert data["url"] == "https://example.com/single"
        assert data["description"] == "A single document for testing"

    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_get_item_cache_hit(self, mock_cache, client):
        """Test cache hit for get item."""
        # Mock cache hit
        cached_item = {
            "uid": "cached-item-uid",
            "title": "Cached Item",
            "portal_type": "Document",
            "url": "https://example.com/cached-item",
            "description": "From cache",
            "created": "2024-01-15T10:30:00Z",
            "modified": "2024-01-20T14:45:00Z",
            "metadata": {"language": "en"},
        }
        mock_cache.return_value = cached_item

        # Make request
        response = client.get("/data/item/cached-item-uid")

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["uid"] == "cached-item-uid"
        assert data["title"] == "Cached Item"
        assert data["description"] == "From cache"

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_get_item_not_found(self, mock_cache, mock_plone_client, client):
        """Test get item when UID not found."""
        # Mock cache miss
        mock_cache.return_value = None

        # Mock Plone client returning empty results
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = {
            "items": [],
            "items_total": 0,
        }
        mock_plone_client.return_value = mock_client_instance

        # Make request
        response = client.get("/data/item/nonexistent-uid")

        # Should return 404
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "not_found"
        assert "nonexistent-uid" in data["detail"]["message"]

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_get_item_private_content(
        self, mock_cache, mock_plone_client, client
    ):
        """Test get item when content is private."""
        # Mock cache miss
        mock_cache.return_value = None

        # Mock Plone client returning private content
        private_response = {
            "items": [
                {
                    "UID": "private-uid",
                    "title": "Private Document",
                    "@type": "Document",
                    "@id": "https://example.com/private",
                    "review_state": "private",  # Private content
                    "exclude_from_nav": False,
                }
            ],
            "items_total": 1,
        }
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = private_response
        mock_plone_client.return_value = mock_client_instance

        # Make request
        response = client.get("/data/item/private-uid")

        # Should return 404 (private content treated as not found)
        assert response.status_code == 404
        assert "not found or not public" in response.json()["detail"]["message"]

    async def test_get_item_invalid_uid(self, client):
        """Test get item with invalid UID."""
        # UID too short
        response = client.get("/data/item/ab")
        assert response.status_code == 422
        assert "at least 3 characters" in response.json()["detail"]["message"]

        # Empty UID
        response = client.get("/data/item/   ")
        assert response.status_code == 422

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_get_item_plone_error(self, mock_cache, mock_plone_client, client):
        """Test handling of Plone errors in get item."""
        # Mock cache miss
        mock_cache.return_value = None

        # Mock Plone client to raise exception
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.side_effect = Exception("Database error")
        mock_plone_client.return_value = mock_client_instance

        # Make request
        response = client.get("/data/item/test-uid")

        # Should return 500 error
        assert response.status_code == 500
        assert "internal_error" in response.json()["detail"]["error"]


class TestRateLimiting:
    """Test rate limiting functionality."""

    def setup_method(self):
        """Clear rate limiter state before each test."""
        from src.eduhub.open_data.rate_limit import get_rate_limiter
        rate_limiter = get_rate_limiter()
        rate_limiter.requests.clear()  # Clear all IP request tracking

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch(
        "src.eduhub.open_data.rate_limit.OPEN_DATA_RATE_LIMIT", 2
    )  # Very low limit for testing
    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_rate_limiting_enforcement(
        self, mock_cache, mock_plone_client, client
    ):
        """Test that rate limiting is enforced."""
        # Mock cache miss to force backend calls
        mock_cache.return_value = None

        # Mock Plone client
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = {
            "items": [],
            "items_total": 0,
        }
        mock_plone_client.return_value = mock_client_instance

        # Make requests up to the limit
        for i in range(2):
            response = client.get("/data/items")
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.get("/data/items")
        assert response.status_code == 429
        assert "rate_limit_exceeded" in response.json()["detail"]["error"]

        # Check retry-after header
        assert "Retry-After" in response.headers


class TestCaching:
    """Test caching functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @patch("src.eduhub.open_data.endpoints.cache_response")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    @patch("src.eduhub.open_data.endpoints.PloneClient")
    async def test_cache_miss_and_set(
        self, mock_plone_client, mock_get_cache, mock_set_cache, client
    ):
        """Test cache miss leads to cache set."""
        # Mock cache miss
        mock_get_cache.return_value = None

        # Mock Plone client
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = {
            "items": [],
            "items_total": 0,
        }
        mock_plone_client.return_value = mock_client_instance

        # Make request
        response = client.get("/data/items")

        # Should be successful
        assert response.status_code == 200

        # Cache should be called to set the result
        mock_set_cache.assert_called_once()

        # Verify cache key and TTL
        call_args = mock_set_cache.call_args
        cache_key = call_args[0][0]
        ttl = call_args[1]["ttl"]

        assert "items:" in cache_key
        assert ttl == 3600  # 1 hour default


# Fixtures for pagination edge cases
@pytest.fixture
def pagination_edge_cases():
    """Fixture for pagination edge case testing."""
    return [
        # Case 1: Empty result set
        {"items": [], "items_total": 0},
        # Case 2: Single page result
        {
            "items": [
                {
                    "UID": "single-page-uid",
                    "title": "Single Page Document",
                    "@type": "Document",
                    "@id": "https://example.com/single-page",
                    "review_state": "published",
                    "exclude_from_nav": False,
                }
            ],
            "items_total": 1,
        },
        # Case 3: Exact page boundary
        {
            "items": [
                {
                    "UID": f"boundary-uid-{i}",
                    "title": f"Boundary Document {i}",
                    "@type": "Document",
                    "@id": f"https://example.com/boundary-{i}",
                    "review_state": "published",
                    "exclude_from_nav": False,
                }
                for i in range(25)  # Exactly one page
            ],
            "items_total": 25,
        },
    ]


@pytest.mark.parametrize("edge_case_index", [0, 1, 2])
class TestPaginationEdgeCases(TestOpenDataEndpoints):
    """Test pagination edge cases."""

    @patch("src.eduhub.open_data.endpoints.PloneClient")
    @patch("src.eduhub.open_data.endpoints.get_cached_response")
    async def test_pagination_edge_case(
        self,
        mock_cache,
        mock_plone_client,
        client,
        pagination_edge_cases,
        edge_case_index,
    ):
        """Test various pagination edge cases."""
        # Mock cache miss
        mock_cache.return_value = None

        # Mock Plone client with edge case data
        mock_client_instance = AsyncMock()
        mock_client_instance.search_content.return_value = pagination_edge_cases[
            edge_case_index
        ]
        mock_plone_client.return_value = mock_client_instance

        # Make request
        response = client.get("/data/items")

        # Should always succeed
        assert response.status_code == 200
        data = response.json()

        # Verify pagination metadata
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data
        assert "next_cursor" in data

        # Verify has_more logic
        expected_has_more = data["total"] > (data["offset"] + len(data["items"]))
        assert data["has_more"] == expected_has_more
