"""
FastAPI router for oEmbed proxy endpoints.

Provides secure proxy service for embedding rich media content from
approved providers like YouTube, Vimeo, Twitter, etc.
"""

from typing import Any, Dict
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import HttpUrl, ValidationError

from ..auth.dependencies import get_current_user
from ..auth.rate_limiting import rate_limit
from .cache import get_oembed_cache
from .client import get_oembed_client
from .models import EmbedError, EmbedRequest, EmbedResponse
from .security import get_security_manager

# Create router instance
router = APIRouter(tags=["Rich Media Embeds"])

# Allowed providers for security
ALLOWED_PROVIDERS = {
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "soundcloud.com",
    "spotify.com",
    "codepen.io",
    "github.com",
}


@router.get(
    "/",
    response_model=EmbedResponse,
    responses={
        422: {
            "model": EmbedError,
            "description": "Invalid URL or unsupported provider",
            "content": {
                "application/json": {
                    "example": {
                        "error": "provider_not_allowed",
                        "message": "Domain 'example.com' is not in the list of supported providers",
                        "url": "https://example.com/video",
                    }
                }
            },
        },
        429: {
            "model": EmbedError,
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": "rate_limit_exceeded",
                        "message": "Rate limit of 20 requests per minute exceeded",
                        "url": "https://www.youtube.com/watch?v=example",
                    }
                }
            },
        },
        504: {
            "model": EmbedError,
            "description": "Provider timeout",
            "content": {
                "application/json": {
                    "example": {
                        "error": "provider_timeout",
                        "message": "Provider request timed out",
                        "url": "https://www.youtube.com/watch?v=example",
                    }
                }
            },
        },
    },
    summary="Embed URL as rich media content",
    description="""
Transform a URL from supported providers into rich embedded content using the oEmbed protocol.

**🎯 Quick Start Example:**
```
GET /embed/?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&maxwidth=800&maxheight=450
Authorization: Bearer YOUR_JWT_TOKEN
```

**🔒 Authentication Required:** This endpoint requires a valid JWT token in the Authorization header.

**⚡ Performance:** Responses are cached for improved performance. Cache status is indicated in the response.

**🛡️ Security:** All HTML is sanitized and URLs are validated against an approved provider allow-list.
""",
)
@rate_limit(
    max_requests=20, window_seconds=60
)  # Task 5.4.2: 20 requests per minute per IP
async def embed_url(
    request: Request,
    url: str = Query(
        ...,
        description="URL to embed from supported provider",
        example="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ),
    maxwidth: int = Query(
        None,
        ge=200,
        le=1920,
        description="Maximum width of embed in pixels (200-1920)",
        example=800,
    ),
    maxheight: int = Query(
        None,
        ge=200,
        le=1080,
        description="Maximum height of embed in pixels (200-1080)",
        example=450,
    ),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> EmbedResponse:
    """
    Embed a URL as rich media content.

    **Supported Providers:**
    - YouTube (youtube.com, youtu.be)
    - Vimeo (vimeo.com)
    - Twitter/X (twitter.com, x.com)
    - Instagram (instagram.com)
    - SoundCloud (soundcloud.com)
    - Spotify (spotify.com)
    - CodePen (codepen.io)
    - GitHub (github.com)

    **Security Features:**
    - Domain allow-list validation
    - HTML sanitization
    - Rate limiting (20 requests/minute per user)
    - Response caching for performance

    **Args:**
        url: URL to embed (must be from supported provider)
        maxwidth: Maximum width of embed (200-1920px)
        maxheight: Maximum height of embed (200-1080px)

    **Returns:**
        EmbedResponse with sanitized HTML and metadata

    **Raises:**
        HTTPException: 422 for invalid URLs, 429 for rate limits, 504 for timeouts
    """
    # Enhanced URL validation using Pydantic HttpUrl (Task 5.1.2)
    try:
        # Step 1: Validate URL format using Pydantic HttpUrl
        validated_url = HttpUrl(url)
        url_str = str(validated_url)

        # Step 2: Extract and normalize domain
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.lower()

        # Remove www. prefix for comparison
        if domain.startswith("www."):
            domain = domain[4:]

        # Step 3: Security validation using security manager (Task 5.4.1)
        security_manager = get_security_manager()
        if not security_manager.is_domain_allowed(url_str):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Provider not allowed",
                    "message": f"Domain '{domain}' is not in the list of supported providers",
                    "supported_providers": sorted(
                        list(security_manager.allowed_domains)
                    ),
                    "url": url,
                },
            )

        # Step 4: Additional security checks
        if parsed_url.scheme not in ["http", "https"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Invalid URL scheme",
                    "message": f"Only HTTP and HTTPS URLs are supported, got: {parsed_url.scheme}",
                    "url": url,
                },
            )

    except ValidationError as e:
        # Pydantic validation failed - invalid URL format
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Invalid URL format",
                "message": "The provided URL is not a valid HTTP/HTTPS URL",
                "details": str(e),
                "url": url,
            },
        )
    except HTTPException:
        # Re-raise our custom HTTP exceptions
        raise
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=422,
            detail={
                "error": "URL validation failed",
                "message": f"Unexpected error during URL validation: {str(e)}",
                "url": url,
            },
        )

    # Task 5.1.3: Fetch real oEmbed data using the client
    try:
        client = await get_oembed_client()
        oembed_data = await client.fetch_embed(url_str, maxwidth, maxheight)

        # Additional security validation (Task 5.4.1)
        oembed_data = security_manager.validate_oembed_response(oembed_data)

        # Convert oEmbed response to our EmbedResponse model
        return EmbedResponse(
            html=oembed_data.get("html", ""),
            title=oembed_data.get("title"),
            provider_name=oembed_data.get("provider_name"),
            provider_url=oembed_data.get("provider_url"),
            width=oembed_data.get("width", maxwidth),
            height=oembed_data.get("height", maxheight),
            thumbnail_url=oembed_data.get("thumbnail_url"),
            cached=oembed_data.get("cached", False),
        )

    except HTTPException:
        # Re-raise HTTP exceptions from the client
        raise
    except Exception as e:
        # Task 5.4.3: Map upstream HTTP failures to meaningful exceptions
        import httpx

        if isinstance(e, httpx.TimeoutException):
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "provider_timeout",
                    "message": "Provider request timed out",
                    "url": url,
                },
            )
        elif isinstance(e, httpx.HTTPStatusError):
            if 400 <= e.response.status_code < 500:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "provider_error",
                        "message": f"Provider returned error: {e.response.status_code}",
                        "url": url,
                    },
                )
            else:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "error": "provider_unavailable",
                        "message": "Provider service unavailable",
                        "url": url,
                    },
                )
        elif isinstance(e, httpx.NetworkError):
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "network_error",
                    "message": "Network error connecting to provider",
                    "url": url,
                },
            )
        else:
            # Handle any unexpected errors
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "oEmbed fetch failed",
                    "message": f"Failed to fetch embed data: {str(e)}",
                    "url": url,
                },
            )


