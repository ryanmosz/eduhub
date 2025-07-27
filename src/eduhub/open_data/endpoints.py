"""
FastAPI endpoints for Open Data API.

Provides public read-only access to CMS content with pagination, caching,
and rate limiting. No authentication required but rate limited per IP.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from ..plone_integration import PloneClient
from .cache import cache_response, get_cached_response
from .models import ItemListResponse, ItemPublic, OpenDataError
from .pagination import paginated_search, validate_pagination_params
from .rate_limit import rate_limit_dependency
from .serializers import to_public_item, to_public_items, validate_search_parameters

logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/data",
    tags=["Open Data"],
    responses={
        429: {"model": OpenDataError, "description": "Rate limit exceeded"},
        500: {"model": OpenDataError, "description": "Internal server error"},
    },
)


@router.get(
    "/items",
    response_model=ItemListResponse,
    responses={
        200: {
            "description": "List of public content items",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "uid": "abc123",
                                "title": "Welcome to EduHub",
                                "description": "Learn about our programs",
                                "portal_type": "Document",
                                "url": "https://eduhub.example.com/welcome",
                                "created": "2024-01-15T10:30:00Z",
                                "modified": "2024-01-20T14:45:00Z",
                            }
                        ],
                        "total": 150,
                        "limit": 25,
                        "offset": 0,
                        "has_more": True,
                        "next_cursor": "eyJvZmZzZXQiOjI1LCJ0aW1lc3RhbXAiOiIyMDI0In0=",
                    }
                }
            },
        },
        422: {
            "model": OpenDataError,
            "description": "Invalid query parameters",
            "content": {
                "application/json": {
                    "example": {
                        "error": "invalid_parameters",
                        "message": "Search query must be at least 2 characters",
                        "details": {"parameter": "search", "value": "a"},
                    }
                }
            },
        },
    },
    summary="List public content items",
    description="""
    📚 **Get paginated list of public CMS content**

    Returns published content items with pagination support. All content is public
    and does not require authentication.

    **Rate Limit**: 60 requests per minute per IP address

    **Performance**:
    - Cache hits: ~10ms response time
    - Cache misses: ~50ms response time

    **Pagination**: Use `cursor` parameter to navigate through pages efficiently.
    """,
)
async def list_items(
    request: Request,
    search: Optional[str] = Query(
        None,
        description="Search query for content (minimum 2 characters)",
        example="education",
        min_length=2,
        max_length=100,
    ),
    portal_type: Optional[str] = Query(
        None,
        description="Filter by content type",
        example="Document",
        regex="^(Document|News Item|Event|File|Image|Folder|Collection)$",
    ),
    limit: int = Query(
        25, ge=1, le=100, description="Number of items per page (1-100)", example=25
    ),
    cursor: Optional[str] = Query(
        None,
        description="Pagination cursor for next page",
        example="eyJvZmZzZXQiOjI1LCJ0aW1lc3RhbXAiOiIyMDI0In0=",
    ),
    _rate_limit: None = Depends(rate_limit_dependency),
) -> ItemListResponse:
    """List public content items with pagination and filtering."""

    try:
        # Validate search parameters
        search_params = validate_search_parameters(
            search=search, portal_type=portal_type, limit=limit
        )

        # Validate pagination parameters
        validated_limit, offset = validate_pagination_params(limit, cursor)

        # Create cache key from all parameters
        cache_key = (
            f"items:{search or ''}:{portal_type or ''}:{validated_limit}:{offset}"
        )

        # Try cache first
        cached_result = await get_cached_response(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for key: {cache_key}")
            return ItemListResponse(**cached_result)

        # Cache miss - fetch from Plone
        logger.debug(f"Cache miss for key: {cache_key}")

        # Get Plone client (this will be dependency injected in real implementation)
        plone_client = PloneClient()

        async with plone_client:
            # Perform paginated search
            plone_results, pagination_info = await paginated_search(
                plone_client=plone_client,
                cursor=cursor,
                limit=validated_limit,
                search=search,
                portal_type=portal_type,
            )

            # Convert Plone results to public format
            public_items = to_public_items(plone_results)

            # Build response
            response_data = {"items": public_items, **pagination_info}

            response = ItemListResponse(**response_data)

            # Cache the response
            await cache_response(cache_key, response.model_dump(), ttl=3600)

            logger.info(
                f"Successfully returned {len(public_items)} items for public API"
            )
            return response

    except ValueError as e:
        logger.warning(f"Invalid parameters in list_items: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_parameters",
                "message": str(e),
                "details": {"endpoint": "list_items"},
            },
        )
    except Exception as e:
        logger.error(f"Error in list_items endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An internal error occurred while fetching content",
                "details": {"endpoint": "list_items"},
            },
        )


@router.get(
    "/item/{uid}",
    response_model=ItemPublic,
    responses={
        200: {
            "description": "Public content item details",
            "content": {
                "application/json": {
                    "example": {
                        "uid": "abc123-def456",
                        "title": "Welcome to EduHub",
                        "description": "Learn about our comprehensive educational programs",
                        "portal_type": "Document",
                        "url": "https://eduhub.example.com/welcome",
                        "created": "2024-01-15T10:30:00Z",
                        "modified": "2024-01-20T14:45:00Z",
                        "metadata": {
                            "subject": ["education", "welcome"],
                            "language": "en",
                        },
                    }
                }
            },
        },
        404: {
            "model": OpenDataError,
            "description": "Content item not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "not_found",
                        "message": "Content item with UID 'abc123' not found or not public",
                        "details": {"uid": "abc123"},
                    }
                }
            },
        },
    },
    summary="Get public content item by UID",
    description="""
    🔍 **Get single public content item by unique identifier**

    Returns detailed information for a specific content item if it's published
    and available for public access.

    **Rate Limit**: 60 requests per minute per IP address

    **Performance**:
    - Cache hits: ~5ms response time
    - Cache misses: ~20ms response time
    """,
)
async def get_item(
    uid: str, request: Request, _rate_limit: None = Depends(rate_limit_dependency)
) -> ItemPublic:
    """Get single public content item by UID."""

    try:
        # Validate UID parameter
        if not uid or len(uid.strip()) < 3:
            raise ValueError("UID must be at least 3 characters long")

        uid = uid.strip()

        # Create cache key
        cache_key = f"item:{uid}"

        # Try cache first
        cached_result = await get_cached_response(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for item UID: {uid}")
            return ItemPublic(**cached_result)

        # Cache miss - fetch from Plone
        logger.debug(f"Cache miss for item UID: {uid}")

        # Get Plone client
        plone_client = PloneClient()

        async with plone_client:
            # Search for content by UID
            plone_results = await plone_client.search_content(
                UID=uid, review_state=["published", "public"]
            )

            items = plone_results.get("items", [])

            if not items:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "not_found",
                        "message": f"Content item with UID '{uid}' not found or not public",
                        "details": {"uid": uid},
                    },
                )

            # Get the first (and should be only) item
            plone_item = items[0]

            # Convert to public format
            public_item = to_public_item(plone_item)

            if not public_item:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "not_found",
                        "message": f"Content item with UID '{uid}' not found or not public",
                        "details": {"uid": uid},
                    },
                )

            # Cache the response
            await cache_response(
                cache_key, public_item.model_dump(), ttl=7200
            )  # 2 hours

            logger.info(f"Successfully returned item {uid} for public API")
            return public_item

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logger.warning(f"Invalid UID parameter: {e}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_parameters",
                "message": str(e),
                "details": {"parameter": "uid", "value": uid},
            },
        )
    except Exception as e:
        logger.error(f"Error in get_item endpoint for UID {uid}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_error",
                "message": "An internal error occurred while fetching content item",
                "details": {"uid": uid, "endpoint": "get_item"},
            },
        )
