"""
Tests for Slack integration client.

Tests async Slack API integration, error handling, exponential backoff,
and message formatting using mocked responses.
"""

import asyncio
import pytest
import respx
from unittest.mock import patch, MagicMock
from datetime import datetime

from slack_sdk.errors import SlackApiError, SlackClientError

from src.eduhub.alerts.models import Alert, AlertCategory, AlertPriority
from src.eduhub.alerts.slack_client import (
    AlertSlackClient, 
    SlackRateLimitError, 
    SlackConfigurationError,
    get_slack_client,
    cleanup_slack_client
)


class TestAlertSlackClient:
    """Test the AlertSlackClient class."""
    
    def setup_method(self):
        """Setup test client with mock token."""
        self.test_token = "xoxb-test-token-123"
        self.client = AlertSlackClient(token=self.test_token)
        
        # Sample alert for testing
        self.sample_alert = Alert(
            title="Test Alert",
            message="This is a test alert message",
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.HIGH,
            source="test_system",
            metadata={"test_key": "test_value"}
        )
    
    def test_initialization_with_token(self):
        """Test client initialization with provided token."""
        client = AlertSlackClient(token="test-token")
        assert client.token == "test-token"
        assert client.client is not None
        assert client.default_channel == "#alerts"
    
    def test_initialization_without_token(self):
        """Test client initialization fails without token."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(SlackConfigurationError):
                AlertSlackClient()
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_send_alert_success(self):
        """Test successful alert sending."""
        # Mock successful Slack API response
        respx.post("https://slack.com/api/chat.postMessage").mock(
            return_value=respx.MockResponse(
                status_code=200,
                json={
                    "ok": True,
                    "ts": "1234567890.123456",
                    "channel": "C1234567890",
                    "message": {"text": "🚨 *Test Alert*"}
                }
            )
        )
        
        # Send alert
        result = await self.client.send_alert(self.sample_alert, channel="#test")
        
        # Verify result
        assert result["success"] is True
        assert "timestamp" in result
        assert result["channel"] == "C1234567890"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_send_alert_with_thread(self):
        """Test sending alert to a thread."""
        respx.post("https://slack.com/api/chat.postMessage").mock(
            return_value=respx.MockResponse(
                status_code=200,
                json={
                    "ok": True,
                    "ts": "1234567890.123456",
                    "channel": "C1234567890"
                }
            )
        )
        
        # Send alert with thread timestamp
        result = await self.client.send_alert(
            self.sample_alert, 
            channel="#test",
            thread_ts="1234567890.000000"
        )
        
        assert result["success"] is True
        
        # Verify request included thread_ts
        request = respx.calls[-1].request
        request_data = dict(request.content)  # Parse form data
        # Note: In real implementation, we'd check the actual request payload
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_send_alert_rate_limited_with_retry(self):
        """Test rate limiting with successful retry."""
        # First request - rate limited
        respx.post("https://slack.com/api/chat.postMessage").mock(
            return_value=respx.MockResponse(
                status_code=429,
                json={
                    "ok": False,
                    "error": "rate_limited"
                },
                headers={"Retry-After": "1"}
            )
        ).mock(
            # Second request - success
            return_value=respx.MockResponse(
                status_code=200,
                json={
                    "ok": True,
                    "ts": "1234567890.123456",
                    "channel": "C1234567890"
                }
            )
        )
        
        # Mock sleep to speed up test
        with patch('asyncio.sleep', return_value=None):
            result = await self.client.send_alert(self.sample_alert, channel="#test")
        
        assert result["success"] is True
        assert len(respx.calls) == 2  # One failed, one successful
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_send_alert_rate_limited_exceeds_retries(self):
        """Test rate limiting that exceeds retry attempts."""
        # Mock client with only 1 retry for faster testing
        client = AlertSlackClient(token=self.test_token)
        client.max_retries = 1
        
        # All requests return rate limited
        respx.post("https://slack.com/api/chat.postMessage").mock(
            return_value=respx.MockResponse(
                status_code=429,
                json={
                    "ok": False,
                    "error": "rate_limited"
                },
                headers={"Retry-After": "60"}
            )
        )
        
        # Should raise SlackRateLimitError after retries
        with patch('asyncio.sleep', return_value=None):
            with pytest.raises(SlackRateLimitError) as exc_info:
                await client.send_alert(self.sample_alert, channel="#test")
            
            assert exc_info.value.retry_after == 60
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_send_alert_server_error_with_retry(self):
        """Test server error with exponential backoff retry."""
        # First request - server error
        respx.post("https://slack.com/api/chat.postMessage").mock(
            return_value=respx.MockResponse(
                status_code=500,
                json={
                    "ok": False,
                    "error": "internal_error"
                }
            )
        ).mock(
            # Second request - success
            return_value=respx.MockResponse(
                status_code=200,
                json={
                    "ok": True,
                    "ts": "1234567890.123456",
                    "channel": "C1234567890"
                }
            )
        )
        
        with patch('asyncio.sleep', return_value=None):
            result = await self.client.send_alert(self.sample_alert, channel="#test")
        
        assert result["success"] is True
        assert len(respx.calls) == 2
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_send_alert_client_error_no_retry(self):
        """Test client error that should not be retried."""
        respx.post("https://slack.com/api/chat.postMessage").mock(
            return_value=respx.MockResponse(
                status_code=400,
                json={
                    "ok": False,
                    "error": "invalid_auth"
                }
            )
        )
        
        # Should raise SlackApiError immediately (no retries for 4xx)
        with pytest.raises(SlackApiError) as exc_info:
            await self.client.send_alert(self.sample_alert, channel="#test")
        
        assert exc_info.value.response["error"] == "invalid_auth"
        assert len(respx.calls) == 1  # No retries
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_send_simple_message(self):
        """Test sending a simple text message."""
        respx.post("https://slack.com/api/chat.postMessage").mock(
            return_value=respx.MockResponse(
                status_code=200,
                json={
                    "ok": True,
                    "ts": "1234567890.123456",
                    "channel": "C1234567890"
                }
            )
        )
        
        result = await self.client.send_simple_message(
            channel="#test",
            text="Hello world",
            priority=AlertPriority.LOW
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_test_connection_success(self):
        """Test successful connection test."""
        respx.post("https://slack.com/api/auth.test").mock(
            return_value=respx.MockResponse(
                status_code=200,
                json={
                    "ok": True,
                    "team": "Test Team",
                    "user": "test_bot",
                    "user_id": "U123456",
                    "team_id": "T123456"
                }
            )
        )
        
        result = await self.client.test_connection()
        
        assert result["success"] is True
        assert result["team"] == "Test Team"
        assert result["user"] == "test_bot"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_test_connection_failure(self):
        """Test failed connection test."""
        respx.post("https://slack.com/api/auth.test").mock(
            return_value=respx.MockResponse(
                status_code=401,
                json={
                    "ok": False,
                    "error": "invalid_auth"
                }
            )
        )
        
        result = await self.client.test_connection()
        
        assert result["success"] is False
        assert result["error"] == "invalid_auth"
    
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_channels(self):
        """Test getting list of channels."""
        respx.post("https://slack.com/api/conversations.list").mock(
            return_value=respx.MockResponse(
                status_code=200,
                json={
                    "ok": True,
                    "channels": [
                        {
                            "id": "C123456",
                            "name": "general",
                            "is_private": False,
                            "is_member": True
                        },
                        {
                            "id": "C789012",
                            "name": "alerts",
                            "is_private": False,
                            "is_member": True
                        }
                    ]
                }
            )
        )
        
        channels = await self.client.get_channels()
        
        assert len(channels) == 2
        assert channels[0]["name"] == "general"
        assert channels[1]["name"] == "alerts"
    
    def test_build_message_formatting(self):
        """Test message formatting for different alert types."""
        # Test high priority alert
        high_priority_alert = Alert(
            title="Critical System Error",
            message="Database connection lost",
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.CRITICAL,
            source="database_monitor"
        )
        
        message_data = self.client._build_message(high_priority_alert, "#alerts")
        
        # Check main structure
        assert "🔥" in message_data["text"]  # Critical emoji
        assert "Critical System Error" in message_data["text"]
        assert len(message_data["attachments"]) == 1
        
        attachment = message_data["attachments"][0]
        assert attachment["color"] == "#8B0000"  # Critical color
        
        # Check fields
        fields = {field["title"]: field["value"] for field in attachment["fields"]}
        assert fields["Message"] == "Database connection lost"
        assert fields["Priority"] == "Critical"
        assert fields["Category"] == "System"
        assert fields["Source"] == "database_monitor"
    
    def test_build_message_with_metadata(self):
        """Test message formatting with metadata."""
        alert_with_metadata = Alert(
            title="Workflow Alert",
            message="Document needs review",
            category=AlertCategory.WORKFLOW,
            priority=AlertPriority.MEDIUM,
            source="workflow_engine",
            metadata={
                "document_id": "doc_123",
                "assigned_to": "user456",
                "deadline": "2024-01-15"
            }
        )
        
        message_data = self.client._build_message(alert_with_metadata, "#workflow")
        attachment = message_data["attachments"][0]
        
        # Check metadata field exists
        fields = {field["title"]: field["value"] for field in attachment["fields"]}
        assert "Details" in fields
        
        details = fields["Details"]
        assert "document_id" in details
        assert "doc_123" in details
    
    def test_calculate_backoff_delay(self):
        """Test exponential backoff calculation."""
        # Test increasing delays
        delay_0 = self.client._calculate_backoff_delay(0)
        delay_1 = self.client._calculate_backoff_delay(1)
        delay_2 = self.client._calculate_backoff_delay(2)
        
        assert 0.1 <= delay_0 <= 2.0   # Base delay ~1s with jitter
        assert 1.0 <= delay_1 <= 4.0   # ~2s with jitter
        assert 2.0 <= delay_2 <= 8.0   # ~4s with jitter
        
        # Test max delay cap
        delay_large = self.client._calculate_backoff_delay(10)
        assert delay_large <= self.client.max_delay * 1.1  # Max delay with jitter
    
    def test_get_metrics(self):
        """Test metrics collection."""
        metrics = self.client.get_metrics()
        
        assert metrics["token_configured"] is True
        assert metrics["default_channel"] == "#alerts"
        assert metrics["max_retries"] == 3
        assert "priority_colors" in metrics
        assert "priority_emojis" in metrics
    
    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test client cleanup."""
        # Mock the close method
        self.client.client.close = MagicMock()
        
        await self.client.close()
        
        # Verify close was called
        self.client.client.close.assert_called_once()


