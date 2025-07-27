"""
WebSocket Hub for Real-time Alert Broadcasting

Manages WebSocket connections, subscriptions, and broadcasting alerts to browser clients.
Supports Redis pub-sub for horizontal scaling and heartbeat for connection health.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect
from channels_redis.core import RedisChannelLayer

from .models import Alert, AlertCategory, AlertPriority, Subscription, WebSocketMessage
from .rate_limit import check_websocket_rate_limit, remove_websocket_rate_limiting
from .monitoring import (
    record_websocket_connection, record_websocket_disconnection, 
    record_websocket_message, record_rate_limit_exceeded
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages individual WebSocket connections and their metadata."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept a new WebSocket connection and return connection ID."""
        await websocket.accept()
        
        connection_id = str(uuid4())
        self.active_connections[connection_id] = websocket
        
        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Store metadata
        self.connection_metadata[connection_id] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow(),
            "subscription": None
        }
        
        # Record metrics
        record_websocket_connection()
        
        logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
        return connection_id
    
    def disconnect(self, connection_id: str) -> Optional[str]:
        """Remove a WebSocket connection and return user_id if found."""
        if connection_id not in self.active_connections:
            return None
            
        # Get user_id before removal
        metadata = self.connection_metadata.get(connection_id, {})
        user_id = metadata.get("user_id")
        
        # Remove from active connections
        del self.active_connections[connection_id]
        del self.connection_metadata[connection_id]
        
        # Update user connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Clean up rate limiting data for this connection
        remove_websocket_rate_limiting(connection_id)
        
        # Record metrics
        record_websocket_disconnection()
        
        logger.info(f"WebSocket disconnected: {connection_id} for user {user_id}")
        return user_id
    
    async def send_message(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send a message to a specific connection with rate limiting."""
        websocket = self.active_connections.get(connection_id)
        if not websocket:
            return False
        
        # Check rate limit for WebSocket messages (10 msg/sec per connection)
        if not await check_websocket_rate_limit(connection_id):
            logger.warning(f"Rate limit exceeded for WebSocket connection {connection_id}")
            
            # Record rate limit violation
            record_rate_limit_exceeded('websocket', connection_id)
            
            # Send rate limit warning to client
            rate_limit_message = WebSocketMessage(
                type="error",
                data={
                    "error": "rate_limit_exceeded",
                    "message": "Message rate limit exceeded (10 messages/second)",
                    "retry_after": 1
                }
            )
            try:
                await websocket.send_text(rate_limit_message.json())
                record_websocket_message("rate_limit_error")
            except Exception:
                pass  # Ignore errors when sending rate limit message
            return False
            
        try:
            await websocket.send_text(message.json())
            # Record successful message
            record_websocket_message(message.type)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to {connection_id}: {e}")
            return False
    
    async def broadcast_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Broadcast a message to all connections for a user."""
        connection_ids = self.user_connections.get(user_id, set())
        sent_count = 0
        
        for connection_id in list(connection_ids):  # Create copy to avoid modification during iteration
            if await self.send_message(connection_id, message):
                sent_count += 1
            else:
                # Connection failed, remove it
                self.disconnect(connection_id)
        
        return sent_count
    
    def get_active_connections_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)
    
    def get_user_connections_count(self, user_id: str) -> int:
        """Get number of active connections for a specific user."""
        return len(self.user_connections.get(user_id, set()))
    
    def update_ping(self, connection_id: str) -> bool:
        """Update last ping timestamp for a connection."""
        if connection_id in self.connection_metadata:
            self.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()
            return True
        return False
    
    def get_stale_connections(self, max_age_seconds: int = 60) -> List[str]:
        """Get connection IDs that haven't pinged recently."""
        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        stale_connections = []
        
        for connection_id, metadata in self.connection_metadata.items():
            last_ping = metadata.get("last_ping", datetime.utcnow())
            if last_ping < cutoff:
                stale_connections.append(connection_id)
        
        return stale_connections


