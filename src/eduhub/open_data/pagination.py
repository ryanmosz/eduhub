"""
Pagination utilities for Open Data API.

Provides cursor-based pagination for better performance than offset/limit,
especially for large datasets.
"""

import base64
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def create_cursor(offset: int, timestamp: Optional[str] = None) -> str:
    """
    Create an opaque cursor for pagination.

    The cursor encodes the offset position and optionally a timestamp
    for stable pagination even when data changes.

    Args:
        offset: Current offset position in the result set
        timestamp: Optional timestamp for pagination stability

    Returns:
        Base64-encoded cursor string
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    cursor_data = {"offset": offset, "timestamp": timestamp}

    # Encode as JSON then base64 for opacity
    cursor_json = json.dumps(cursor_data, separators=(",", ":"))
    cursor_bytes = cursor_json.encode("utf-8")
    cursor_b64 = base64.b64encode(cursor_bytes).decode("ascii")

    return cursor_b64


def parse_cursor(cursor: str) -> tuple[int, Optional[str]]:
    """
    Parse an opaque cursor to extract pagination information.

    Args:
        cursor: Base64-encoded cursor string

    Returns:
        Tuple of (offset, timestamp)

    Raises:
        ValueError: If cursor is malformed or invalid
    """
    try:
        # Decode from base64 then JSON
        cursor_bytes = base64.b64decode(cursor.encode("ascii"))
        cursor_json = cursor_bytes.decode("utf-8")
        cursor_data = json.loads(cursor_json)

        # Validate cursor structure
        if not isinstance(cursor_data, dict):
            raise ValueError("Cursor data must be a dictionary")

        if "offset" not in cursor_data:
            raise ValueError("Cursor missing required 'offset' field")

        offset = cursor_data["offset"]
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Cursor offset must be a non-negative integer")

        timestamp = cursor_data.get("timestamp")

        return offset, timestamp

    except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning(f"Invalid cursor format: {e}")
        raise ValueError(f"Invalid cursor format: {e}")


def calculate_pagination_info(
    total_items: int, current_offset: int, limit: int, items_returned: int
) -> dict[str, Any]:
    """
    Calculate pagination metadata for API responses.

    Args:
        total_items: Total number of items available
        current_offset: Current starting position
        limit: Requested number of items per page
        items_returned: Actual number of items in current response

    Returns:
        Dictionary with pagination metadata
    """
    # If we got fewer items than requested, there are no more items
    if items_returned < limit:
        has_more = False
        next_offset = None
    else:
        # Check if there are more items beyond current page
        has_more = (current_offset + limit) < total_items
        next_offset = current_offset + limit if has_more else None

    return {
        "total": total_items,
        "limit": limit,
        "offset": current_offset,
        "has_more": has_more,
        "next_cursor": create_cursor(next_offset) if next_offset is not None else None,
    }


def build_plone_search_params(
    search: Optional[str] = None,
    portal_type: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
    **additional_filters,
) -> dict[str, Any]:
    """
    Build search parameters for Plone API calls.

    Translates Open Data API parameters into Plone search parameters.

    Args:
        search: Search query string
        portal_type: Content type filter
        limit: Number of results to return
        offset: Starting position
        additional_filters: Any additional search parameters

    Returns:
        Dictionary of Plone search parameters
    """
    params = {
        "b_size": limit,
        "b_start": offset,
        # Only include published content
        "review_state": ["published", "public"],
        # Sort by modification date for consistency
        "sort_on": "modified",
        "sort_order": "descending",
    }

    if search:
        params["SearchableText"] = search

    if portal_type:
        params["portal_type"] = [portal_type]

    # Add any additional filters
    params.update(additional_filters)

    return params


async def paginated_search(
    plone_client,
    cursor: Optional[str] = None,
    limit: int = 25,
    search: Optional[str] = None,
    portal_type: Optional[str] = None,
    **additional_filters,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Perform paginated search against Plone API.

    Args:
        plone_client: PloneClient instance
        cursor: Pagination cursor (if continuing from previous page)
        limit: Number of results per page
        search: Search query string
        portal_type: Content type filter
        additional_filters: Additional search parameters

    Returns:
        Tuple of (search_results, pagination_info)
    """
    # Parse cursor to get offset
    offset = 0
    if cursor:
        try:
            offset, _ = parse_cursor(cursor)
        except ValueError as e:
            logger.warning(f"Invalid cursor provided: {e}")
            # Start from beginning if cursor is invalid
            offset = 0

    # Build Plone search parameters
    search_params = build_plone_search_params(
        search=search,
        portal_type=portal_type,
        limit=limit,
        offset=offset,
        **additional_filters,
    )

    try:
        # Execute search via Plone client
        plone_response = await plone_client.search_content(**search_params)

        # Extract results and metadata
        items = plone_response.get("items", [])
        total = plone_response.get("items_total", 0)

        # Calculate pagination info
        pagination_info = calculate_pagination_info(
            total_items=total,
            current_offset=offset,
            limit=limit,
            items_returned=len(items),
        )

        logger.info(
            f"Paginated search returned {len(items)} items (offset={offset}, total={total})"
        )

        return items, pagination_info

    except Exception as e:
        logger.error(f"Error during paginated search: {e}")
        raise


def validate_pagination_params(
    limit: int, cursor: Optional[str] = None
) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.

    Args:
        limit: Requested page size
        cursor: Optional pagination cursor

    Returns:
        Tuple of (validated_limit, offset)

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate limit
    if limit < 1:
        raise ValueError("Limit must be at least 1")
    if limit > 100:
        raise ValueError("Limit cannot exceed 100")

    # Parse cursor for offset
    offset = 0
    if cursor:
        try:
            parsed_offset, _ = parse_cursor(cursor)
            offset = parsed_offset
        except ValueError:
            # Invalid cursor - start from beginning
            logger.warning("Invalid cursor provided, starting from beginning")
            offset = 0

    return limit, offset
