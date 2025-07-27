"""
Tests for WebSocket hub functionality.

Tests connection management, subscription handling, alert broadcasting,
and integration with Redis pub-sub.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import WebSocket
from fastapi.testclient import TestClient

from src.eduhub.alerts.models import Alert, AlertCategory, AlertPriority, Subscription, WebSocketMessage
from src.eduhub.alerts.websocket_hub import AlertWebSocketManager, ConnectionManager


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.accepted = False
        self.closed = False
        self.sent_messages = []
        self.close_code = None
        self.close_reason = None
    
    async def accept(self):
        self.accepted = True
    
    async def close(self, code=None, reason=None):
        self.closed = True
        self.close_code = code
        self.close_reason = reason
    
    async def send_text(self, message: str):
        if self.closed:
            raise RuntimeError("WebSocket connection closed")
        self.sent_messages.append(message)
    
    def get_last_message(self) -> dict:
        if not self.sent_messages:
            return {}
        return json.loads(self.sent_messages[-1])
    
    def get_all_messages(self) -> list:
        return [json.loads(msg) for msg in self.sent_messages]


class TestConnectionManager:
    """Test the ConnectionManager class."""
    
    def setup_method(self):
        self.manager = ConnectionManager()
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """Test connecting a WebSocket client."""
        websocket = MockWebSocket()
        user_id = "test-user-123"
        
        connection_id = await self.manager.connect(websocket, user_id)
        
        assert connection_id is not None
        assert websocket.accepted
        assert connection_id in self.manager.active_connections
        assert user_id in self.manager.user_connections
        assert connection_id in self.manager.user_connections[user_id]
        assert connection_id in self.manager.connection_metadata
        
        metadata = self.manager.connection_metadata[connection_id]
        assert metadata["user_id"] == user_id
        assert isinstance(metadata["connected_at"], datetime)
        assert isinstance(metadata["last_ping"], datetime)
    
    def test_disconnect_websocket(self):
        """Test disconnecting a WebSocket client."""
        # Setup a connection first
        websocket = MockWebSocket()
        user_id = "test-user-123"
        connection_id = "test-connection-id"
        
        self.manager.active_connections[connection_id] = websocket
        self.manager.user_connections[user_id] = {connection_id}
        self.manager.connection_metadata[connection_id] = {"user_id": user_id}
        
        # Disconnect
        returned_user_id = self.manager.disconnect(connection_id)
        
        assert returned_user_id == user_id
        assert connection_id not in self.manager.active_connections
        assert connection_id not in self.manager.connection_metadata
        assert user_id not in self.manager.user_connections
    
    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending a message to a connection."""
        websocket = MockWebSocket()
        user_id = "test-user-123"
        connection_id = await self.manager.connect(websocket, user_id)
        
        message = WebSocketMessage(type="test", data={"key": "value"})
        success = await self.manager.send_message(connection_id, message)
        
        assert success
        assert len(websocket.sent_messages) == 1
        sent_data = websocket.get_last_message()
        assert sent_data["type"] == "test"
        assert sent_data["data"]["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_connection(self):
        """Test sending a message to a non-existent connection."""
        message = WebSocketMessage(type="test", data={})
        success = await self.manager.send_message("nonexistent", message)
        
        assert not success
    
    @pytest.mark.asyncio
    async def test_broadcast_to_user(self):
        """Test broadcasting a message to all user connections."""
        user_id = "test-user-123"
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        
        connection_id1 = await self.manager.connect(websocket1, user_id)
        connection_id2 = await self.manager.connect(websocket2, user_id)
        
        message = WebSocketMessage(type="broadcast", data={"message": "hello"})
        sent_count = await self.manager.broadcast_to_user(user_id, message)
        
        assert sent_count == 2
        assert len(websocket1.sent_messages) == 1
        assert len(websocket2.sent_messages) == 1
        
        # Check message content
        assert websocket1.get_last_message()["type"] == "broadcast"
        assert websocket2.get_last_message()["type"] == "broadcast"
    
    def test_get_stale_connections(self):
        """Test identifying stale connections."""
        # Setup connections with different ping times
        current_time = datetime.utcnow()
        old_time = current_time - timedelta(seconds=120)
        
        self.manager.connection_metadata = {
            "fresh": {"last_ping": current_time, "user_id": "user1"},
            "stale": {"last_ping": old_time, "user_id": "user2"}
        }
        
        stale_connections = self.manager.get_stale_connections(max_age_seconds=60)
        
        assert "stale" in stale_connections
        assert "fresh" not in stale_connections
    
    def test_connection_counts(self):
        """Test connection count methods."""
        user_id = "test-user"
        
        assert self.manager.get_active_connections_count() == 0
        assert self.manager.get_user_connections_count(user_id) == 0
        
        # Add connections
        self.manager.active_connections["conn1"] = MockWebSocket()
        self.manager.active_connections["conn2"] = MockWebSocket()
        self.manager.user_connections[user_id] = {"conn1", "conn2"}
        
        assert self.manager.get_active_connections_count() == 2
        assert self.manager.get_user_connections_count(user_id) == 2


class TestAlertWebSocketManager:
    """Test the main AlertWebSocketManager class."""
    
    def setup_method(self):
        self.manager = AlertWebSocketManager()
    
    @pytest.mark.asyncio
    async def test_initialize_without_redis(self):
        """Test initialization when Redis is not available."""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis.return_value.ping.side_effect = Exception("Redis not available")
            
            await self.manager.initialize()
            
            assert self.manager.redis_client is None
            assert self.manager.channel_layer is None
    
    @pytest.mark.asyncio
    async def test_connect_client_success(self):
        """Test successful client connection."""
        websocket = MockWebSocket()
        user_id = "test-user-123"
        
        connection_id = await self.manager.connect_client(websocket, user_id)
        
        assert connection_id is not None
        assert websocket.accepted
        assert len(websocket.sent_messages) == 1
        
        # Check welcome message
        welcome_msg = websocket.get_last_message()
        assert welcome_msg["type"] == "connected"
        assert "connection_id" in welcome_msg["data"]
        assert "heartbeat_interval" in welcome_msg["data"]
    
    @pytest.mark.asyncio
    async def test_connect_client_limit_exceeded(self):
        """Test connection rejection when limit is exceeded."""
        self.manager.max_connections_per_user = 1
        user_id = "test-user-123"
        
        # Connect first client successfully
        websocket1 = MockWebSocket()
        connection_id1 = await self.manager.connect_client(websocket1, user_id)
        assert connection_id1 is not None
        
        # Second connection should be rejected
        websocket2 = MockWebSocket()
        connection_id2 = await self.manager.connect_client(websocket2, user_id)
        
        assert connection_id2 is None
        assert websocket2.closed
        assert websocket2.close_code == 1008
    
    @pytest.mark.asyncio
    async def test_handle_ping_message(self):
        """Test handling ping message."""
        websocket = MockWebSocket()
        user_id = "test-user-123"
        connection_id = await self.manager.connect_client(websocket, user_id)
        
        # Clear welcome message
        websocket.sent_messages.clear()
        
        # Send ping
        await self.manager.handle_message(connection_id, '{"type": "ping"}')
        
        # Should receive pong
        assert len(websocket.sent_messages) == 1
        pong_msg = websocket.get_last_message()
        assert pong_msg["type"] == "pong"
        assert "server_time" in pong_msg["data"]
    
    @pytest.mark.asyncio
    async def test_handle_subscribe_message(self):
        """Test handling subscription request."""
        websocket = MockWebSocket()
        user_id = "test-user-123"
        connection_id = await self.manager.connect_client(websocket, user_id)
        
        # Clear welcome message
        websocket.sent_messages.clear()
        
        # Send subscription request
        subscribe_data = {
            "type": "subscribe",
            "data": {
                "categories": ["workflow", "system"],
                "priorities": ["high", "critical"]
            }
        }
        
        await self.manager.handle_message(connection_id, json.dumps(subscribe_data))
        
        # Should receive subscription confirmation
        assert len(websocket.sent_messages) == 1
        confirm_msg = websocket.get_last_message()
        assert confirm_msg["type"] == "subscribed"
        assert confirm_msg["data"]["categories"] == ["workflow", "system"]
        assert confirm_msg["data"]["priorities"] == ["high", "critical"]
        
        # Check subscription was stored
        assert connection_id in self.manager.subscriptions
        subscription = self.manager.subscriptions[connection_id]
        assert subscription.user_id == user_id
        assert AlertCategory.WORKFLOW in subscription.categories
        assert AlertPriority.HIGH in subscription.priorities
    
    @pytest.mark.asyncio
    async def test_broadcast_alert_with_filtering(self):
        """Test alert broadcasting with subscription filtering."""
        # Setup two connections with different subscriptions
        user1_websocket = MockWebSocket()
        user2_websocket = MockWebSocket()
        
        user1_id = await self.manager.connect_client(user1_websocket, "user1")
        user2_id = await self.manager.connect_client(user2_websocket, "user2")
        
        # Subscribe user1 to workflow alerts
        self.manager.subscriptions[user1_id] = Subscription(
            user_id="user1",
            connection_id=user1_id,
            categories=[AlertCategory.WORKFLOW],
            priorities=[AlertPriority.HIGH]
        )
        
        # Subscribe user2 to system alerts only
        self.manager.subscriptions[user2_id] = Subscription(
            user_id="user2", 
            connection_id=user2_id,
            categories=[AlertCategory.SYSTEM],
            priorities=[AlertPriority.MEDIUM]
        )
        
        # Clear welcome messages
        user1_websocket.sent_messages.clear()
        user2_websocket.sent_messages.clear()
        
        # Create workflow alert
        alert = Alert(
            title="Workflow Update",
            message="Document approved",
            category=AlertCategory.WORKFLOW,
            priority=AlertPriority.HIGH,
            source="test"
        )
        
        # Broadcast alert
        stats = await self.manager.broadcast_alert(alert)
        
        # Only user1 should receive the alert
        assert stats["total_sent"] == 1
        assert stats["filtered"] == 1
        assert len(user1_websocket.sent_messages) == 1
        assert len(user2_websocket.sent_messages) == 0
        
        # Check alert content
        alert_msg = user1_websocket.get_last_message()
        assert alert_msg["type"] == "alert"
        assert alert_msg["data"]["title"] == "Workflow Update"
    
    @pytest.mark.asyncio
    async def test_broadcast_alert_user_specific(self):
        """Test broadcasting user-specific alerts."""
        # Setup connections for two users
        user1_websocket = MockWebSocket()
        user2_websocket = MockWebSocket()
        
        user1_id = await self.manager.connect_client(user1_websocket, "user1")
        user2_id = await self.manager.connect_client(user2_websocket, "user2")
        
        # Subscribe both to workflow alerts
        for user_id, connection_id in [("user1", user1_id), ("user2", user2_id)]:
            self.manager.subscriptions[connection_id] = Subscription(
                user_id=user_id,
                connection_id=connection_id,
                categories=[AlertCategory.WORKFLOW],
                priorities=[AlertPriority.MEDIUM]
            )
        
        # Clear welcome messages
        user1_websocket.sent_messages.clear()
        user2_websocket.sent_messages.clear()
        
        # Create user-specific alert
        alert = Alert(
            title="Personal Alert",
            message="Your document was approved",
            category=AlertCategory.WORKFLOW,
            priority=AlertPriority.MEDIUM,
            source="test",
            user_id="user1"  # Specific to user1
        )
        
        # Broadcast alert
        stats = await self.manager.broadcast_alert(alert)
        
        # Only user1 should receive the alert
        assert stats["total_sent"] == 1
        assert stats["filtered"] == 1
        assert len(user1_websocket.sent_messages) == 1
        assert len(user2_websocket.sent_messages) == 0
    
    def test_get_metrics(self):
        """Test metrics collection."""
        # Add some test data
        self.manager.connection_manager.active_connections["conn1"] = MockWebSocket()
        self.manager.subscriptions["conn1"] = MagicMock()
        
        metrics = self.manager.get_metrics()
        
        assert metrics["active_connections"] == 1
        assert metrics["active_subscriptions"] == 1
        assert "redis_enabled" in metrics
        assert "heartbeat_interval" in metrics
        assert "max_connections_per_user" in metrics
    
    @pytest.mark.asyncio
    async def test_disconnect_client_cleanup(self):
        """Test that disconnecting a client cleans up all resources."""
        websocket = MockWebSocket()
        user_id = "test-user-123"
        connection_id = await self.manager.connect_client(websocket, user_id)
        
        # Add subscription
        self.manager.subscriptions[connection_id] = Subscription(
            user_id=user_id,
            connection_id=connection_id,
            categories=[AlertCategory.SYSTEM],
            priorities=[AlertPriority.HIGH]
        )
        
        # Verify setup
        assert connection_id in self.manager.connection_manager.active_connections
        assert connection_id in self.manager.subscriptions
        
        # Disconnect
        returned_user_id = self.manager.disconnect_client(connection_id)
        
        # Verify cleanup
        assert returned_user_id == user_id
        assert connection_id not in self.manager.connection_manager.active_connections
        assert connection_id not in self.manager.subscriptions
    
    @pytest.mark.asyncio
    async def test_invalid_json_message(self):
        """Test handling invalid JSON messages."""
        websocket = MockWebSocket()
        user_id = "test-user-123"
        connection_id = await self.manager.connect_client(websocket, user_id)
        
        # Clear welcome message
        websocket.sent_messages.clear()
        
        # Send invalid JSON
        await self.manager.handle_message(connection_id, "invalid json {")
        
        # Should not crash, no response sent
        assert len(websocket.sent_messages) == 0 