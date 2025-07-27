"""
Slack Integration Client for Alert Broadcasting

Provides async Slack API wrapper with exponential backoff, rate limiting,
and comprehensive error handling for reliable team notifications.
"""

import asyncio
import logging
import os
import random
from typing import Any, Dict, List, Optional
from datetime import datetime

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError, SlackClientError

from .models import Alert, AlertPriority
from .monitoring import record_slack_api_call, measure_operation, slack_api_latency_ms

logger = logging.getLogger(__name__)


class SlackRateLimitError(Exception):
    """Raised when Slack rate limits are exceeded."""
    
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Slack rate limit exceeded. Retry after {retry_after} seconds.")


class SlackConfigurationError(Exception):
    """Raised when Slack configuration is invalid."""
    pass


class AlertSlackClient:
    """
    Async Slack client for broadcasting alerts to teams.
    
    Features:
    - Exponential backoff with jitter for rate limiting
    - Automatic retry on transient failures
    - Rich message formatting with attachments
    - Channel and DM support
    - Comprehensive error logging
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise SlackConfigurationError("SLACK_BOT_TOKEN environment variable is required")
        
        self.client = AsyncWebClient(token=self.token)
        self.default_channel = os.getenv("SLACK_DEFAULT_CHANNEL", "#alerts")
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        self.max_delay = 60.0  # seconds
        self.jitter_factor = 0.1
        
        # Priority color mapping
        self.priority_colors = {
            AlertPriority.LOW: "#36A64F",       # Green
            AlertPriority.MEDIUM: "#FFA500",    # Orange  
            AlertPriority.HIGH: "#FF4444",      # Red
            AlertPriority.CRITICAL: "#8B0000"   # Dark red
        }
        
        # Priority emoji mapping
        self.priority_emojis = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🚨",
            AlertPriority.CRITICAL: "🔥"
        }
    
    async def send_alert(
        self, 
        alert: Alert, 
        channel: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an alert to a Slack channel or DM.
        
        Args:
            alert: The alert to send
            channel: Target channel (defaults to alert.slack_channel or default_channel)
            thread_ts: Thread timestamp for threaded replies
            
        Returns:
            Dict containing Slack API response
            
        Raises:
            SlackRateLimitError: When rate limits are exceeded beyond retry attempts
            SlackApiError: When Slack API returns an error
            SlackConfigurationError: When configuration is invalid
        """
        target_channel = channel or alert.slack_channel or self.default_channel
        
        if not target_channel:
            raise SlackConfigurationError("No target channel specified for alert")
        
        # Build message payload
        message_data = self._build_message(alert, target_channel, thread_ts)
        
        # Send with retry logic
        return await self._send_with_retry(message_data)
    
    async def send_simple_message(
        self,
        channel: str,
        text: str,
        priority: AlertPriority = AlertPriority.MEDIUM
    ) -> Dict[str, Any]:
        """
        Send a simple text message to a channel.
        
        Args:
            channel: Target channel
            text: Message text
            priority: Message priority for emoji selection
            
        Returns:
            Dict containing Slack API response
        """
        emoji = self.priority_emojis.get(priority, "ℹ️")
        formatted_text = f"{emoji} {text}"
        
        message_data = {
            "channel": channel,
            "text": formatted_text
        }
        
        return await self._send_with_retry(message_data)
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the Slack connection and token validity.
        
        Returns:
            Dict containing authentication test results
        """
        try:
            response = await self.client.auth_test()
            logger.info(f"Slack connection test successful: {response.get('team')} - {response.get('user')}")
            return {
                "success": True,
                "team": response.get("team"),
                "user": response.get("user"),
                "user_id": response.get("user_id"),
                "team_id": response.get("team_id")
            }
        except SlackApiError as e:
            logger.error(f"Slack connection test failed: {e.response['error']}")
            return {
                "success": False,
                "error": e.response.get("error", "Unknown error"),
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Slack connection test error: {e}")
            return {
                "success": False,
                "error": "connection_error",
                "details": str(e)
            }
    
    async def get_channels(self) -> List[Dict[str, Any]]:
        """
        Get list of available Slack channels.
        
        Returns:
            List of channel information dicts
        """
        try:
            response = await self.client.conversations_list(
                types="public_channel,private_channel"
            )
            channels = response.get("channels", [])
            
            return [
                {
                    "id": channel["id"],
                    "name": channel["name"],
                    "is_private": channel.get("is_private", False),
                    "is_member": channel.get("is_member", False)
                }
                for channel in channels
            ]
        except SlackApiError as e:
            logger.error(f"Failed to get Slack channels: {e.response['error']}")
            return []
    
    def _build_message(
        self, 
        alert: Alert, 
        channel: str, 
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build the Slack message payload for an alert."""
        
        # Get priority styling
        color = self.priority_colors.get(alert.priority, "#36A64F")
        emoji = self.priority_emojis.get(alert.priority, "ℹ️")
        
        # Build main message text
        main_text = f"{emoji} *{alert.title}*"
        
        # Build attachment with rich formatting
        attachment = {
            "color": color,
            "fields": [
                {
                    "title": "Message",
                    "value": alert.message,
                    "short": False
                },
                {
                    "title": "Priority",
                    "value": alert.priority.value.title(),
                    "short": True
                },
                {
                    "title": "Category", 
                    "value": alert.category.value.title(),
                    "short": True
                },
                {
                    "title": "Source",
                    "value": alert.source,
                    "short": True
                },
                {
                    "title": "Created",
                    "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "short": True
                }
            ],
            "footer": "EduHub Alert System",
            "ts": int(alert.created_at.timestamp())
        }
        
        # Add user-specific information if available
        if alert.user_id:
            attachment["fields"].append({
                "title": "Target User",
                "value": alert.user_id,
                "short": True
            })
        
        # Add metadata fields if present
        if alert.metadata:
            metadata_text = []
            for key, value in alert.metadata.items():
                metadata_text.append(f"*{key}*: {value}")
            
            if metadata_text:
                attachment["fields"].append({
                    "title": "Details",
                    "value": "\n".join(metadata_text[:5]),  # Limit to 5 items
                    "short": False
                })
        
        # Build final message payload
        message_data = {
            "channel": channel,
            "text": main_text,
            "attachments": [attachment],
            "unfurl_links": False,
            "unfurl_media": False
        }
        
        # Add thread timestamp if specified
        if thread_ts:
            message_data["thread_ts"] = thread_ts
        
        return message_data
    
    async def _send_with_retry(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send message with exponential backoff retry logic."""
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Log attempt
                if attempt > 0:
                    logger.info(f"Slack API retry attempt {attempt}/{self.max_retries}")
                
                # Make the API call with monitoring
                async with measure_operation(slack_api_latency_ms, {'endpoint': 'chat.postMessage'}):
                    response = await self.client.chat_postMessage(**message_data)
                
                # Record successful API call
                record_slack_api_call('chat.postMessage', 'success', 0)  # Latency recorded by measure_operation
                
                # Success - log and return
                logger.info(f"Slack message sent successfully to {message_data['channel']}")
                return {
                    "success": True,
                    "timestamp": response.get("ts"),
                    "channel": response.get("channel"),
                    "message": response.get("message", {})
                }
                
            except SlackApiError as e:
                last_exception = e
                error_code = e.response.get("error", "unknown_error")
                
                # Handle rate limiting
                if error_code == "rate_limited":
                    retry_after = int(e.response.get("headers", {}).get("Retry-After", 60))
                    
                    # Record rate limit hit
                    record_slack_api_call('chat.postMessage', 'rate_limited', 0)
                    
                    if attempt < self.max_retries:
                        logger.warning(f"Slack rate limit hit. Waiting {retry_after}s before retry {attempt + 1}")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        raise SlackRateLimitError(retry_after)
                
                # Handle server errors (5xx) - retry with backoff
                elif error_code in ["internal_error", "service_unavailable"] or (e.response.get("status") is not None and e.response.get("status") >= 500):
                    # Record server error
                    record_slack_api_call('chat.postMessage', 'server_error', 0)
                    
                    if attempt < self.max_retries:
                        delay = self._calculate_backoff_delay(attempt)
                        logger.warning(f"Slack server error ({error_code}). Retrying in {delay:.2f}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Slack server error after {self.max_retries} retries: {error_code}")
                        raise
                
                # Handle client errors (4xx) - don't retry
                else:
                    # Record client error
                    record_slack_api_call('chat.postMessage', 'client_error', 0)
                    logger.error(f"Slack client error (no retry): {error_code} - {e.response.get('error')}")
                    raise
                    
            except SlackClientError as e:
                last_exception = e
                
                # Network/connection errors - retry with backoff
                if attempt < self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)
                    logger.warning(f"Slack connection error. Retrying in {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Slack connection error after {self.max_retries} retries: {e}")
                    raise
            
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected Slack error: {e}")
                raise
        
        # If we get here, all retries failed
        raise last_exception
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        
        # Exponential backoff: base_delay * 2^attempt
        delay = self.base_delay * (2 ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.max_delay)
        
        # Add jitter to avoid thundering herd
        jitter = delay * self.jitter_factor * (2 * random.random() - 1)
        delay = delay + jitter
        
        # Ensure positive delay
        return max(0.1, delay)
    
    async def close(self):
        """Close the Slack client and clean up resources."""
        if hasattr(self.client, 'close'):
            await self.client.close()
        logger.info("Slack client closed")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get Slack client metrics and configuration."""
        return {
            "token_configured": bool(self.token),
            "default_channel": self.default_channel,
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "priority_colors": self.priority_colors,
            "priority_emojis": self.priority_emojis
        }


# Global Slack client instance (lazy initialization)
_slack_client: Optional[AlertSlackClient] = None


def get_slack_client() -> AlertSlackClient:
    """Get or create the global Slack client instance."""
    global _slack_client
    
    if _slack_client is None:
        try:
            _slack_client = AlertSlackClient()
        except SlackConfigurationError as e:
            logger.warning(f"Slack client not configured: {e}")
            raise
    
    return _slack_client


async def cleanup_slack_client():
    """Clean up the global Slack client."""
    global _slack_client
    
    if _slack_client:
        await _slack_client.close()
        _slack_client = None
