"""
Prometheus Monitoring for Alert Broadcasting System

Provides metrics instrumentation for alert throughput, failures, and latency tracking.
Exports metrics that can be scraped by Prometheus for monitoring and alerting.
"""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram, Info, generate_latest, CONTENT_TYPE_LATEST

from .models import Alert, AlertChannel, AlertPriority, AlertCategory

# Prometheus metrics for alert system
alerts_sent_total = Counter(
    'alerts_sent_total',
    'Total number of alerts sent successfully',
    ['channel', 'priority', 'category']
)

alerts_failed_total = Counter(
    'alerts_failed_total', 
    'Total number of failed alert deliveries',
    ['channel', 'priority', 'category', 'error_type']
)

broadcast_latency_ms = Histogram(
    'alert_broadcast_latency_milliseconds',
    'Time taken to broadcast alerts to all channels',
    ['channel', 'priority'],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
)

websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Current number of active WebSocket connections'
)

websocket_messages_sent = Counter(
    'websocket_messages_sent_total',
    'Total number of WebSocket messages sent',
    ['message_type']
)

slack_api_calls_total = Counter(
    'slack_api_calls_total',
    'Total number of Slack API calls made',
    ['endpoint', 'status']
)

slack_api_latency_ms = Histogram(
    'slack_api_latency_milliseconds',
    'Time taken for Slack API calls',
    ['endpoint'],
    buckets=[50, 100, 250, 500, 1000, 2500, 5000, 10000]
)

rate_limit_exceeded_total = Counter(
    'rate_limit_exceeded_total',
    'Total number of rate limit violations',
    ['limit_type', 'source']
)

alert_queue_size = Histogram(
    'alert_queue_size',
    'Number of alerts waiting in dispatch queue',
    buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500]
)

# System info metric
alerts_system_info = Info(
    'alerts_system_info',
    'Alert system configuration and version information'
)


def record_alert_sent(alert: Alert, channel: AlertChannel, latency_ms: float = None):
    """
    Record a successfully sent alert.
    
    Args:
        alert: Alert that was sent
        channel: Channel used for delivery
        latency_ms: Optional latency in milliseconds
    """
    labels = {
        'channel': channel.value,
        'priority': alert.priority.value,
        'category': alert.category.value
    }
    
    alerts_sent_total.labels(**labels).inc()
    
    if latency_ms is not None:
        broadcast_latency_ms.labels(
            channel=channel.value,
            priority=alert.priority.value
        ).observe(latency_ms)


def record_alert_failed(alert: Alert, channel: AlertChannel, error_type: str):
    """
    Record a failed alert delivery.
    
    Args:
        alert: Alert that failed to send
        channel: Channel that failed
        error_type: Type of error (e.g., 'network_error', 'rate_limited', 'invalid_config')
    """
    labels = {
        'channel': channel.value,
        'priority': alert.priority.value,
        'category': alert.category.value,
        'error_type': error_type
    }
    
    alerts_failed_total.labels(**labels).inc()


def record_websocket_connection():
    """Record a new WebSocket connection."""
    websocket_connections_active.inc()


def record_websocket_disconnection():
    """Record a WebSocket disconnection."""
    websocket_connections_active.dec()  # Decrement gauge


def record_websocket_message(message_type: str = "alert"):
    """
    Record a WebSocket message sent.
    
    Args:
        message_type: Type of message (alert, ping, pong, error, etc.)
    """
    websocket_messages_sent.labels(message_type=message_type).inc()


def record_slack_api_call(endpoint: str, status: str, latency_ms: float):
    """
    Record a Slack API call.
    
    Args:
        endpoint: Slack API endpoint called (e.g., 'chat.postMessage')
        status: Call status ('success', 'error', 'rate_limited')
        latency_ms: Call latency in milliseconds
    """
    slack_api_calls_total.labels(endpoint=endpoint, status=status).inc()
    slack_api_latency_ms.labels(endpoint=endpoint).observe(latency_ms)


def record_rate_limit_exceeded(limit_type: str, source: str):
    """
    Record a rate limit violation.
    
    Args:
        limit_type: Type of rate limit ('websocket', 'rest', 'slack')
        source: Source of the limit violation (IP, connection_id, etc.)
    """
    rate_limit_exceeded_total.labels(limit_type=limit_type, source=source).inc()


def record_queue_size(size: int):
    """
    Record current alert queue size.
    
    Args:
        size: Number of alerts waiting in queue
    """
    alert_queue_size.observe(size)


@asynccontextmanager
async def measure_operation(metric_histogram: Histogram, labels: Dict[str, str] = None):
    """
    Context manager to measure operation latency.
    
    Args:
        metric_histogram: Prometheus histogram to record to
        labels: Optional labels for the metric
        
    Usage:
        async with measure_operation(broadcast_latency_ms, {'channel': 'websocket'}):
            await send_alert_to_websocket(alert)
    """
    start_time = time.time()
    try:
        yield
    finally:
        latency_ms = (time.time() - start_time) * 1000
        if labels:
            metric_histogram.labels(**labels).observe(latency_ms)
        else:
            metric_histogram.observe(latency_ms)


def initialize_system_info():
    """Initialize system information metrics."""
    import os
    from datetime import datetime
    
    info_data = {
        'version': '8.4.0',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'redis_enabled': str(bool(os.getenv('REDIS_URL'))),
        'slack_enabled': str(bool(os.getenv('SLACK_BOT_TOKEN'))),
        'startup_time': datetime.utcnow().isoformat(),
        'max_websocket_connections': os.getenv('WEBSOCKET_MAX_CONNECTIONS_PER_USER', '5'),
        'heartbeat_interval': os.getenv('WEBSOCKET_HEARTBEAT_INTERVAL', '30')
    }
    
    alerts_system_info.info(info_data)


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get current metrics summary for debugging/admin purposes.
    
    Returns:
        Dict with current metric values
    """
    # Note: In production, you'd query the actual metric values
    # For now, return a summary structure
    return {
        'alerts_sent': 'See Prometheus /metrics endpoint',
        'alerts_failed': 'See Prometheus /metrics endpoint', 
        'active_connections': 'See Prometheus /metrics endpoint',
        'average_latency_ms': 'See Prometheus /metrics endpoint',
        'rate_limit_violations': 'See Prometheus /metrics endpoint',
        'metrics_endpoint': '/metrics',
        'prometheus_format': 'Available for scraping'
    }


def export_metrics() -> str:
    """
    Export metrics in Prometheus format.
    
    Returns:
        Metrics data in Prometheus exposition format
    """
    return generate_latest()


def get_metrics_content_type() -> str:
    """
    Get the content type for Prometheus metrics.
    
    Returns:
        Prometheus metrics content type
    """
    return CONTENT_TYPE_LATEST


# Initialize system info on module import
initialize_system_info()


# Example usage patterns:
#
# # Record successful alert
# record_alert_sent(alert, AlertChannel.WEBSOCKET, latency_ms=45.2)
#
# # Record failed alert
# record_alert_failed(alert, AlertChannel.SLACK, 'rate_limited')
#
# # Measure operation latency
# async with measure_operation(slack_api_latency_ms, {'endpoint': 'chat.postMessage'}):
#     await slack_client.send_message(channel, message)
#
# # Record rate limiting
# record_rate_limit_exceeded('websocket', connection_id)
#
# # Export metrics for Prometheus
# metrics_data = export_metrics()
# content_type = get_metrics_content_type()
