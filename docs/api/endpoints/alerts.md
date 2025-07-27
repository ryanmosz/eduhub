# Alert System API Endpoints

The EduHub alert system provides real-time broadcasting capabilities through both REST API and WebSocket connections. This system enables sending alerts to multiple channels (WebSocket clients and Slack) with rate limiting, authentication, and comprehensive monitoring.

## Authentication

All endpoints (except `/health`) require authentication:
- **Bearer Token**: JWT token with appropriate scopes
- **Required Scope**: `alerts:write` for sending alerts
- **Admin Roles**: `manager`, `admin`, `administrator` bypass scope requirements

## Rate Limiting

The alert system implements rate limiting to prevent abuse:
- **REST Endpoints**: 20 requests per minute per IP address
- **WebSocket Messages**: 10 messages per second per connection
- **429 Response**: Returns `Retry-After` header when rate limited

## Endpoints

### POST /alerts/send

Send a new alert to configured channels.

**Authentication**: Required (`alerts:write` scope)  
**Rate Limit**: 20 requests/minute per IP

#### Request Body

```json
{
  "title": "System Alert",
  "message": "Database maintenance scheduled for 2 AM",
  "priority": "high",
  "category": "system",
  "channels": ["websocket", "slack"]
}
```

#### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Alert title (1-200 characters) |
| `message` | string | Yes | Alert message content (1-1000 characters) |
| `priority` | enum | No | `low`, `medium`, `high`, `critical` (default: `medium`) |
| `category` | enum | Yes | `system`, `workflow`, `schedule`, `security` |
| `channels` | array | No | `["websocket", "slack"]` (default: `["websocket"]`) |

#### Response

**200 OK**
```json
{
  "alert_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "delivered",
  "channels_sent": ["websocket", "slack"],
  "created_at": "2025-01-15T10:30:00Z"
}
```

**403 Forbidden**
```json
{
  "detail": "Insufficient permissions. Required scope: alerts:write"
}
```

**429 Too Many Requests**
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 30
}
```

### GET /alerts/test

Simple test endpoint for rate limiting validation.

**Authentication**: Not required  
**Rate Limit**: 20 requests/minute per IP

#### Response

**200 OK**
```json
{
  "message": "Rate limiting test endpoint",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### GET /alerts/metrics

Get alert system metrics for monitoring.

**Authentication**: Not required  
**Rate Limit**: None

#### Response

**200 OK**
```json
{
  "alerts_sent_total": 1250,
  "alerts_failed_total": 23,
  "websocket_connections_active": 42,
  "total_websocket_messages": 5670,
  "slack_api_calls_total": 890,
  "rate_limit_violations": 15,
  "system_uptime_seconds": 86400
}
```

### GET /alerts/health

Health check endpoint for alert system monitoring.

**Authentication**: Not required  
**Rate Limit**: None

#### Response

**200 OK**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "websocket_manager": "operational",
    "slack_client": "operational",
    "redis": "optional",
    "prometheus": "operational"
  }
}
```

## WebSocket Connection

For real-time alert delivery, clients can connect via WebSocket:

**URL**: `ws://localhost:8000/ws/alerts`  
**Authentication**: JWT token via query parameter or headers

### Connection Example

```javascript
const token = "your-jwt-token";
const ws = new WebSocket(`ws://localhost:8000/ws/alerts?token=${token}`);

ws.onopen = () => {
    console.log("Connected to alert system");
};

