"""
Tests for unified alert dispatch service.

Tests multi-channel delivery, persistence, deduplication, metrics,
and error handling scenarios.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.eduhub.alerts.models import Alert, AlertChannel, AlertCategory, AlertPriority, AlertRequest
from src.eduhub.alerts.services import AlertDispatchService, AlertDispatchError, AlertDeliveryError


class TestAlertDispatchService:
    """Test the unified alert dispatch service."""
    
    def setup_method(self):
        """Setup test service with mocked dependencies."""
        self.service = AlertDispatchService()
        
        # Sample alert for testing
        self.sample_alert = Alert(
            title="Test Alert",
            message="This is a test alert",
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.HIGH,
            channels=[AlertChannel.WEBSOCKET, AlertChannel.SLACK],
            source="test_system"
        )
    
    @pytest.mark.asyncio
    async def test_initialization_with_redis(self):
        """Test service initialization with Redis available."""
        with patch('redis.asyncio.from_url') as mock_redis, \
             patch('src.eduhub.alerts.services.websocket_manager') as mock_ws_manager, \
             patch('src.eduhub.alerts.services.get_slack_client') as mock_slack:
            
            # Mock Redis connection
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock WebSocket manager
            mock_ws_manager.initialize = AsyncMock()
            
            # Mock Slack client
            mock_slack_client = MagicMock()
            mock_slack.return_value = mock_slack_client
            
            await self.service.initialize()
            
            # Verify initialization
            assert self.service.redis_client is not None
            assert self.service.slack_client is not None
            mock_ws_manager.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialization_without_redis(self):
        """Test service initialization when Redis is unavailable."""
        with patch('redis.asyncio.from_url') as mock_redis, \
             patch('src.eduhub.alerts.services.websocket_manager') as mock_ws_manager:
            
            # Mock Redis connection failure
            mock_redis.return_value.ping.side_effect = Exception("Redis unavailable")
            
            await self.service.initialize()
            
            # Should fallback gracefully
            assert self.service.redis_client is None
    
    @pytest.mark.asyncio
    async def test_dispatch_alert_success_all_channels(self):
        """Test successful alert dispatch to all channels."""
        # Mock dependencies
        self.service._persist_alert = AsyncMock()
        self.service._mark_for_deduplication = AsyncMock()
        self.service._is_duplicate_alert = AsyncMock(return_value=False)
        self.service._dispatch_to_websocket = AsyncMock(return_value=True)
        self.service._dispatch_to_slack = AsyncMock(return_value=True)
        self.service._update_metrics = AsyncMock()
        
        result = await self.service.dispatch_alert(self.sample_alert)
        
        # Verify result
        assert result.status == "delivered"
        assert len(result.channels_sent) == 2
        assert AlertChannel.WEBSOCKET in result.channels_sent
        assert AlertChannel.SLACK in result.channels_sent
        
        # Verify method calls
        self.service._persist_alert.assert_called_once_with(self.sample_alert)
        self.service._dispatch_to_websocket.assert_called_once_with(self.sample_alert)
        self.service._dispatch_to_slack.assert_called_once_with(self.sample_alert)
    
    @pytest.mark.asyncio
    async def test_dispatch_alert_partial_success(self):
        """Test alert dispatch with partial channel failure."""
        # Mock dependencies
        self.service._persist_alert = AsyncMock()
        self.service._mark_for_deduplication = AsyncMock()
        self.service._is_duplicate_alert = AsyncMock(return_value=False)
        self.service._dispatch_to_websocket = AsyncMock(return_value=True)
        self.service._dispatch_to_slack = AsyncMock(return_value=False)  # Slack fails
        self.service._update_metrics = AsyncMock()
        
        result = await self.service.dispatch_alert(self.sample_alert)
        
        # Verify partial success
        assert result.status == "partial"
        assert len(result.channels_sent) == 1
        assert AlertChannel.WEBSOCKET in result.channels_sent
        assert AlertChannel.SLACK not in result.channels_sent
    
    @pytest.mark.asyncio
    async def test_dispatch_alert_all_channels_fail(self):
        """Test alert dispatch when all channels fail."""
        # Mock dependencies
        self.service._persist_alert = AsyncMock()
        self.service._mark_for_deduplication = AsyncMock()
        self.service._is_duplicate_alert = AsyncMock(return_value=False)
        self.service._dispatch_to_websocket = AsyncMock(return_value=False)
        self.service._dispatch_to_slack = AsyncMock(return_value=False)
        
        # Should raise AlertDeliveryError
        with pytest.raises(AlertDeliveryError):
            await self.service.dispatch_alert(self.sample_alert)
    
    @pytest.mark.asyncio
    async def test_dispatch_alert_duplicate_detection(self):
        """Test duplicate alert detection."""
        # Mock duplicate detection
        self.service._is_duplicate_alert = AsyncMock(return_value=True)
        
        result = await self.service.dispatch_alert(self.sample_alert)
        
        # Should return duplicate status
        assert result.status == "duplicate"
        assert len(result.channels_sent) == 0
        assert self.service._metrics["duplicate_alerts"] == 1
    
    @pytest.mark.asyncio
    async def test_dispatch_alert_expired(self):
        """Test dispatch of expired alert."""
        # Create expired alert
        expired_alert = Alert(
            title="Expired Alert",
            message="This alert has expired",
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.HIGH,
            channels=[AlertChannel.WEBSOCKET],
            source="test_system",
            expires_at=datetime.utcnow() - timedelta(minutes=1)  # Expired
        )
        
        result = await self.service.dispatch_alert(expired_alert)
        
        # Should return expired status
        assert result.status == "expired"
        assert len(result.channels_sent) == 0
        assert self.service._metrics["expired_alerts"] == 1
    
    @pytest.mark.asyncio
    async def test_dispatch_to_websocket_success(self):
        """Test WebSocket dispatch success."""
        with patch('src.eduhub.alerts.services.websocket_manager') as mock_ws_manager:
            mock_ws_manager.broadcast_alert = AsyncMock(return_value={
                "total_sent": 5,
                "filtered": 2
            })
            
            result = await self.service._dispatch_to_websocket(self.sample_alert)
            
            assert result is True
            assert self.service._metrics["websocket_deliveries"] == 1
    
    @pytest.mark.asyncio
    async def test_dispatch_to_websocket_failure(self):
        """Test WebSocket dispatch failure."""
        with patch('src.eduhub.alerts.services.websocket_manager') as mock_ws_manager:
            mock_ws_manager.broadcast_alert = AsyncMock(side_effect=Exception("WebSocket error"))
            
            result = await self.service._dispatch_to_websocket(self.sample_alert)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_dispatch_to_slack_success(self):
        """Test Slack dispatch success."""
        mock_slack_client = AsyncMock()
        mock_slack_client.send_alert = AsyncMock(return_value={"success": True})
        self.service.slack_client = mock_slack_client
        
        result = await self.service._dispatch_to_slack(self.sample_alert)
        
        assert result is True
        assert self.service._metrics["slack_deliveries"] == 1
    
    @pytest.mark.asyncio
    async def test_dispatch_to_slack_failure(self):
        """Test Slack dispatch failure."""
        mock_slack_client = AsyncMock()
        mock_slack_client.send_alert = AsyncMock(side_effect=Exception("Slack error"))
        self.service.slack_client = mock_slack_client
        
        result = await self.service._dispatch_to_slack(self.sample_alert)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_dispatch_to_slack_not_configured(self):
        """Test Slack dispatch when client is not configured."""
        self.service.slack_client = None
        
        result = await self.service._dispatch_to_slack(self.sample_alert)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_create_and_dispatch_alert(self):
        """Test creating and dispatching alert from request."""
        request = AlertRequest(
            title="Test Request Alert",
            message="Alert from request",
            category=AlertCategory.WORKFLOW,
            priority=AlertPriority.MEDIUM,
            channels=[AlertChannel.WEBSOCKET],
            expires_in_seconds=3600
        )
        
        # Mock dispatch method
        self.service.dispatch_alert = AsyncMock(return_value=MagicMock(
            alert_id=uuid4(),
            status="delivered"
        ))
        
        result = await self.service.create_and_dispatch_alert(request, source="api")
        
        # Verify alert was created and dispatched
        self.service.dispatch_alert.assert_called_once()
        
        # Check the alert that was created
        call_args = self.service.dispatch_alert.call_args[0]
        created_alert = call_args[0]
        
        assert created_alert.title == request.title
        assert created_alert.message == request.message
        assert created_alert.category == request.category
        assert created_alert.source == "api"
        assert created_alert.expires_at is not None
    
    @pytest.mark.asyncio
    async def test_deduplication_logic(self):
        """Test alert deduplication logic."""
        # Mock Redis client
        mock_redis = AsyncMock()
        self.service.redis_client = mock_redis
        
        # Test duplicate detection
        mock_redis.exists = AsyncMock(return_value=True)
        
        is_duplicate = await self.service._is_duplicate_alert(self.sample_alert)
        assert is_duplicate is True
        
        # Test marking for deduplication
        mock_redis.setex = AsyncMock()
        
        await self.service._mark_for_deduplication(self.sample_alert)
        
        # Verify setex was called with correct parameters
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 300  # 5 minute window
    
    @pytest.mark.asyncio
    async def test_alert_persistence(self):
        """Test alert persistence to Redis."""
        # Mock Redis client
        mock_redis = AsyncMock()
        self.service.redis_client = mock_redis
        
        await self.service._persist_alert(self.sample_alert)
        
        # Verify Redis operations
        mock_redis.hset.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_alert_retrieval(self):
        """Test retrieving alerts from persistence."""
        # Mock Redis client
        mock_redis = AsyncMock()
        self.service.redis_client = mock_redis
        
        # Mock stored alert data
        alert_json = self.sample_alert.model_dump_json()
        mock_redis.hget = AsyncMock(return_value=alert_json)
        
        retrieved_alert = await self.service.get_alert_by_id(self.sample_alert.id)
        
        assert retrieved_alert is not None
        assert retrieved_alert.id == self.sample_alert.id
        assert retrieved_alert.title == self.sample_alert.title
    
    @pytest.mark.asyncio
    async def test_recent_alerts_retrieval(self):
        """Test retrieving recent alerts."""
        # Mock Redis client
        mock_redis = AsyncMock()
        self.service.redis_client = mock_redis
        
        # Mock multiple alerts
        alert1_json = self.sample_alert.model_dump_json()
        
        alert2 = Alert(
            title="Second Alert",
            message="Another alert",
            category=AlertCategory.WORKFLOW,
            priority=AlertPriority.LOW,
            channels=[AlertChannel.SLACK],
            source="test_system"
        )
        alert2_json = alert2.model_dump_json()
        
        mock_redis.hgetall = AsyncMock(return_value={
            str(self.sample_alert.id): alert1_json,
            str(alert2.id): alert2_json
        })
        
        recent_alerts = await self.service.get_recent_alerts(limit=10)
        
        assert len(recent_alerts) == 2
        # Should be sorted by created_at descending
        assert recent_alerts[0].created_at >= recent_alerts[1].created_at
    
    @pytest.mark.asyncio
    async def test_expired_alerts_cleanup(self):
        """Test cleaning up expired alerts."""
        # Mock Redis client
        mock_redis = AsyncMock()
        self.service.redis_client = mock_redis
        
        # Create expired alert
        expired_alert = Alert(
            title="Expired Alert",
            message="This should be cleaned up",
            category=AlertCategory.SYSTEM,
            priority=AlertPriority.LOW,
            channels=[AlertChannel.WEBSOCKET],
            source="test_system",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        # Mock Redis data
        mock_redis.hgetall = AsyncMock(return_value={
            str(self.sample_alert.id): self.sample_alert.model_dump_json(),
            str(expired_alert.id): expired_alert.model_dump_json()
        })
        mock_redis.hdel = AsyncMock()
        
        cleaned_count = await self.service.cleanup_expired_alerts()
        
        assert cleaned_count == 1
        mock_redis.hdel.assert_called_once_with(
            self.service.alerts_key,
            str(expired_alert.id)
        )
    
    @pytest.mark.asyncio
    async def test_dispatch_timeout(self):
        """Test dispatch timeout handling."""
        # Mock slow channel dispatch
        async def slow_websocket_dispatch(alert):
            await asyncio.sleep(0.1)  # Simulate slow operation
            return True
        
        async def slow_slack_dispatch(alert):
            await asyncio.sleep(0.1)  # Simulate slow operation
            return True
        
        self.service._dispatch_to_websocket = slow_websocket_dispatch
        self.service._dispatch_to_slack = slow_slack_dispatch
        self.service.max_broadcast_timeout_ms = 50  # Very short timeout
        
        # Mock other dependencies
        self.service._persist_alert = AsyncMock()
        self.service._mark_for_deduplication = AsyncMock()
        self.service._is_duplicate_alert = AsyncMock(return_value=False)
        self.service._update_metrics = AsyncMock()
        
        # Should handle timeout gracefully
        result = await self.service.dispatch_alert(self.sample_alert)
        
        # All channels should be marked as failed due to timeout
        assert result.status == "partial" or len(result.channels_sent) == 0
    
    def test_get_metrics(self):
        """Test metrics retrieval."""
        # Set some test metrics
        self.service._metrics["total_alerts_dispatched"] = 10
        self.service._metrics["websocket_deliveries"] = 8
        self.service._metrics["slack_deliveries"] = 6
        self.service._metrics["failed_deliveries"] = 2
        
        with patch('src.eduhub.alerts.services.websocket_manager') as mock_ws_manager:
            mock_ws_manager.get_metrics.return_value = {"active_subscriptions": 5}
            
            metrics = self.service.get_metrics()
            
            assert metrics.total_alerts_sent == 10
            assert metrics.websocket_alerts_sent == 8
            assert metrics.slack_alerts_sent == 6
            assert metrics.failed_alerts == 2
            assert metrics.active_subscriptions == 5
    
    @pytest.mark.asyncio
    async def test_test_channels(self):
        """Test channel connectivity testing."""
        # Mock WebSocket manager
        with patch('src.eduhub.alerts.services.websocket_manager') as mock_ws_manager:
            mock_ws_manager.get_metrics.return_value = {"active_connections": 3}
            
            # Mock Slack client
            mock_slack_client = AsyncMock()
            mock_slack_client.test_connection = AsyncMock(return_value={
                "success": True,
                "team": "Test Team"
            })
            self.service.slack_client = mock_slack_client
            
            # Mock Redis client
            mock_redis = AsyncMock()
            self.service.redis_client = mock_redis
            
            results = await self.service.test_channels()
            
            # Verify all channels tested
            assert "websocket" in results
            assert "slack" in results
            assert "redis" in results
            
            assert results["websocket"]["available"] is True
            assert results["slack"]["success"] is True
            assert results["redis"]["success"] is True 