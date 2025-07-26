"""
Rate Limiting Middleware for Authentication Endpoints

Provides simple rate limiting functionality to prevent abuse of auth endpoints.
Uses in-memory storage for MVP - in production would use Redis or similar.
"""

import time
from collections import defaultdict, deque
from functools import wraps
from typing import Deque, Dict

from fastapi import HTTPException, Request, status


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.

    In production, this should be replaced with Redis-based rate limiting
    for distributed deployments.
    """

    def __init__(self):
        # Store request timestamps per IP address
        self.requests: dict[str, Deque[float]] = defaultdict(deque)

    def is_allowed(
        self, ip_address: str, max_requests: int = 10, window_seconds: int = 60
    ) -> bool:
        """
        Check if request is allowed based on rate limit.

        Args:
            ip_address: Client IP address
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            bool: True if request is allowed, False otherwise
        """
        current_time = time.time()
        window_start = current_time - window_seconds

        # Get request history for this IP
        ip_requests = self.requests[ip_address]

        # Remove old requests outside the window
        while ip_requests and ip_requests[0] < window_start:
            ip_requests.popleft()

        # Check if adding this request would exceed limit
        if len(ip_requests) >= max_requests:
            return False

        # Add current request
        ip_requests.append(current_time)
        return True

    def get_reset_time(self, ip_address: str, window_seconds: int = 60) -> float:
        """
        Get time when rate limit will reset for IP address.

        Args:
            ip_address: Client IP address
            window_seconds: Time window in seconds

        Returns:
            float: Unix timestamp when limit resets
        """
        ip_requests = self.requests[ip_address]
        if not ip_requests:
            return time.time()

        # Oldest request + window duration = reset time
        return ip_requests[0] + window_seconds

    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """
        Clean up old entries to prevent memory bloat.

        Args:
            max_age_seconds: Remove IPs with no requests in this timeframe
        """
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds

        # Find IPs to remove
        ips_to_remove = []
        for ip, requests in self.requests.items():
            if not requests or requests[-1] < cutoff_time:
                ips_to_remove.append(ip)

        # Remove old IPs
        for ip in ips_to_remove:
            del self.requests[ip]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """
    Decorator for rate limiting FastAPI endpoints.

    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds

    Returns:
        Decorator function
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break

            if not request:
                # No request object found, skip rate limiting
                return await func(*args, **kwargs)

            # Get client IP address
            client_ip = get_client_ip(request)

            # Check rate limit
            if not rate_limiter.is_allowed(client_ip, max_requests, window_seconds):
                reset_time = rate_limiter.get_reset_time(client_ip, window_seconds)
                retry_after = int(reset_time - time.time())

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.

    Handles proxy headers like X-Forwarded-For and X-Real-IP.

    Args:
        request: FastAPI request object

    Returns:
        str: Client IP address
    """
    # Check for forwarded IP (behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


# Periodic cleanup function (call this periodically in production)
def cleanup_rate_limiter():
    """Clean up old rate limiter entries to prevent memory leaks."""
    rate_limiter.cleanup_old_entries()
