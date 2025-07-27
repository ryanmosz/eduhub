"""
Rate limiting for Open Data API endpoints.

Implements IP-based rate limiting for public endpoints to prevent abuse
while maintaining good performance for legitimate users.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException, Request

from ..auth.rate_limiting import RateLimiter

logger = logging.getLogger(__name__)

# Configuration
OPEN_DATA_RATE_LIMIT = int(
    os.getenv("OPEN_DATA_RATE_LIMIT", "60")
)  # requests per minute
RATE_LIMIT_WINDOW = 60  # 1 minute window

# Global rate limiter instance
_rate_limiter: RateLimiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
        logger.info(
            f"Initialized Open Data API rate limiter: {OPEN_DATA_RATE_LIMIT} req/min"
        )

    return _rate_limiter


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Handles X-Forwarded-For headers for proxy deployments.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address string
    """
    # Check for X-Forwarded-For header (common in proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Use the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Check for X-Real-IP header (common in nginx setups)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client IP
    client_host = request.client.host if request.client else "unknown"
    return client_host


async def check_rate_limit(request: Request) -> None:
    """
    Check if request is within rate limits.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    try:
        # Get client IP
        client_ip = get_client_ip(request)

        # Check rate limit
        rate_limiter = get_rate_limiter()

        # Check if request is allowed (using the existing RateLimiter interface)
        is_allowed = rate_limiter.is_allowed(
            ip_address=client_ip,
            max_requests=OPEN_DATA_RATE_LIMIT,
            window_seconds=RATE_LIMIT_WINDOW,
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip}: "
                f"{OPEN_DATA_RATE_LIMIT} requests in {RATE_LIMIT_WINDOW}s"
            )

            # Calculate retry-after header
            reset_time = rate_limiter.get_reset_time(client_ip, RATE_LIMIT_WINDOW)
            retry_after = max(1, int(reset_time - datetime.utcnow().timestamp()))

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {OPEN_DATA_RATE_LIMIT} requests per minute",
                    "details": {
                        "limit": OPEN_DATA_RATE_LIMIT,
                        "window_seconds": RATE_LIMIT_WINDOW,
                        "retry_after": retry_after,
                    },
                },
                headers={"Retry-After": str(retry_after)},
            )

        # Log successful rate limit check
        logger.debug(
            f"Rate limit check passed for IP {client_ip}: {OPEN_DATA_RATE_LIMIT} requests"
        )

    except HTTPException:
        # Re-raise HTTP exceptions (rate limit exceeded)
        raise
    except Exception as e:
        # Log error but don't block request on rate limit failures
        logger.error(f"Rate limit check error: {e}")
        # Continue processing - fail open for availability


async def rate_limit_dependency(request: Request) -> None:
    """
    FastAPI dependency for rate limiting.

    Use with Depends() in endpoint functions.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    await check_rate_limit(request)


def get_rate_limit_info(request: Request) -> dict[str, Any]:
    """
    Get current rate limit status for a client.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with rate limit information
    """
    try:
        client_ip = get_client_ip(request)
        rate_limiter = get_rate_limiter()

        # Get current usage (approximate - check requests history)
        ip_requests = rate_limiter.requests.get(client_ip, [])
        current_count = len(ip_requests)

        return {
            "limit": OPEN_DATA_RATE_LIMIT,
            "window_seconds": RATE_LIMIT_WINDOW,
            "current_count": current_count,
            "remaining": max(0, OPEN_DATA_RATE_LIMIT - current_count),
            "client_ip": client_ip,
        }
    except Exception as e:
        logger.error(f"Error getting rate limit info: {e}")
        return {
            "limit": OPEN_DATA_RATE_LIMIT,
            "window_seconds": RATE_LIMIT_WINDOW,
            "current_count": 0,
            "remaining": OPEN_DATA_RATE_LIMIT,
            "client_ip": "unknown",
        }
