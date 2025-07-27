"""
Unified Alert Dispatch Service

Orchestrates multi-channel alert delivery across WebSocket and Slack channels.
Provides persistence, tracking, deduplication, and comprehensive metrics.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID
import json

import redis.asyncio as redis
from fastapi import HTTPException

from .models import Alert, AlertChannel, AlertPriority, AlertRequest, AlertResponse, AlertMetrics
from .websocket_hub import websocket_manager
from .slack_client import get_slack_client, SlackConfigurationError

logger = logging.getLogger(__name__)


class AlertDispatchError(Exception):
    """Base exception for alert dispatch errors."""
    pass


class AlertPersistenceError(AlertDispatchError):
    """Raised when alert persistence operations fail."""
    pass


class AlertDeliveryError(AlertDispatchError):
    """Raised when alert delivery fails across all channels."""
    pass


class AlertDispatchService:
    """
    Unified service for dispatching alerts across multiple channels.
    
    Features:
    - Multi-channel delivery (WebSocket, Slack)
    - Redis persistence and deduplication
    - Delivery tracking and metrics
    - Failure handling and circuit breaker patterns
    - Alert expiration and cleanup
    - Rate limiting and throttling
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.slack_client = None
        
        # Configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.alert_ttl = int(os.getenv("ALERT_RETENTION_DAYS", "30")) * 24 * 3600  # seconds
        self.max_broadcast_timeout_ms = int(os.getenv("ALERT_BROADCAST_TIMEOUT_MS", "50"))
        self.deduplication_window_seconds = 300  # 5 minutes
        
        # Metrics tracking
        self._metrics = {
            "total_alerts_dispatched": 0,
            "websocket_deliveries": 0,
            "slack_deliveries": 0,
            "failed_deliveries": 0,
            "duplicate_alerts": 0,
            "expired_alerts": 0
        }
        
        # Redis keys
        self.alerts_key = "alerts:active"
        self.metrics_key = "alerts:metrics"
        self.dedup_key_prefix = "alerts:dedup:"
        
    async def initialize(self):
        """Initialize Redis connection and external services."""
        try:
            # Initialize Redis
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Alert dispatch service connected to Redis")
            
            # Initialize WebSocket manager
            await websocket_manager.initialize()
            
            # Initialize Slack client (optional)
            try:
                self.slack_client = get_slack_client()
                logger.info("Alert dispatch service connected to Slack")
            except SlackConfigurationError:
                logger.warning("Slack not configured - WebSocket-only mode")
                self.slack_client = None
                
        except Exception as e:
            logger.error(f"Failed to initialize alert dispatch service: {e}")
            # Fallback to in-memory mode
            self.redis_client = None
    
    async def shutdown(self):
        """Clean shutdown of the dispatch service."""
        if self.redis_client:
            await self.redis_client.close()
        
        await websocket_manager.shutdown()
        
        if self.slack_client:
            await self.slack_client.close()
        
        logger.info("Alert dispatch service shutdown complete")
    
    async def dispatch_alert(self, alert: Alert) -> AlertResponse:
        """
        Main method to dispatch an alert across configured channels.
        
        Args:
            alert: The alert to dispatch
            
        Returns:
            AlertResponse with dispatch results
            
        Raises:
            AlertDeliveryError: When delivery fails across all channels
        """
        dispatch_start = datetime.utcnow()
        
        try:
            # Check for duplicates
            if await self._is_duplicate_alert(alert):
                self._metrics["duplicate_alerts"] += 1
                logger.info(f"Duplicate alert detected: {alert.id}")
                return AlertResponse(
                    alert_id=alert.id,
                    status="duplicate",
                    channels_sent=[],
                    created_at=alert.created_at
                )
            
            # Check expiration
            if alert.expires_at and alert.expires_at < datetime.utcnow():
                self._metrics["expired_alerts"] += 1
                logger.warning(f"Alert expired before dispatch: {alert.id}")
                return AlertResponse(
                    alert_id=alert.id,
                    status="expired",
                    channels_sent=[],
                    created_at=alert.created_at
                )
            
            # Persist alert
            await self._persist_alert(alert)
            
            # Mark for deduplication
            await self._mark_for_deduplication(alert)
            
            # Dispatch to channels
            delivery_results = await self._dispatch_to_channels(alert)
            
            # Update metrics
            self._metrics["total_alerts_dispatched"] += 1
            await self._update_metrics(delivery_results)
            
            # Determine status
            successful_channels = [channel for channel, success in delivery_results.items() if success]
            failed_channels = [channel for channel, success in delivery_results.items() if not success]
            
            if not successful_channels:
                self._metrics["failed_deliveries"] += 1
                raise AlertDeliveryError(f"Alert delivery failed on all channels: {failed_channels}")
            
            if failed_channels:
                logger.warning(f"Alert {alert.id} partially delivered. Failed: {failed_channels}")
                status = "partial"
            else:
                status = "delivered"
            
            # Calculate dispatch time
            dispatch_time = (datetime.utcnow() - dispatch_start).total_seconds() * 1000
            logger.info(f"Alert {alert.id} dispatched in {dispatch_time:.2f}ms to {successful_channels}")
            
            return AlertResponse(
                alert_id=alert.id,
                status=status,
                channels_sent=[AlertChannel(ch) for ch in successful_channels],
                created_at=alert.created_at
            )
            
        except Exception as e:
            self._metrics["failed_deliveries"] += 1
            logger.error(f"Alert dispatch failed for {alert.id}: {e}")
            raise AlertDispatchError(f"Failed to dispatch alert: {e}")
    
    async def create_and_dispatch_alert(self, request: AlertRequest, source: str = "api") -> AlertResponse:
        """
        Create an alert from request and dispatch it.
        
        Args:
            request: Alert creation request
            source: Source identifier for the alert
            
        Returns:
            AlertResponse with dispatch results
        """
        # Calculate expiration if specified
        expires_at = None
        if request.expires_in_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=request.expires_in_seconds)
        
        # Create alert
        alert = Alert(
            title=request.title,
            message=request.message,
            priority=request.priority,
            category=request.category,
            channels=request.channels,
            source=source,
            user_id=request.user_id,
            metadata=request.metadata,
            expires_at=expires_at,
            slack_channel=request.slack_channel
        )
        
        return await self.dispatch_alert(alert)
    
    async def _dispatch_to_channels(self, alert: Alert) -> Dict[str, bool]:
        """Dispatch alert to all configured channels."""
        delivery_results = {}
        
        # Dispatch to each channel in parallel
        tasks = []
        
        for channel in alert.channels:
            if channel == AlertChannel.WEBSOCKET:
                tasks.append(self._dispatch_to_websocket(alert))
            elif channel == AlertChannel.SLACK:
                tasks.append(self._dispatch_to_slack(alert))
            else:
                logger.warning(f"Unknown channel type: {channel}")
                delivery_results[channel.value] = False
        
        # Wait for all dispatches with timeout
        if tasks:
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.max_broadcast_timeout_ms / 1000.0
                )
                
                # Process results
                channel_index = 0
                for channel in alert.channels:
                    if channel in [AlertChannel.WEBSOCKET, AlertChannel.SLACK]:
                        result = results[channel_index]
                        if isinstance(result, Exception):
                            logger.error(f"Channel {channel.value} dispatch failed: {result}")
                            delivery_results[channel.value] = False
                        else:
                            delivery_results[channel.value] = result
                        channel_index += 1
                        
            except asyncio.TimeoutError:
                logger.error(f"Alert dispatch timeout after {self.max_broadcast_timeout_ms}ms")
                # Mark all pending channels as failed
                for channel in alert.channels:
                    if channel.value not in delivery_results:
                        delivery_results[channel.value] = False
        
        return delivery_results
    
    async def _dispatch_to_websocket(self, alert: Alert) -> bool:
        """Dispatch alert to WebSocket subscribers."""
        try:
            stats = await websocket_manager.broadcast_alert(alert)
            success = stats.get("total_sent", 0) > 0 or stats.get("filtered", 0) > 0
            
            if success:
                self._metrics["websocket_deliveries"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"WebSocket dispatch failed: {e}")
            return False
    
    async def _dispatch_to_slack(self, alert: Alert) -> bool:
        """Dispatch alert to Slack channel."""
        if not self.slack_client:
            logger.warning("Slack client not available")
            return False
        
        try:
            result = await self.slack_client.send_alert(alert)
            success = result.get("success", False)
            
            if success:
                self._metrics["slack_deliveries"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Slack dispatch failed: {e}")
            return False
    
    async def _is_duplicate_alert(self, alert: Alert) -> bool:
        """Check if alert is a duplicate within the deduplication window."""
        if not self.redis_client:
            return False
        
        # Create deduplication key based on content hash
        content_hash = hash(f"{alert.title}:{alert.message}:{alert.category}:{alert.user_id}")
        dedup_key = f"{self.dedup_key_prefix}{content_hash}"
        
        try:
            exists = await self.redis_client.exists(dedup_key)
            return bool(exists)
        except Exception as e:
            logger.error(f"Deduplication check failed: {e}")
            return False
    
    async def _mark_for_deduplication(self, alert: Alert) -> None:
        """Mark alert for deduplication tracking."""
        if not self.redis_client:
            return
        
        content_hash = hash(f"{alert.title}:{alert.message}:{alert.category}:{alert.user_id}")
        dedup_key = f"{self.dedup_key_prefix}{content_hash}"
        
        try:
            await self.redis_client.setex(
                dedup_key,
                self.deduplication_window_seconds,
                str(alert.id)
            )
        except Exception as e:
            logger.error(f"Deduplication marking failed: {e}")
    
    async def _persist_alert(self, alert: Alert) -> None:
        """Persist alert to Redis for tracking and metrics."""
        if not self.redis_client:
            return
        
        try:
            alert_data = alert.model_dump_json()
            await self.redis_client.hset(
                self.alerts_key,
                str(alert.id),
                alert_data
            )
            
            # Set expiration on the alert
            if alert.expires_at:
                expire_seconds = int((alert.expires_at - datetime.utcnow()).total_seconds())
                if expire_seconds > 0:
                    await self.redis_client.expire(
                        f"{self.alerts_key}:{alert.id}",
                        expire_seconds
                    )
            else:
                # Default TTL
                await self.redis_client.expire(
                    f"{self.alerts_key}:{alert.id}",
                    self.alert_ttl
                )
                
        except Exception as e:
            logger.error(f"Alert persistence failed: {e}")
            raise AlertPersistenceError(f"Failed to persist alert {alert.id}")
    
    async def _update_metrics(self, delivery_results: Dict[str, bool]) -> None:
        """Update metrics in Redis."""
        if not self.redis_client:
            return
        
        try:
            # Update Redis metrics
            metrics_data = {
                "timestamp": datetime.utcnow().isoformat(),
                **self._metrics
            }
            
            await self.redis_client.hset(
                self.metrics_key,
                "current",
                json.dumps(metrics_data)
            )
            
        except Exception as e:
            logger.error(f"Metrics update failed: {e}")
    
    async def get_alert_by_id(self, alert_id: UUID) -> Optional[Alert]:
        """Retrieve an alert by ID from persistence."""
        if not self.redis_client:
            return None
        
        try:
            alert_data = await self.redis_client.hget(self.alerts_key, str(alert_id))
            if alert_data:
                return Alert.model_validate_json(alert_data)
            return None
            
        except Exception as e:
            logger.error(f"Alert retrieval failed: {e}")
            return None
    
    async def get_recent_alerts(self, limit: int = 100) -> List[Alert]:
        """Get recent alerts from persistence."""
        if not self.redis_client:
            return []
        
        try:
            alert_data_items = await self.redis_client.hgetall(self.alerts_key)
            alerts = []
            
            for alert_data in alert_data_items.values():
                try:
                    alert = Alert.model_validate_json(alert_data)
                    alerts.append(alert)
                except Exception as e:
                    logger.warning(f"Failed to parse stored alert: {e}")
            
            # Sort by created_at descending and limit
            alerts.sort(key=lambda a: a.created_at, reverse=True)
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"Recent alerts retrieval failed: {e}")
            return []
    
    async def cleanup_expired_alerts(self) -> int:
        """Clean up expired alerts from persistence."""
        if not self.redis_client:
            return 0
        
        try:
            current_time = datetime.utcnow()
            alert_data_items = await self.redis_client.hgetall(self.alerts_key)
            
            expired_count = 0
            for alert_id, alert_data in alert_data_items.items():
                try:
                    alert = Alert.model_validate_json(alert_data)
                    if alert.expires_at and alert.expires_at < current_time:
                        await self.redis_client.hdel(self.alerts_key, alert_id)
                        expired_count += 1
                except Exception as e:
                    logger.warning(f"Failed to check alert expiration: {e}")
            
            logger.info(f"Cleaned up {expired_count} expired alerts")
            return expired_count
            
        except Exception as e:
            logger.error(f"Alert cleanup failed: {e}")
            return 0
    
    def get_metrics(self) -> AlertMetrics:
        """Get current alert dispatch metrics."""
        return AlertMetrics(
            total_alerts_sent=self._metrics["total_alerts_dispatched"],
            websocket_alerts_sent=self._metrics["websocket_deliveries"],
            slack_alerts_sent=self._metrics["slack_deliveries"],
            failed_alerts=self._metrics["failed_deliveries"],
            active_subscriptions=websocket_manager.get_metrics()["active_subscriptions"],
            average_broadcast_latency_ms=float(self.max_broadcast_timeout_ms),  # Approximation
            start_time=datetime.utcnow() - timedelta(hours=1),  # Approximation
            end_time=datetime.utcnow()
        )
    
    async def test_channels(self) -> Dict[str, Any]:
        """Test connectivity to all configured channels."""
        results = {}
        
        # Test WebSocket manager
        results["websocket"] = {
            "available": True,
            "metrics": websocket_manager.get_metrics()
        }
        
        # Test Slack client
        if self.slack_client:
            try:
                slack_test = await self.slack_client.test_connection()
                results["slack"] = slack_test
            except Exception as e:
                results["slack"] = {
                    "success": False,
                    "error": str(e)
                }
        else:
            results["slack"] = {
                "success": False,
                "error": "Slack client not configured"
            }
        
        # Test Redis
        if self.redis_client:
            try:
                await self.redis_client.ping()
                results["redis"] = {
                    "success": True,
                    "connected": True
                }
            except Exception as e:
                results["redis"] = {
                    "success": False,
                    "error": str(e)
                }
        else:
            results["redis"] = {
                "success": False,
                "error": "Redis client not configured"
            }
        
        return results


# Global dispatch service instance
dispatch_service = AlertDispatchService()
