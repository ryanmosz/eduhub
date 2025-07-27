"""
Real-time Alert Broadcasting Module

Provides WebSocket-based real-time notifications and Slack integration
for broadcasting alerts to browser clients and external teams.

Key Components:
- WebSocket hub for browser client subscriptions
- Slack client for external team notifications  
- Alert dispatch service orchestrating multi-channel delivery
- Rate limiting and monitoring for production reliability
"""

from .models import Alert, AlertChannel, AlertPriority, Subscription

__all__ = [
    "Alert",
    "AlertChannel", 
    "AlertPriority",
    "Subscription",
] 