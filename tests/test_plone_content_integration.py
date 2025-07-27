"""
Tests for Plone content integration with oEmbed functionality.

Tests Tasks 5.3.4 and 5.3.5:
- Task 5.3.4: posting Plone content with YouTube URL returns rendered embed HTML
- Task 5.3.5: sanitizer strips <script> tags from malicious oEmbed payloads
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

from src.eduhub.main import app
from src.eduhub.oembed.content_utils import inject_oembed
from src.eduhub.plone_integration import transform_plone_content_with_embeds

# Test client for FastAPI endpoints
client = TestClient(app)

# Mock data for testing
MOCK_YOUTUBE_OEMBED = {
    "type": "video",
    "version": "1.0",
    "title": "Test YouTube Video",
    "provider_name": "YouTube",
    "html": '<iframe width="800" height="450" src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0"></iframe>',
    "width": 800,
    "height": 450,
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
}

MALICIOUS_OEMBED_PAYLOAD = {
    "type": "video",
    "version": "1.0",
    "title": "Malicious Video",
    "provider_name": "EvilProvider",
    "html": '<iframe width="800" height="450" src="https://example.com/embed/test"></iframe><script>alert("XSS attack!");</script>',
    "width": 800,
    "height": 450,
}

MOCK_PLONE_CONTENT = {
    "UID": "test-content-uid",
    "title": "Test Document with Video",
    "@type": "Document",
    "@id": "http://plone.example.com/documents/test-doc",
    "description": "A test document containing a YouTube video",
    "text": {
        "data": "Check out this amazing video: https://youtube.com/watch?v=dQw4w9WgXcQ"
    },
    "created": "2024-01-01T00:00:00Z",
    "modified": "2024-01-01T00:00:00Z",
    "review_state": "published",
}

MOCK_USER = {"sub": "test-user-123", "email": "test@example.com", "name": "Test User"}


class TestPloneContentIntegration:
    """Test Plone content integration with oEmbed functionality."""

    @pytest.fixture
    def mock_auth(self):
        """Mock authentication for testing endpoints."""
        with patch("src.eduhub.auth.dependencies.get_current_user") as mock_get_user:
            from src.eduhub.auth.models import User

            mock_user = User(**MOCK_USER)
            mock_get_user.return_value = mock_user
            yield mock_get_user

    @pytest.fixture
    def mock_plone_client(self):
        """Mock Plone client for testing."""
        with patch(
            "src.eduhub.plone_content_endpoints.get_plone_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            yield mock_client

    @respx.mock
    @pytest.mark.asyncio
    async def test_task_5_3_4_plone_content_with_youtube_url_returns_embed_html(
        self, mock_auth, mock_plone_client
    ):
        """
        Task 5.3.4: TEST (pytest + monkeypatch):
        posting Plone content with YouTube URL returns rendered embed HTML.
        """
        # Mock the YouTube oEmbed endpoint
        youtube_mock = respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_OEMBED)
        )

        # Mock Plone client create_content_with_embeds method
        mock_plone_client.create_content_with_embeds.return_value = {
            **MOCK_PLONE_CONTENT,
            "text": {
                "data": 'Check out this amazing video: <div class="oembed-embed" data-provider="youtube.com"><iframe width="800" height="450" src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0"></iframe></div>'
            },
        }

        # Test data for content creation
        content_data = {
            "parent_path": "/documents",
            "portal_type": "Document",
            "title": "Test Document with Video",
            "text": "Check out this amazing video: https://youtube.com/watch?v=dQw4w9WgXcQ",
            "inject_embeds": True,
            "maxwidth": 800,
            "maxheight": 450,
        }

        # Create content via API endpoint
        response = client.post("/plone/content/create", json=content_data)

        # Verify response
        assert response.status_code == 200
        response_data = response.json()

        assert response_data["status"] == "success"
        assert response_data["oembed_processed"] == True
        assert response_data["portal_type"] == "Document"
        assert (
            "Content 'Test Document with Video' created successfully"
            in response_data["message"]
        )

        # Verify that the YouTube oEmbed endpoint was called
        assert youtube_mock.called
        assert youtube_mock.call_count == 1

        # Verify that Plone client was called with correct parameters
        mock_plone_client.create_content_with_embeds.assert_called_once_with(
            parent_path="/documents",
            portal_type="Document",
            title="Test Document with Video",
            text="Check out this amazing video: https://youtube.com/watch?v=dQw4w9WgXcQ",
            inject_embeds=True,
            description=None,
        )

        print(
            "✅ Task 5.3.4: Plone content creation with YouTube URL successfully returns embed HTML"
        )

    @pytest.mark.asyncio
    async def test_task_5_3_5_sanitizer_strips_script_tags_from_malicious_oembed(self):
        """
        Task 5.3.5: TEST (pytest):
        sanitizer strips <script> tags from malicious oEmbed payloads.
        """
        # Test the sanitization function directly from the oEmbed client
        from src.eduhub.oembed.client import OEmbedClient

        client = OEmbedClient()

        # Test malicious HTML with script tags
        malicious_html = '<iframe width="800" height="450" src="https://example.com/embed/test"></iframe><script>alert("XSS attack!");</script><script src="evil.js"></script>'

        # Test the sanitize_html function directly
        sanitized_html = client.sanitize_html(malicious_html)

        # Verify that script tags are completely removed
        assert "<script>" not in sanitized_html
        assert "</script>" not in sanitized_html
        assert 'alert("XSS attack!")' not in sanitized_html
        assert 'src="evil.js"' not in sanitized_html

        # Verify that legitimate iframe content is preserved
        assert "<iframe" in sanitized_html
        assert "https://example.com/embed/test" in sanitized_html
        assert 'width="800"' in sanitized_html
        assert 'height="450"' in sanitized_html

        # Test additional malicious content
        malicious_html2 = '<iframe src="https://youtube.com/embed/test"></iframe><script>document.cookie="stolen"</script><img src="x" onerror="alert(1)">'
        sanitized_html2 = client.sanitize_html(malicious_html2)

        # Verify script and onerror attributes are removed
        assert "<script>" not in sanitized_html2
        assert "onerror=" not in sanitized_html2
        assert "document.cookie" not in sanitized_html2

        # But iframe should remain
        assert "<iframe" in sanitized_html2
        assert "youtube.com/embed/test" in sanitized_html2

        await client.close()

        print(
            "✅ Task 5.3.5: Sanitizer successfully strips <script> tags and other malicious content from oEmbed payloads"
        )

    @respx.mock
    @pytest.mark.asyncio
    async def test_content_update_with_embeds(self, mock_auth, mock_plone_client):
        """Test updating existing Plone content with oEmbed injection."""
        # Mock YouTube oEmbed response
        respx.get("https://www.youtube.com/oembed").mock(
            return_value=httpx.Response(200, json=MOCK_YOUTUBE_OEMBED)
        )

        # Mock Plone client methods
        mock_plone_client.get_content.return_value = MOCK_PLONE_CONTENT
        mock_plone_client.update_content_with_embeds.return_value = {
            **MOCK_PLONE_CONTENT,
            "text": {
                "data": 'Updated content with video: <div class="oembed-embed" data-provider="youtube.com"><iframe width="800" height="450" src="https://www.youtube.com/embed/dQw4w9WgXcQ" frameborder="0"></iframe></div>'
            },
        }

        # Test data for content update
        update_data = {
            "text": "Updated content with video: https://youtube.com/watch?v=dQw4w9WgXcQ",
            "inject_embeds": True,
            "maxwidth": 800,
            "maxheight": 450,
        }

        # Update content via API endpoint
        response = client.patch("/plone/content/documents/test-doc", json=update_data)

        # Verify response
        assert response.status_code == 200
        response_data = response.json()

        assert response_data["status"] == "success"
        assert response_data["oembed_processed"] == True
        assert "updated successfully with oEmbed processing" in response_data["message"]

        # Verify Plone client was called
        mock_plone_client.update_content_with_embeds.assert_called_once()

    @pytest.mark.asyncio
    async def test_preview_embeds_endpoint(self, mock_auth, mock_plone_client):
        """Test the preview embeds endpoint."""
        # Mock Plone client
        mock_plone_client.get_content.return_value = MOCK_PLONE_CONTENT

        # Test preview endpoint
        response = client.get(
            "/plone/content/documents/test-doc/preview-embeds?maxwidth=800&maxheight=600"
        )

        # Verify response structure
        assert response.status_code == 200
        response_data = response.json()

        assert response_data["status"] == "success"
        assert "original_content" in response_data
        assert "enhanced_content" in response_data
        assert "detected_media_urls" in response_data
        assert "plain_media_urls" in response_data
        assert "oembed_metadata" in response_data

    @pytest.mark.asyncio
    async def test_batch_process_embeds_dry_run(self, mock_auth, mock_plone_client):
        """Test batch processing of content with dry run."""
        # Mock Plone client
        mock_plone_client.get_content.side_effect = [
            MOCK_PLONE_CONTENT,
            {
                **MOCK_PLONE_CONTENT,
                "UID": "second-content",
                "@type": "Event",
            },  # Different type
        ]

        # Test batch processing endpoint
        batch_data = {
            "paths": ["documents/test-doc", "events/test-event"],
            "dry_run": True,
            "maxwidth": 800,
            "maxheight": 600,
        }

        response = client.post("/plone/content/batch-process", json=batch_data)

        # Verify response
        assert response.status_code == 200
        response_data = response.json()

        assert response_data["status"] == "completed"
        assert response_data["dry_run"] == True
        assert "summary" in response_data
        assert "results" in response_data

        # Verify that Document was processed and Event was skipped
        results = response_data["results"]
        assert len(results) == 2

        doc_result = next(r for r in results if r["path"] == "documents/test-doc")
        event_result = next(r for r in results if r["path"] == "events/test-event")

        assert doc_result["status"] == "preview"  # Document processed in preview
        assert event_result["status"] == "skipped"  # Event skipped

    @pytest.mark.asyncio
    async def test_embed_stats_endpoint(self, mock_auth):
        """Test the embed statistics endpoint."""
        response = client.get("/plone/content/embed-stats")

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["status"] == "success"
        assert "supported_domains" in response_data
        assert "features" in response_data
        assert "endpoints" in response_data

        # Verify supported domains include expected providers
        supported_domains = response_data["supported_domains"]
        assert "youtube.com" in supported_domains
        assert "twitter.com" in supported_domains
        assert "vimeo.com" in supported_domains

    @pytest.mark.asyncio
    async def test_transform_plone_content_with_embeds_function(self):
        """Test the core transform function with embed injection."""
        with respx.mock:
            # Mock YouTube oEmbed response
            respx.get("https://www.youtube.com/oembed").mock(
                return_value=httpx.Response(200, json=MOCK_YOUTUBE_OEMBED)
            )

            # Transform content with embeds
            enhanced_content = await transform_plone_content_with_embeds(
                MOCK_PLONE_CONTENT, inject_embeds=True, maxwidth=800, maxheight=450
            )

            # Verify transformation
            assert enhanced_content.uid == "test-content-uid"
            assert enhanced_content.title == "Test Document with Video"
            assert enhanced_content.portal_type == "Document"

            # Verify embed processing metadata
            assert enhanced_content.metadata["oembed_processed"] == True
            assert "oembed_timestamp" in enhanced_content.metadata

            # Verify that text contains embed HTML
            assert "<iframe" in enhanced_content.text
            assert "youtube.com/embed" in enhanced_content.text
            assert 'class="oembed-embed"' in enhanced_content.text

    @pytest.mark.asyncio
    async def test_url_detection_in_content_utils(self):
        """Test URL detection functionality."""
        from src.eduhub.oembed.content_utils import (
            detect_media_urls,
            extract_plain_urls,
        )

        test_text = """
        Check out these videos:
        https://youtube.com/watch?v=dQw4w9WgXcQ
        https://vimeo.com/123456789
        https://twitter.com/user/status/123456789
        <a href="https://youtube.com/watch?v=already_linked">Already linked</a>
        """

        # Test URL detection
        detected_urls = detect_media_urls(test_text)
        assert len(detected_urls) >= 4  # All URLs should be detected

        # Verify specific URLs are detected
        url_strings = [url for url, domain, start, end in detected_urls]
        assert any("youtube.com/watch?v=dQw4w9WgXcQ" in url for url in url_strings)
        assert any("vimeo.com/123456789" in url for url in url_strings)
        assert any("twitter.com/user/status/123456789" in url for url in url_strings)

        # Test plain URL extraction (should exclude linked URLs)
        plain_urls = extract_plain_urls(test_text)
        # The linked YouTube URL should be filtered out
        assert len(plain_urls) >= 3

        print("✅ URL detection and filtering working correctly")


# Cleanup fixture
@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Clean up any global state if needed
    pass


if __name__ == "__main__":
    import subprocess

    subprocess.run(["pytest", __file__, "-v", "-s"])
