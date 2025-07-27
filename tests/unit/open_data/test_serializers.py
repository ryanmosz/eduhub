"""
Unit tests for Open Data API serializers.

Tests the conversion of Plone content to public-safe data models.
"""

from unittest.mock import patch

import pytest

from src.eduhub.open_data.models import ItemPublic
from src.eduhub.open_data.serializers import (
    PUBLIC_METADATA_FIELDS,
    PUBLIC_PORTAL_TYPES,
    is_public_content,
    sanitize_metadata,
    to_public_item,
    to_public_items,
    validate_search_parameters,
)


class TestIsPublicContent:
    """Test public content filtering logic."""

    def test_valid_public_content(self):
        """Test that valid public content is accepted."""
        plone_data = {
            "@type": "Document",
            "review_state": "published",
            "exclude_from_nav": False,
        }
        assert is_public_content(plone_data) is True

    def test_invalid_portal_type(self):
        """Test that invalid portal types are rejected."""
        plone_data = {
            "@type": "PrivateType",
            "review_state": "published",
            "exclude_from_nav": False,
        }
        assert is_public_content(plone_data) is False

    def test_private_review_state(self):
        """Test that private content is rejected."""
        plone_data = {
            "@type": "Document",
            "review_state": "private",
            "exclude_from_nav": False,
        }
        assert is_public_content(plone_data) is False

    def test_excluded_from_nav(self):
        """Test that content excluded from nav is rejected."""
        plone_data = {
            "@type": "Document",
            "review_state": "published",
            "exclude_from_nav": True,
        }
        assert is_public_content(plone_data) is False

    def test_portal_type_fallback(self):
        """Test fallback to portal_type field."""
        plone_data = {
            "portal_type": "News Item",
            "review_state": "published",
            "exclude_from_nav": False,
        }
        assert is_public_content(plone_data) is True


class TestSanitizeMetadata:
    """Test metadata sanitization."""

    def test_safe_metadata_fields(self):
        """Test that safe metadata fields are included."""
        plone_data = {
            "subject": ["education", "programming"],
            "language": "en",
            "effective": "2024-01-15T10:30:00Z",
            "secret_field": "should_not_appear",
        }

        result = sanitize_metadata(plone_data)

        assert result["subject"] == ["education", "programming"]
        assert result["language"] == "en"
        assert result["effective"] == "2024-01-15T10:30:00Z"
        assert "secret_field" not in result

    def test_empty_metadata(self):
        """Test with no metadata fields."""
        plone_data = {"title": "Test"}
        result = sanitize_metadata(plone_data)
        assert result == {}

    def test_none_values_excluded(self):
        """Test that None values are excluded."""
        plone_data = {"subject": ["test"], "language": None, "effective": ""}

        result = sanitize_metadata(plone_data)

        assert result["subject"] == ["test"]
        assert "language" not in result
        assert "effective" not in result


class TestToPublicItem:
    """Test conversion to public item model."""

    def test_valid_conversion(self):
        """Test successful conversion of valid Plone data."""
        plone_data = {
            "UID": "abc123-def456",
            "title": "Test Document",
            "description": "Test description",
            "@type": "Document",
            "@id": "https://example.com/test",
            "created": "2024-01-15T10:30:00Z",
            "modified": "2024-01-20T14:45:00Z",
            "review_state": "published",
            "subject": ["test", "education"],
            "language": "en",
            "exclude_from_nav": False,
        }

        result = to_public_item(plone_data)

        assert isinstance(result, ItemPublic)
        assert result.uid == "abc123-def456"
        assert result.title == "Test Document"
        assert result.description == "Test description"
        assert result.portal_type == "Document"
        assert result.url == "https://example.com/test"
        assert result.created == "2024-01-15T10:30:00Z"
        assert result.modified == "2024-01-20T14:45:00Z"
        assert result.metadata["subject"] == ["test", "education"]
        assert result.metadata["language"] == "en"

    def test_private_content_returns_none(self):
        """Test that private content returns None."""
        plone_data = {
            "UID": "private123",
            "title": "Private Document",
            "@type": "Document",
            "@id": "https://example.com/private",
            "review_state": "private",
            "exclude_from_nav": False,
        }

        result = to_public_item(plone_data)
        assert result is None

    def test_missing_required_fields(self):
        """Test that missing required fields raise ValueError."""
        # Missing UID
        plone_data = {
            "title": "Test",
            "@type": "Document",
            "@id": "https://example.com/test",
            "review_state": "published",
            "exclude_from_nav": False,
        }

        with pytest.raises(ValueError, match="missing required UID field"):
            to_public_item(plone_data)

        # Missing title
        plone_data = {
            "UID": "test123",
            "@type": "Document",
            "@id": "https://example.com/test",
            "review_state": "published",
            "exclude_from_nav": False,
        }

        with pytest.raises(ValueError, match="missing required title field"):
            to_public_item(plone_data)

    def test_optional_fields_handling(self):
        """Test that optional fields are handled correctly."""
        plone_data = {
            "UID": "test123",
            "title": "Test Document",
            # description missing (optional)
            "@type": "Document",
            "@id": "https://example.com/test",
            "review_state": "published",
            "exclude_from_nav": False,
        }

        result = to_public_item(plone_data)

        assert result is not None
        assert result.description is None
        assert result.created is None
        assert result.modified is None