ws.onmessage = (event) => {
    const alert = JSON.parse(event.data);
    console.log("New alert:", alert);
};
```

### Message Format

```json
{
  "type": "alert",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "System Alert",
    "message": "Database maintenance scheduled",
    "priority": "high",
    "category": "system",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error description",
  "error_code": "ALERTS_001",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `ALERTS_001` | Invalid alert data |
| `ALERTS_002` | Rate limit exceeded |
| `ALERTS_003` | Authentication required |
| `ALERTS_004` | Insufficient permissions |
| `ALERTS_005` | Delivery failure |

## Usage Examples

### Send Critical System Alert

```bash
curl -X POST "http://localhost:8000/alerts/send" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Database Connection Lost",
    "message": "Primary database connection failed. Failover initiated.",
    "priority": "critical",
    "category": "system",
    "channels": ["websocket", "slack"]
  }'
```

### Monitor System Health

```bash
curl "http://localhost:8000/alerts/health"
```

### Get Metrics for Dashboard

```bash
curl "http://localhost:8000/alerts/metrics"
```

## Rate Limiting Details

### REST API Limits
- **Window**: 1 minute sliding window
- **Limit**: 20 requests per IP address
- **Response**: 429 with `Retry-After` header
- **Reset**: Automatic after window expires

### WebSocket Limits
- **Window**: 1 second sliding window  
- **Limit**: 10 messages per connection
- **Response**: Error message sent to client
- **Disconnect**: After 3 consecutive violations

## Monitoring & Metrics

The alert system exposes comprehensive metrics for monitoring:

### Prometheus Metrics

- `alerts_sent_total{channel, priority, category}` - Total successful alerts
- `alerts_failed_total{channel, priority, category}` - Total failed alerts  
- `websocket_connections_active` - Current WebSocket connections
- `websocket_messages_sent{type}` - Total WebSocket messages sent
- `slack_api_calls_total{status}` - Slack API call status counters
- `rate_limit_exceeded_total{type}` - Rate limit violation counters
- `alert_broadcast_latency_milliseconds{channel, priority}` - Latency histogram

### Metrics Endpoint

Access raw Prometheus metrics:
```bash
curl "http://localhost:8000/metrics"
```

## Integration Examples

### React Frontend Integration

```typescript
import { useEffect, useState } from 'react';

const useAlerts = (token: string) => {
  const [alerts, setAlerts] = useState([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const websocket = new WebSocket(`ws://localhost:8000/ws/alerts?token=${token}`);
    
    websocket.onmessage = (event) => {
      const alert = JSON.parse(event.data);
      if (alert.type === 'alert') {
        setAlerts(prev => [alert.data, ...prev]);
      }
    };

    setWs(websocket);
    return () => websocket.close();
  }, [token]);

  const sendAlert = async (alertData) => {
    const response = await fetch('/alerts/send', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(alertData)
    });
    return response.json();
  };

  return { alerts, sendAlert };
};
```

### Python Client Integration

```python
import asyncio
import websockets
import json
import httpx

class AlertClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {"Authorization": f"Bearer {token}"}
    
    async def send_alert(self, title: str, message: str, **kwargs):
        """Send an alert via REST API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/alerts/send",
                headers=self.headers,
                json={
                    "title": title,
                    "message": message,
                    **kwargs
                }
            )
            return response.json()
    
    async def listen_alerts(self, callback):
        """Listen for real-time alerts via WebSocket."""
        uri = f"ws://localhost:8000/ws/alerts?token={self.token}"
        async with websockets.connect(uri) as websocket:
            async for message in websocket:
                alert = json.loads(message)
                await callback(alert)

# Usage
client = AlertClient("http://localhost:8000", "your-jwt-token")

# Send alert
await client.send_alert(
    title="Build Failed",
    message="CI/CD pipeline failed on branch main",
    priority="high",
    category="system"
)

# Listen for alerts
async def handle_alert(alert):
    print(f"New alert: {alert['data']['title']}")

await client.listen_alerts(handle_alert)
```

## Performance Considerations

### Scalability
- **WebSocket Connections**: Scales to ~1000 concurrent connections per instance
- **Message Throughput**: ~10,000 messages/second with rate limiting
- **Redis Backend**: Optional for horizontal scaling across instances

### Latency Targets
- **WebSocket Broadcast**: ≤ 50ms (local network)
- **Slack API**: ≤ 300ms (includes network latency)
- **REST API Response**: ≤ 100ms (excluding external calls)

### Resource Usage
- **Memory**: ~100MB baseline + 1KB per active WebSocket connection
- **CPU**: <5% under normal load (1000 messages/minute)
- **Network**: Minimal (JSON payloads typically <1KB) 