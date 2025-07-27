"""
Pydantic models for real-time alert broadcasting system.

Defines the core data structures for alerts, subscriptions, and configurations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AlertPriority(str, Enum):
    """Alert priority levels."""
    
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Available alert delivery channels."""
    
    WEBSOCKET = "websocket"
    SLACK = "slack"
    EMAIL = "email"  # Future extension


class AlertCategory(str, Enum):
    """Alert categories for filtering and routing."""
    
    SYSTEM = "system"
    WORKFLOW = "workflow"
    SCHEDULE = "schedule"
    CONTENT = "content"
    SECURITY = "security"


class Alert(BaseModel):
    """Core alert model for multi-channel broadcasting."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique alert identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Alert title")
    message: str = Field(..., min_length=1, max_length=1000, description="Alert message content")
    priority: AlertPriority = Field(default=AlertPriority.MEDIUM, description="Alert priority level")
    category: AlertCategory = Field(..., description="Alert category")
    channels: List[AlertChannel] = Field(default=[AlertChannel.WEBSOCKET], description="Target delivery channels")
    
    # Metadata
    source: str = Field(..., description="Source system/component generating the alert")
    user_id: Optional[str] = Field(None, description="Target user ID (if user-specific)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional alert metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Alert creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Alert expiration timestamp")
    
    # Slack-specific fields
    slack_channel: Optional[str] = Field(None, description="Target Slack channel (if using Slack)")
    slack_thread_ts: Optional[str] = Field(None, description="Slack thread timestamp for replies")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Subscription(BaseModel):
    """WebSocket subscription configuration."""
    
    id: UUID = Field(default_factory=uuid4, description="Subscription identifier")
    user_id: str = Field(..., description="Subscribed user ID")
    categories: List[AlertCategory] = Field(default_factory=list, description="Subscribed alert categories")
    priorities: List[AlertPriority] = Field(default_factory=list, description="Subscribed priority levels")
    
    # Connection metadata
    connection_id: str = Field(..., description="WebSocket connection identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Subscription creation time")
    last_ping: Optional[datetime] = Field(None, description="Last heartbeat timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class AlertRequest(BaseModel):
    """Request model for creating new alerts via REST API."""
    
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    priority: AlertPriority = AlertPriority.MEDIUM
    category: AlertCategory
    channels: List[AlertChannel] = [AlertChannel.WEBSOCKET]
    
    # Optional targeting
    user_id: Optional[str] = None
    slack_channel: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Optional expiration
    expires_in_seconds: Optional[int] = Field(None, ge=1, le=86400, description="Expiration in seconds (max 24h)")


class AlertResponse(BaseModel):
    """Response model for alert operations."""
    
    alert_id: UUID
    status: str = "dispatched"
    channels_sent: List[AlertChannel]
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class SubscriptionRequest(BaseModel):
    """Request model for WebSocket subscription management."""
    
    categories: List[AlertCategory] = Field(default_factory=list)
    priorities: List[AlertPriority] = Field(default_factory=list)


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    
    type: str = Field(..., description="Message type (alert, ping, pong, subscribe)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AlertMetrics(BaseModel):
    """Metrics model for monitoring dashboard."""
    
    total_alerts_sent: int = 0
    websocket_alerts_sent: int = 0
    slack_alerts_sent: int = 0
    failed_alerts: int = 0
    active_subscriptions: int = 0
    average_broadcast_latency_ms: float = 0.0
    
    # Time window for metrics
    start_time: datetime
    end_time: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 