class TestToPublicItems:
    """Test bulk conversion of Plone items."""

    def test_mixed_content_filtering(self, caplog):
        """Test that private content is filtered out and logged."""
        # Enable logging for the test
        import logging

        caplog.set_level(logging.INFO)
        plone_results = [
            {
                "UID": "public1",
                "title": "Public Document 1",
                "@type": "Document",
                "@id": "https://example.com/doc1",
                "review_state": "published",
                "exclude_from_nav": False,
            },
            {
                "UID": "private1",
                "title": "Private Document",
                "@type": "Document",
                "@id": "https://example.com/private",
                "review_state": "private",
                "exclude_from_nav": False,
            },
            {
                "UID": "public2",
                "title": "Public Document 2",
                "@type": "News Item",
                "@id": "https://example.com/news1",
                "review_state": "published",
                "exclude_from_nav": False,
            },
        ]

        result = to_public_items(plone_results)

        # Should only return the 2 public items
        assert len(result) == 2
        assert result[0].uid == "public1"
        assert result[1].uid == "public2"

        # Check logging
        assert "Filtered out 1 non-public items" in caplog.text
        assert "Successfully serialized 2 items for public API" in caplog.text

    def test_serialization_errors_handling(self, caplog):
        """Test handling of serialization errors."""
        plone_results = [
            {
                "UID": "valid1",
                "title": "Valid Document",
                "@type": "Document",
                "@id": "https://example.com/valid",
                "review_state": "published",
                "exclude_from_nav": False,
            },
            {
                # Missing required fields - will cause error
                "title": "Invalid Document",
                "@type": "Document",
                "review_state": "published",
                "exclude_from_nav": False,
            },
        ]

        result = to_public_items(plone_results)

        # Should only return the 1 valid item
        assert len(result) == 1
        assert result[0].uid == "valid1"

        # Check error logging
        assert "Failed to serialize 1 items due to errors" in caplog.text

    def test_empty_list(self):
        """Test with empty list."""
        result = to_public_items([])
        assert result == []


class TestValidateSearchParameters:
    """Test search parameter validation."""

    def test_valid_parameters(self):
        """Test validation of valid parameters."""
        result = validate_search_parameters(
            search="python programming", portal_type="Document", limit=25, offset=0
        )

        expected = {
            "search": "python programming",
            "portal_type": "Document",
            "limit": 25,
            "offset": 0,
        }
        assert result == expected

    def test_search_query_validation(self):
        """Test search query validation rules."""
        # Too short
        with pytest.raises(ValueError, match="at least 2 characters"):
            validate_search_parameters(search="a")

        # Too long
        long_query = "x" * 101
        with pytest.raises(ValueError, match="too long"):
            validate_search_parameters(search=long_query)

        # Whitespace handling
        result = validate_search_parameters(search="  python  ")
        assert result["search"] == "python"

    def test_portal_type_validation(self):
        """Test portal type validation."""
        # Valid portal type
        result = validate_search_parameters(portal_type="Document")
        assert result["portal_type"] == "Document"

        # Invalid portal type
        with pytest.raises(ValueError, match="Invalid portal_type"):
            validate_search_parameters(portal_type="InvalidType")

    def test_pagination_validation(self):
        """Test pagination parameter validation."""
        # Invalid limit
        with pytest.raises(ValueError, match="between 1 and 100"):
            validate_search_parameters(limit=0)

        with pytest.raises(ValueError, match="between 1 and 100"):
            validate_search_parameters(limit=101)

        # Invalid offset
        with pytest.raises(ValueError, match="non-negative"):
            validate_search_parameters(offset=-1)

    def test_optional_parameters(self):
        """Test that optional parameters are handled correctly."""
        result = validate_search_parameters(limit=10, offset=20)

        expected = {"limit": 10, "offset": 20}
        assert result == expected
        assert "search" not in result
        assert "portal_type" not in result


# Test fixtures for integration tests
@pytest.fixture
def valid_plone_data():
    """Fixture with valid Plone content data."""
    return {
        "UID": "test-uid-123",
        "title": "Test Document",
        "description": "A test document for unit testing",
        "@type": "Document",
        "portal_type": "Document",
        "@id": "https://example.com/test-document",
        "created": "2024-01-15T10:30:00Z",
        "modified": "2024-01-20T14:45:00Z",
        "review_state": "published",
        "subject": ["testing", "development"],
        "language": "en",
        "effective": "2024-01-15T10:30:00Z",
        "exclude_from_nav": False,
    }


@pytest.fixture
def private_plone_data():
    """Fixture with private Plone content data."""
    return {
        "UID": "private-uid-456",
        "title": "Private Document",
        "description": "A private document",
        "@type": "Document",
        "@id": "https://example.com/private-document",
        "review_state": "private",
        "exclude_from_nav": True,
    }