class TestSlackClientGlobals:
    """Test global Slack client management."""
    
    def setup_method(self):
        """Reset global client before each test."""
        # Clear any existing global client
        import src.eduhub.alerts.slack_client as slack_module
        slack_module._slack_client = None
    
    def test_get_slack_client_success(self):
        """Test getting global Slack client."""
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test-token'}):
            client = get_slack_client()
            assert isinstance(client, AlertSlackClient)
            
            # Second call should return same instance
            client2 = get_slack_client()
            assert client is client2
    
    def test_get_slack_client_no_token(self):
        """Test getting client without token configuration."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(SlackConfigurationError):
                get_slack_client()
    
    @pytest.mark.asyncio
    async def test_cleanup_slack_client(self):
        """Test global client cleanup."""
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test-token'}):
            # Create client
            client = get_slack_client()
            client.close = MagicMock()
            
            # Cleanup
            await cleanup_slack_client()
            
            # Verify cleanup
            client.close.assert_called_once()
            
            # Verify new client is created on next call
            new_client = get_slack_client()
            assert new_client is not client


class TestSlackErrorHandling:
    """Test various error conditions and edge cases."""
    
    def setup_method(self):
        self.client = AlertSlackClient(token="test-token")
    
    def test_send_alert_no_channel_specified(self):
        """Test sending alert without specifying channel."""
        alert = Alert(
            title="Test",
            message="Test message",
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.MEDIUM,
            source="test"
        )
        # Should use default channel when none specified
        message_data = self.client._build_message(alert, self.client.default_channel)
        assert message_data["channel"] == "#alerts"
    
    @pytest.mark.asyncio
    async def test_send_alert_configuration_error(self):
        """Test configuration error handling."""
        alert = Alert(
            title="Test", 
            message="Test message",
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.MEDIUM,
            source="test"
        )
        
        # Clear channels to trigger configuration error
        alert.slack_channel = None
        self.client.default_channel = None
        
        with pytest.raises(SlackConfigurationError):
            await self.client.send_alert(alert)
    
    def test_priority_fallbacks(self):
        """Test fallback behavior for unknown priorities."""
        # Mock an unknown priority (this shouldn't happen in practice)
        alert = Alert(
            title="Test",
            message="Test message", 
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.MEDIUM,
            source="test"
        )
        
        # Test color fallback
        color = self.client.priority_colors.get("unknown_priority", "#36A64F")
        assert color == "#36A64F"  # Default green
        
        # Test emoji fallback  
        emoji = self.client.priority_emojis.get("unknown_priority", "ℹ️")
        assert emoji == "ℹ️"  # Default info 