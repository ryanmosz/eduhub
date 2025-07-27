"""
Alert-specific Rate Limiting

Extends the existing rate limiting infrastructure to handle alerts module requirements:
- REST endpoint rate limiting (20 req/min per IP)
- WebSocket message rate limiting (10 msg/sec per connection)
"""

import time
from collections import defaultdict, deque
from functools import wraps
from typing import Deque, Dict, Optional

from fastapi import HTTPException, Request, status, WebSocket

from ..auth.rate_limiting import RateLimiter, get_client_ip
from .monitoring import record_rate_limit_exceeded


class AlertRateLimiter(RateLimiter):
    """
    Enhanced rate limiter specifically for alerts module.
    
    Extends the base RateLimiter with WebSocket connection-specific tracking
    and alert-optimized configurations.
    """
    
    def __init__(self):
        super().__init__()
        # WebSocket connection-specific tracking
        self.websocket_requests: Dict[str, Deque[float]] = defaultdict(deque)
    
    def is_websocket_allowed(
        self, 
        connection_id: str, 
        max_messages: int = 10, 
        window_seconds: int = 1
    ) -> bool:
        """
        Check if WebSocket message is allowed based on rate limit.
        
        Args:
            connection_id: WebSocket connection identifier
            max_messages: Maximum messages allowed in window  
            window_seconds: Time window in seconds
            
        Returns:
            bool: True if message is allowed, False otherwise
        """
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Get message history for this connection
        connection_messages = self.websocket_requests[connection_id]
        
        # Remove old messages outside the window
        while connection_messages and connection_messages[0] < window_start:
            connection_messages.popleft()
        
        # Check if adding this message would exceed limit
        if len(connection_messages) >= max_messages:
            return False
        
        # Add current message
        connection_messages.append(current_time)
        return True
    
    def get_websocket_reset_time(
        self, 
        connection_id: str, 
        window_seconds: int = 1
    ) -> float:
        """
        Get time when WebSocket rate limit will reset for connection.
        
        Args:
            connection_id: WebSocket connection identifier
            window_seconds: Time window in seconds
            
        Returns:
            float: Unix timestamp when limit resets
        """
        connection_messages = self.websocket_requests[connection_id]
        if not connection_messages:
            return time.time()
        
        # Oldest message + window duration = reset time
        return connection_messages[0] + window_seconds
    
    def cleanup_websocket_entries(self, max_age_seconds: int = 3600):
        """
        Clean up old WebSocket entries to prevent memory bloat.
        
        Args:
            max_age_seconds: Remove connections with no messages in this timeframe
        """
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds
        
        # Find connections to remove
        connections_to_remove = []
        for connection_id, messages in self.websocket_requests.items():
            if not messages or messages[-1] < cutoff_time:
                connections_to_remove.append(connection_id)
        
        # Remove old connections
        for connection_id in connections_to_remove:
            del self.websocket_requests[connection_id]
    
    def remove_websocket_connection(self, connection_id: str):
        """
        Remove all rate limiting data for a WebSocket connection.
        
        Args:
            connection_id: WebSocket connection identifier to remove
        """
        if connection_id in self.websocket_requests:
            del self.websocket_requests[connection_id]


# Global alert rate limiter instance
alert_rate_limiter = AlertRateLimiter()


def alert_rest_rate_limit(max_requests: int = 20, window_seconds: int = 60):
    """
    Rate limiting decorator for alert REST endpoints.
    
    Default: 20 requests per minute per IP (as specified in task 8.4.1).
    
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
            
            # Check rate limit using alert-specific limiter
            if not alert_rate_limiter.is_allowed(client_ip, max_requests, window_seconds):
                reset_time = alert_rate_limiter.get_reset_time(client_ip, window_seconds)
                retry_after = int(reset_time - time.time())
                
                # Record rate limit violation
                record_rate_limit_exceeded('rest', client_ip)
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Alert endpoint rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def check_websocket_rate_limit(
    connection_id: str,
    max_messages: int = 10,
    window_seconds: int = 1
) -> bool:
    """
    Check if WebSocket message sending is allowed for a connection.
    
    Default: 10 messages per second per connection (as specified in task 8.4.1).
    
    Args:
        connection_id: WebSocket connection identifier
        max_messages: Maximum messages allowed in window
        window_seconds: Time window in seconds
        
    Returns:
        bool: True if message is allowed, False if rate limited
    """
    return alert_rate_limiter.is_websocket_allowed(
        connection_id, max_messages, window_seconds
    )


async def get_websocket_retry_after(
    connection_id: str,
    window_seconds: int = 1
) -> float:
    """
    Get the time until WebSocket rate limit resets for a connection.
    
    Args:
        connection_id: WebSocket connection identifier
        window_seconds: Time window in seconds
        
    Returns:
        float: Seconds until rate limit resets
    """
    reset_time = alert_rate_limiter.get_websocket_reset_time(connection_id, window_seconds)
    return max(0, reset_time - time.time())


def cleanup_alert_rate_limiter():
    """
    Clean up old rate limiter entries to prevent memory leaks.
    Should be called periodically in production.
    """
    alert_rate_limiter.cleanup_old_entries()
    alert_rate_limiter.cleanup_websocket_entries()


def remove_websocket_rate_limiting(connection_id: str):
    """
    Remove rate limiting data for a disconnected WebSocket connection.
    
    Args:
        connection_id: WebSocket connection identifier to clean up
    """
    alert_rate_limiter.remove_websocket_connection(connection_id)


# Rate limiting configuration constants
ALERT_REST_MAX_REQUESTS = 20  # requests per minute per IP
ALERT_REST_WINDOW_SECONDS = 60  # 1 minute window

WEBSOCKET_MAX_MESSAGES = 10  # messages per second per connection  
WEBSOCKET_WINDOW_SECONDS = 1  # 1 second window
