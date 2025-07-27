"""
Serializers for transforming Plone content into public Open Data API models.

These functions convert raw Plone API responses into public-safe, validated
Pydantic models that filter out sensitive information.
"""

import logging
from typing import Any, Dict, List, Optional

from .models import ItemPublic

logger = logging.getLogger(__name__)

# Define which portal types are allowed for public access
PUBLIC_PORTAL_TYPES = {
    "Document",
    "News Item",
    "Event",
    "File",
    "Image",
    "Folder",
    "Collection",
}

# Define which metadata fields are safe for public exposure
PUBLIC_METADATA_FIELDS = {
    "subject",
    "language",
    "effective",
    "expires",
    "tags",
    "location",
    "contact_info",
    "event_date",
    "event_location",
}


def is_public_content(plone_data: dict[str, Any]) -> bool:
    """
    Check if Plone content is suitable for public exposure.

    Args:
        plone_data: Raw Plone API response data

    Returns:
        True if content can be publicly exposed, False otherwise
    """
    # Check portal type whitelist
    portal_type = plone_data.get("@type") or plone_data.get("portal_type", "")
    if portal_type not in PUBLIC_PORTAL_TYPES:
        return False

    # Check if content is published/public
    review_state = plone_data.get("review_state", "")
    if review_state not in ["published", "public"]:
        return False

    # Check for private/restricted flags
    if plone_data.get("exclude_from_nav", False):
        return False

    return True


def sanitize_metadata(plone_data: dict[str, Any]) -> dict[str, Any]:
    """
    Extract only public-safe metadata fields from Plone content.

    Args:
        plone_data: Raw Plone API response data

    Returns:
        Dictionary containing only public metadata fields
    """
    metadata = {}

    for field in PUBLIC_METADATA_FIELDS:
        if field in plone_data and plone_data[field]:
            metadata[field] = plone_data[field]

    return metadata


def to_public_item(plone_data: dict[str, Any]) -> Optional[ItemPublic]:
    """
    Transform raw Plone API response into public ItemPublic model.

    This function filters out sensitive information and only includes
    data that is safe for public consumption.

    Args:
        plone_data: Raw Plone API response data

    Returns:
        ItemPublic model instance or None if content should not be public

    Raises:
        ValueError: If required fields are missing or invalid
    """
    try:
        # First check if this content should be public
        if not is_public_content(plone_data):
            logger.debug(
                f"Content {plone_data.get('UID', 'unknown')} not suitable for public access"
            )
            return None

        # Extract required fields
        uid = plone_data.get("UID", "")
        if not uid:
            raise ValueError("Content missing required UID field")

        title = plone_data.get("title", "")
        if not title:
            raise ValueError("Content missing required title field")

        portal_type = plone_data.get("@type") or plone_data.get("portal_type", "")
        if not portal_type:
            raise ValueError("Content missing required portal_type field")

        url = plone_data.get("@id", "")
        if not url:
            raise ValueError("Content missing required @id field")

        # Build the public item
        public_item = ItemPublic(
            uid=uid,
            title=title,
            description=plone_data.get("description") or None,
            portal_type=portal_type,
            url=url,
            created=plone_data.get("created"),
            modified=plone_data.get("modified"),
            metadata=sanitize_metadata(plone_data),
        )

        logger.debug(f"Successfully serialized content {uid} to public format")
        return public_item

    except Exception as e:
        logger.error(f"Error serializing Plone content to public format: {e}")
        logger.debug(f"Problematic content data: {plone_data}")
        raise ValueError(f"Failed to serialize content: {e}")


def to_public_items(plone_results: list[dict[str, Any]]) -> list[ItemPublic]:
    """
    Transform a list of Plone content items into public ItemPublic models.

    Filters out items that should not be public and logs any serialization errors.

    Args:
        plone_results: List of raw Plone API response data

    Returns:
        List of ItemPublic models (may be fewer than input if items filtered out)
    """
    public_items = []
    filtered_count = 0
    error_count = 0

    for plone_data in plone_results:
        try:
            public_item = to_public_item(plone_data)
            if public_item:
                public_items.append(public_item)
            else:
                filtered_count += 1

        except Exception as e:
            error_count += 1
            logger.warning(f"Failed to serialize content item: {e}")
            continue

    if filtered_count > 0:
        logger.info(f"Filtered out {filtered_count} non-public items")
    if error_count > 0:
        logger.warning(f"Failed to serialize {error_count} items due to errors")

    logger.info(f"Successfully serialized {len(public_items)} items for public API")
    return public_items


def validate_search_parameters(
    search: Optional[str] = None,
    portal_type: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Validate and sanitize search parameters for public API.

    Args:
        search: Search query string
        portal_type: Content type filter
        limit: Number of results per page
        offset: Starting position

    Returns:
        Dictionary of validated parameters

    Raises:
        ValueError: If parameters are invalid
    """
    params = {}

    # Validate and sanitize search query
    if search:
        search = search.strip()
        if len(search) < 2:
            raise ValueError("Search query must be at least 2 characters")
        if len(search) > 100:
            raise ValueError("Search query too long (max 100 characters)")
        params["search"] = search

    # Validate portal type
    if portal_type:
        if portal_type not in PUBLIC_PORTAL_TYPES:
            raise ValueError(
                f"Invalid portal_type '{portal_type}'. Allowed types: {list(PUBLIC_PORTAL_TYPES)}"
            )
        params["portal_type"] = portal_type

    # Validate pagination
    if limit < 1 or limit > 100:
        raise ValueError("Limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("Offset must be non-negative")

    params["limit"] = limit
    params["offset"] = offset

    return params
