"""
FastAPI endpoints for real-time alert broadcasting system.

Provides REST API endpoints for alert management and WebSocket connections
for real-time browser notifications.
"""

import json
import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer

from ..auth.dependencies import get_alerts_write_user, get_current_user
from ..auth.models import User
from .models import Alert, AlertMetrics, AlertRequest, AlertResponse
from .rate_limit import alert_rest_rate_limit
from .services import AlertService

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()
security = HTTPBearer()

# Service instance
alert_service = AlertService()

# WebSocket connections store (for demo)
active_connections: List[WebSocket] = []


@router.post("/send", response_model=AlertResponse)
@alert_rest_rate_limit(
    max_requests=20, window_seconds=60
)  # 20 req/min as per task 8.4.1
async def send_alert(
    alert_request: AlertRequest,
    request: Request,
    current_user: User = Depends(get_alerts_write_user),
) -> AlertResponse:
    """
    Send a new alert to configured channels.

    Requires 'alerts:write' permission. Rate limited to 20 requests per minute per IP.
    """
    try:
        # Create alert from request
        alert = Alert(
            title=alert_request.title,
            message=alert_request.message,
            priority=alert_request.priority,
            category=alert_request.category,
            channels=alert_request.channels,
            source=f"api_user_{current_user.username}",
            user_id=alert_request.user_id,
            slack_channel=alert_request.slack_channel,
            metadata=alert_request.metadata,
        )

        # Dispatch alert
        sent_channels = await alert_service.dispatch_alert(alert)
        
        # Broadcast to WebSocket clients
        alert_data = json.dumps({
            "id": str(alert.id),
            "type": alert.priority.value if hasattr(alert.priority, 'value') else 'info',
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.created_at.isoformat() if hasattr(alert.created_at, 'isoformat') else str(alert.created_at),
        })
        
        # Send to all connected WebSocket clients
        disconnected = []
        for connection in active_connections:
            try:
                await connection.send_text(alert_data)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            active_connections.remove(conn)

        return AlertResponse(
            alert_id=alert.id,
            status="dispatched",
            channels_sent=sent_channels + ["websocket"],
            created_at=alert.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispatch alert: {str(e)}",
        )


@router.get("/test", response_model=dict)
@alert_rest_rate_limit(max_requests=20, window_seconds=60)  # For testing rate limits
async def test_endpoint(
    request: Request, current_user: User = Depends(get_current_user)
) -> dict:
    """
    Simple test endpoint for rate limiting validation.

    This endpoint is used primarily for testing rate limiting behavior.
    """
    return {
        "message": "Alert system test endpoint",
        "user": current_user.username,
        "timestamp": "2025-01-01T00:00:00Z",
    }


@router.get("/metrics", response_model=AlertMetrics)
async def get_metrics(current_user: User = Depends(get_current_user)) -> AlertMetrics:
    """
    Get alert system metrics.

    Returns metrics for monitoring dashboard. No rate limiting on monitoring endpoints.
    """
    return await alert_service.get_metrics()


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint for alert system.

    Returns system status. No authentication or rate limiting required.
    """
    return {"status": "healthy", "service": "alerts", "version": "1.0.0"}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert notifications.
    
    Clients connect here to receive real-time alerts.
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Connected to alert system",
            "timestamp": str(datetime.now())
        }))
        
        # Keep connection alive and wait for messages
        while True:
            # Wait for any message from client (heartbeat)
            data = await websocket.receive_text()
            
            # Send pong response for heartbeat
            if data == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": str(datetime.now())
                }))
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)
        await websocket.close()