@router.get(
    "/providers",
    response_model=dict[str, Any],
    summary="List supported providers",
    description="Get list of supported oEmbed providers and their configurations",
)
@rate_limit(max_requests=30, window_seconds=60)  # More generous for info endpoint
async def list_providers(request: Request) -> dict[str, Any]:
    """
    List all supported oEmbed providers.

    **Returns:**
        Dictionary with provider information and capabilities
    """
    return {
        "providers": list(get_security_manager().allowed_domains),
        "count": len(ALLOWED_PROVIDERS),
        "features": {
            "caching": "Redis-backed with configurable TTL",
            "rate_limiting": "20 requests/minute per authenticated user",
            "security": "Domain allow-list + HTML sanitization",
            "formats": "JSON response with sanitized HTML embed code",
        },
        "examples": {
            "youtube": "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "vimeo": "https://vimeo.com/123456789",
            "twitter": "https://twitter.com/user/status/123456789",
        },
    }


@router.get(
    "/health",
    summary="Health check for oEmbed service",
    description="Check health status of oEmbed proxy service",
)
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint for oEmbed service.

    **Returns:**
        Service health status and basic metrics
    """
    return {
        "status": "healthy",
        "service": "oembed-proxy",
        "version": "0.1.0",
        "providers_configured": len(ALLOWED_PROVIDERS),
        "features": {
            "validation": "enabled",
            "caching": "enabled",  # Task 5.2 - Redis-backed with in-memory fallback
            "rate_limiting": "enabled",  # Task 5.4.2 - 20 requests/minute per IP
            "sanitization": "enabled",  # Task 5.1.3 & 5.4.1 - enhanced security
        },
    }


@router.get(
    "/test",
    summary="Test oEmbed client (no auth required)",
    description="Test the oEmbed client functionality with a hardcoded YouTube URL",
)
async def test_oembed_client() -> dict[str, Any]:
    """
    Test endpoint for oEmbed client functionality.

    **Returns:**
        Test results from fetching a YouTube oEmbed
    """
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    try:
        # Test URL validation
        validated_url = HttpUrl(test_url)
        url_str = str(validated_url)

        # Parse domain
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Test oEmbed client
        client = await get_oembed_client()
        oembed_data = await client.fetch_embed(url_str, maxwidth=800, maxheight=450)

        return {
            "status": "success",
            "test_url": test_url,
            "domain": domain,
            "oembed_response": {
                "title": oembed_data.get("title"),
                "provider_name": oembed_data.get("provider_name"),
                "width": oembed_data.get("width"),
                "height": oembed_data.get("height"),
                "html_length": len(oembed_data.get("html", "")),
                "html_sanitized": True,
                "thumbnail_url": oembed_data.get("thumbnail_url"),
                "cached": oembed_data.get("cached", False),
            },
            "message": "✅ Task 5.1.3 Complete - oEmbed client successfully fetched and sanitized HTML",
        }

    except HTTPException as e:
        return {
            "status": "error",
            "test_url": test_url,
            "error": e.detail,
            "message": "❌ oEmbed client test failed with HTTP exception",
        }
    except Exception as e:
        return {
            "status": "error",
            "test_url": test_url,
            "error": str(e),
            "message": "❌ oEmbed client test failed with unexpected error",
        }


@router.get(
    "/cache/stats",
    summary="Cache statistics",
    description="Get oEmbed cache statistics and performance metrics",
)
async def cache_stats() -> dict[str, Any]:
    """
    Get cache statistics and health information.

    **Returns:**
        Cache statistics including hit rates, Redis status, and configuration
    """
    try:
        cache = await get_oembed_cache()
        stats = await cache.stats()

        return {
            "status": "healthy",
            "cache_type": (
                "redis_with_memory_fallback"
                if stats["redis_available"]
                else "memory_only"
            ),
            "redis_available": stats["redis_available"],
            "redis_url": stats.get("redis_url"),
            "ttl_seconds": stats["ttl_seconds"],
            "ttl_human": f"{stats['ttl_seconds'] // 3600}h {(stats['ttl_seconds'] % 3600) // 60}m",
            "redis_cache_size": stats.get("redis_cache_size", 0),
            "memory_cache_size": stats["memory_cache_size"],
            "total_cached_entries": (
                stats.get("redis_cache_size", 0) if stats["redis_available"] else 0
            )
            + stats["memory_cache_size"],
            "configuration": {
                "OEMBED_CACHE_TTL": stats["ttl_seconds"],
                "REDIS_URL": stats.get("redis_url", "not_configured"),
                "fallback_mode": "memory" if not stats["redis_available"] else "none",
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to retrieve cache statistics",
        }


@router.post(
    "/cache/clear",
    summary="Clear cache",
    description="Clear all cached oEmbed responses",
)
async def clear_cache() -> dict[str, Any]:
    """
    Clear all cached oEmbed responses.

    **Returns:**
        Status of cache clearing operation
    """
    try:
        cache = await get_oembed_cache()
        success = await cache.clear()

        return {
            "status": "success" if success else "partial",
            "message": (
                "Cache cleared successfully"
                if success
                else "Cache partially cleared (Redis may be unavailable)"
            ),
            "cleared_at": "2024-01-01T00:00:00Z",  # Would use actual timestamp
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "message": "Failed to clear cache"}