class AlertWebSocketManager:
    """
    Main WebSocket hub for alert broadcasting.
    
    Features:
    - Connection management with user tracking
    - Redis pub-sub for horizontal scaling
    - Subscription filtering by category/priority
    - Heartbeat for connection health
    - Metrics collection
    """
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.subscriptions: Dict[str, Subscription] = {}  # connection_id -> subscription
        self.redis_client: Optional[redis.Redis] = None
        self.channel_layer: Optional[RedisChannelLayer] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # Configuration from environment
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.heartbeat_interval = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30"))
        self.max_connections_per_user = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS_PER_USER", "5"))
        
        # Redis channel names
        self.alert_channel = "alerts:broadcast"
        self.metrics_channel = "alerts:metrics"
    
    async def initialize(self):
        """Initialize Redis connections and background tasks."""
        try:
            # Initialize Redis client
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Initialize Redis channel layer for pub-sub
            self.channel_layer = RedisChannelLayer(hosts=[self.redis_url])
            
            # Start heartbeat task
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            logger.info("AlertWebSocketManager initialized with Redis support")
            
        except Exception as e:
            logger.warning(f"Redis connection failed, falling back to in-memory mode: {e}")
            self.redis_client = None
            self.channel_layer = None
    
    async def shutdown(self):
        """Clean shutdown of the WebSocket manager."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("AlertWebSocketManager shutdown complete")
    
    async def connect_client(self, websocket: WebSocket, user_id: str) -> Optional[str]:
        """
        Connect a new WebSocket client.
        
        Returns connection_id if successful, None if rejected.
        """
        # Check connection limits
        current_connections = self.connection_manager.get_user_connections_count(user_id)
        if current_connections >= self.max_connections_per_user:
            await websocket.close(code=1008, reason="Too many connections")
            logger.warning(f"Connection rejected for user {user_id}: limit exceeded")
            return None
        
        try:
            connection_id = await self.connection_manager.connect(websocket, user_id)
            
            # Send welcome message
            welcome_message = WebSocketMessage(
                type="connected",
                data={
                    "connection_id": connection_id,
                    "server_time": datetime.utcnow().isoformat(),
                    "heartbeat_interval": self.heartbeat_interval
                }
            )
            await self.connection_manager.send_message(connection_id, welcome_message)
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket for user {user_id}: {e}")
            return None
    
    def disconnect_client(self, connection_id: str):
        """Disconnect a WebSocket client and clean up resources."""
        user_id = self.connection_manager.disconnect(connection_id)
        
        # Remove subscription
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
        
        return user_id
    
    async def handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message from client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self._handle_ping(connection_id)
            elif message_type == "subscribe":
                await self._handle_subscribe(connection_id, data.get("data", {}))
            elif message_type == "unsubscribe":
                await self._handle_unsubscribe(connection_id)
            else:
                logger.warning(f"Unknown message type from {connection_id}: {message_type}")
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {connection_id}: {message}")
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
    
    async def broadcast_alert(self, alert: Alert) -> Dict[str, int]:
        """
        Broadcast an alert to all relevant subscribers.
        
        Returns dict with broadcast statistics.
        """
        start_time = datetime.utcnow()
        stats = {"total_sent": 0, "failed": 0, "filtered": 0}
        
        # Create WebSocket message
        alert_message = WebSocketMessage(
            type="alert",
            data=alert.dict()
        )
        
        # Filter and send to subscribed connections
        for connection_id, subscription in self.subscriptions.items():
            if self._should_send_alert(alert, subscription):
                success = await self.connection_manager.send_message(connection_id, alert_message)
                if success:
                    stats["total_sent"] += 1
                else:
                    stats["failed"] += 1
                    # Clean up failed connection
                    self.disconnect_client(connection_id)
            else:
                stats["filtered"] += 1
        
        # Broadcast via Redis for other instances
        if self.channel_layer:
            try:
                await self.channel_layer.send(
                    self.alert_channel,
                    {
                        "type": "alert.broadcast",
                        "alert": alert.dict(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as e:
                logger.error(f"Failed to broadcast alert via Redis: {e}")
        
        # Calculate and log performance
        broadcast_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.info(f"Alert broadcast completed in {broadcast_time:.2f}ms: {stats}")
        
        return stats
    
    async def _handle_ping(self, connection_id: str):
        """Handle ping message and respond with pong."""
        self.connection_manager.update_ping(connection_id)
        
        pong_message = WebSocketMessage(
            type="pong",
            data={"server_time": datetime.utcnow().isoformat()}
        )
        await self.connection_manager.send_message(connection_id, pong_message)
    
    async def _handle_subscribe(self, connection_id: str, data: Dict[str, Any]):
        """Handle subscription request."""
        try:
            # Get user_id from connection metadata
            metadata = self.connection_manager.connection_metadata.get(connection_id, {})
            user_id = metadata.get("user_id")
            
            if not user_id:
                logger.error(f"No user_id found for connection {connection_id}")
                return
            
            # Parse subscription preferences
            categories = [AlertCategory(cat) for cat in data.get("categories", [])]
            priorities = [AlertPriority(pri) for pri in data.get("priorities", [])]
            
            # Create subscription
            subscription = Subscription(
                user_id=user_id,
                connection_id=connection_id,
                categories=categories,
                priorities=priorities
            )
            
            self.subscriptions[connection_id] = subscription
            
            # Send confirmation
            confirm_message = WebSocketMessage(
                type="subscribed",
                data={
                    "subscription_id": str(subscription.id),
                    "categories": [cat.value for cat in categories],
                    "priorities": [pri.value for pri in priorities]
                }
            )
            await self.connection_manager.send_message(connection_id, confirm_message)
            
            logger.info(f"Subscription created for {connection_id}: {len(categories)} categories, {len(priorities)} priorities")
            
        except Exception as e:
            logger.error(f"Failed to handle subscription for {connection_id}: {e}")
    
    async def _handle_unsubscribe(self, connection_id: str):
        """Handle unsubscribe request."""
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]
            
            unsubscribe_message = WebSocketMessage(
                type="unsubscribed",
                data={"status": "success"}
            )
            await self.connection_manager.send_message(connection_id, unsubscribe_message)
            
            logger.info(f"Subscription removed for {connection_id}")
    
    def _should_send_alert(self, alert: Alert, subscription: Subscription) -> bool:
        """Determine if an alert should be sent to a subscription."""
        # Check if alert is for specific user
        if alert.user_id and alert.user_id != subscription.user_id:
            return False
        
        # Check category filter
        if subscription.categories and alert.category not in subscription.categories:
            return False
        
        # Check priority filter
        if subscription.priorities and alert.priority not in subscription.priorities:
            return False
        
        # Check expiration
        if alert.expires_at and alert.expires_at < datetime.utcnow():
            return False
        
        return True
    
    async def _heartbeat_loop(self):
        """Background task to check connection health and clean up stale connections."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Find and disconnect stale connections
                stale_connections = self.connection_manager.get_stale_connections(
                    max_age_seconds=self.heartbeat_interval * 2
                )
                
                for connection_id in stale_connections:
                    logger.info(f"Cleaning up stale connection: {connection_id}")
                    self.disconnect_client(connection_id)
                
                # Log active connection stats
                active_count = self.connection_manager.get_active_connections_count()
                subscription_count = len(self.subscriptions)
                
                if active_count > 0:
                    logger.debug(f"Active connections: {active_count}, Subscriptions: {subscription_count}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current WebSocket metrics."""
        return {
            "active_connections": self.connection_manager.get_active_connections_count(),
            "active_subscriptions": len(self.subscriptions),
            "redis_enabled": self.redis_client is not None,
            "heartbeat_interval": self.heartbeat_interval,
            "max_connections_per_user": self.max_connections_per_user
        }


# Global WebSocket manager instance
websocket_manager = AlertWebSocketManager()
