# oEmbed Rich Media Embeds API

Transform URLs from supported providers into rich embedded content using the oEmbed protocol with security, caching, and authentication.

## 🎯 Quick Start

```http
GET /embed/?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&maxwidth=800&maxheight=450
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```

**Response:**
```json
{
  "html": "<iframe src=\"https://www.youtube.com/embed/dQw4w9WgXcQ\" width=\"560\" height=\"315\" frameborder=\"0\" allowfullscreen></iframe>",
  "title": "Rick Astley - Never Gonna Give You Up (Video)",
  "provider_name": "YouTube",
  "provider_url": "https://www.youtube.com/",
  "width": 560,
  "height": 315,
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  "cached": true
}
```

## 📋 API Endpoints

### `GET /embed/` - Embed URL as Rich Media

Transform a URL from supported providers into rich embedded content.

#### Authentication Required
- **Method**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer {your_jwt_token}`

#### Request Parameters

| Parameter | Type | Required | Constraints | Description |
|-----------|------|----------|-------------|-------------|
| `url` | string | **Yes** | Valid HTTP/HTTPS URL | URL to embed from supported provider |
| `maxwidth` | integer | No | 200-1920 | Maximum width of embed in pixels |
| `maxheight` | integer | No | 200-1080 | Maximum height of embed in pixels |

#### Example Requests

**Basic YouTube Embed:**
```http
GET /embed/?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Custom Dimensions:**
```http
GET /embed/?url=https://vimeo.com/123456789&maxwidth=800&maxheight=450
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Success Response (200 OK)

```json
{
  "html": "<iframe src=\"https://www.youtube.com/embed/dQw4w9WgXcQ\" width=\"560\" height=\"315\" frameborder=\"0\" allowfullscreen></iframe>",
  "title": "Rick Astley - Never Gonna Give You Up (Video)",
  "provider_name": "YouTube",
  "provider_url": "https://www.youtube.com/",
  "width": 560,
  "height": 315,
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  "cached": true
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `html` | string | Sanitized HTML embed code ready for injection |
| `title` | string \| null | Title of the embedded content |
| `provider_name` | string \| null | Name of the oEmbed provider |
| `provider_url` | string \| null | URL of the oEmbed provider |
| `width` | integer \| null | Width of the embed in pixels |
| `height` | integer \| null | Height of the embed in pixels |
| `thumbnail_url` | string \| null | URL of thumbnail image for the content |
| `cached` | boolean | Whether response was served from cache |

#### Error Responses

**422 Unprocessable Entity - Invalid URL or Unsupported Provider**
```json
{
  "error": "provider_not_allowed",
  "message": "Domain 'example.com' is not in the list of supported providers",
  "url": "https://example.com/video"
}
```

**429 Too Many Requests - Rate Limit Exceeded**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit of 20 requests per minute exceeded",
  "url": "https://www.youtube.com/watch?v=example"
}
```

**504 Gateway Timeout - Provider Timeout**
```json
{
  "error": "provider_timeout",
  "message": "Provider request timed out",
  "url": "https://www.youtube.com/watch?v=example"
}
```

### `GET /embed/providers` - List Supported Providers

Get comprehensive information about supported oEmbed providers.

#### Request
```http
GET /embed/providers
Authorization: Bearer YOUR_JWT_TOKEN
```

#### Response (200 OK)
```json
{
  "providers": [
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "soundcloud.com",
    "spotify.com",
    "codepen.io",
    "github.com"
  ],
  "count": 10,
  "features": {
    "caching": "Redis-backed with configurable TTL",
    "rate_limiting": "20 requests/minute per authenticated user",
    "security": "Domain allow-list + HTML sanitization",
    "formats": "JSON response with sanitized HTML embed code"
  },
  "examples": {
    "youtube": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "vimeo": "https://vimeo.com/123456789",
    "twitter": "https://twitter.com/user/status/123456789"
  }
}
```

### `GET /embed/health` - Service Health Check

Check the health and status of the oEmbed service.

#### Request
```http
GET /embed/health
```

#### Response (200 OK)
```json
{
  "status": "healthy",
  "service": "oembed-proxy",
  "version": "0.1.0",
  "providers_configured": 10,
  "features": {
    "validation": "enabled",
    "caching": "enabled",
    "rate_limiting": "enabled",
    "sanitization": "enabled"
  }
}
```

### `GET /embed/cache/stats` - Cache Statistics

Get detailed cache performance metrics and statistics.

#### Request
```http
GET /embed/cache/stats
Authorization: Bearer YOUR_JWT_TOKEN
```

#### Response (200 OK)
```json
{
  "status": "healthy",
  "cache_type": "redis_with_memory_fallback",
  "redis_available": true,
  "redis_url": "redis://localhost:6379/0",
  "ttl_seconds": 3600,
  "ttl_human": "1h 0m",
  "redis_cache_size": 150,
  "memory_cache_size": 25,
  "total_cached_entries": 175,
  "configuration": {
    "OEMBED_CACHE_TTL": 3600,
    "REDIS_URL": "redis://localhost:6379/0",
    "fallback_mode": "none"
  }
}
```

## 🛡️ Security Features

### Domain Allow-List
Only URLs from pre-approved providers are processed:

**Supported Domains:**
- `youtube.com`, `youtu.be` - YouTube videos
- `vimeo.com` - Vimeo videos
- `twitter.com`, `x.com` - Twitter/X posts
- `instagram.com` - Instagram posts
- `soundcloud.com` - SoundCloud tracks
- `spotify.com` - Spotify content
- `codepen.io` - CodePen demos
- `github.com` - GitHub repositories

### HTML Sanitization
All returned HTML is sanitized using `bleach` to remove:
- `<script>` tags and JavaScript
- Malicious attributes and URLs
- Non-allowlisted HTML elements

### Rate Limiting
- **Limit**: 20 requests per minute per authenticated user
- **Scope**: Per IP address + JWT user ID
- **Headers**: Rate limit info included in response headers

### Authentication
- **Required**: Valid JWT token for all endpoints (except `/health`)
- **Format**: `Authorization: Bearer {jwt_token}`
- **Integration**: Validates against existing Auth0 user authentication

## ⚡ Performance & Caching

### Cache Strategy
- **Primary**: Redis-backed cache (if available)
- **Fallback**: In-memory Python dictionary cache
- **TTL**: Configurable (default: 1 hour)
- **Key Format**: SHA-256 hash of URL + parameters

### Cache Behavior
- **Cache Hit**: Response served in < 10ms
- **Cache Miss**: External provider call + cache storage
- **Cache Status**: Indicated in response `cached` field

### Performance Targets
- **Cache Hit Latency**: < 10ms
- **Cache Miss Latency**: < 300ms (with external provider call)
- **Throughput**: 100+ requests/second with caching

## 📝 Usage Examples

### Python with httpx
```python
import httpx
import asyncio

async def embed_youtube_video():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/embed/",
            params={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "maxwidth": 800,
                "maxheight": 450
            },
            headers={
                "Authorization": "Bearer YOUR_JWT_TOKEN"
            }
        )

        if response.status_code == 200:
            embed_data = response.json()
            print(f"Title: {embed_data['title']}")
            print(f"HTML: {embed_data['html']}")
            return embed_data
        else:
            print(f"Error: {response.status_code} - {response.text}")

# Run the example
asyncio.run(embed_youtube_video())
```

### JavaScript/TypeScript
```javascript
async function embedContent(url, maxwidth = 800, maxheight = 450) {
  try {
    const response = await fetch(`/embed/?url=${encodeURIComponent(url)}&maxwidth=${maxwidth}&maxheight=${maxheight}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const embedData = await response.json();

    // Inject HTML into page
    document.getElementById('embed-container').innerHTML = embedData.html;

    return embedData;
  } catch (error) {
    console.error('Error embedding content:', error);
    throw error;
  }
}

// Usage examples
embedContent('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
embedContent('https://vimeo.com/123456789', 1200, 675);
```

### cURL
```bash
# Basic embed request
curl -X GET "http://localhost:8000/embed/?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# Custom dimensions
curl -X GET "http://localhost:8000/embed/?url=https://vimeo.com/123456789&maxwidth=1200&maxheight=675" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get provider list
curl -X GET "http://localhost:8000/embed/providers" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check service health
curl -X GET "http://localhost:8000/embed/health"
```

## 🔗 Integration with Plone Content

### Automatic Embed Injection
When creating or updating Plone content, URLs are automatically detected and converted to embeds:

```python
# Example: Creating content with embedded media
content_data = {
    "title": "My Video Tutorial",
    "text": """
    <p>Check out this great tutorial:</p>
    <p>https://www.youtube.com/watch?v=dQw4w9WgXcQ</p>
    <p>Also see this Vimeo video: https://vimeo.com/123456789</p>
    """
}

# The content processor will automatically convert URLs to rich embeds
```

### Manual Embed Integration
For custom integrations, use the embed endpoint to process URLs:

```python
from eduhub.oembed.client import get_oembed_client

async def process_content_embeds(content_text):
    """Process content and replace URLs with embed HTML."""
    client = await get_oembed_client()

    # URL detection logic here
    urls = extract_urls(content_text)

    for url in urls:
        try:
            embed_data = await client.fetch_embed(url)
            content_text = content_text.replace(url, embed_data['html'])
        except Exception as e:
            print(f"Failed to embed {url}: {e}")

    return content_text
```

## 🚨 Error Handling

### Common Error Scenarios

**Invalid URL Format:**
```json
{
  "error": "invalid_url_format",
  "message": "The provided URL is not a valid HTTP/HTTPS URL",
  "url": "not-a-valid-url"
}
```

**Unsupported Provider:**
```json
{
  "error": "provider_not_allowed",
  "message": "Domain 'example.com' is not in the list of supported providers",
  "url": "https://example.com/video"
}
```

**Provider Service Down:**
```json
{
  "error": "provider_unavailable",
  "message": "Provider service unavailable",
  "url": "https://www.youtube.com/watch?v=example"
}
```

**Network Timeout:**
```json
{
  "error": "provider_timeout",
  "message": "Provider request timed out",
  "url": "https://www.youtube.com/watch?v=example"
}
```

### Error Handling Best Practices

1. **Check Status Codes**: Always verify HTTP status before processing response
2. **Parse Error Messages**: Use `error` field for programmatic handling
3. **Graceful Degradation**: Fall back to plain URL display on embed failure
4. **Retry Logic**: Implement exponential backoff for temporary failures
5. **User Feedback**: Show meaningful error messages to users

## 📊 Monitoring & Analytics

### Available Metrics
- **Request Volume**: Total embed requests per time period
- **Cache Hit Rate**: Percentage of requests served from cache
- **Provider Response Times**: Latency by provider
- **Error Rates**: Failed requests by error type
- **Popular Content**: Most embedded URLs

### Health Monitoring
```bash
# Check overall service health
curl http://localhost:8000/embed/health

# Get detailed cache statistics
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/embed/cache/stats

# Monitor via logs
tail -f logs/oembed.log | grep "ERROR\|WARN"
```

## 🔧 Configuration

### Environment Variables
```bash
# Cache configuration
OEMBED_CACHE_TTL=3600          # Cache TTL in seconds
REDIS_URL=redis://localhost:6379/0  # Redis connection string

# Security settings
OEMBED_RATE_LIMIT_REQUESTS=20  # Requests per minute per user
OEMBED_RATE_LIMIT_WINDOW=60    # Rate limit window in seconds

# Provider timeouts
OEMBED_REQUEST_TIMEOUT=10      # Request timeout in seconds
OEMBED_CONNECT_TIMEOUT=5       # Connection timeout in seconds
```

### Provider Configuration
To add new providers, update the allowed domains list in `src/eduhub/oembed/endpoints.py`:

```python
ALLOWED_PROVIDERS = {
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "soundcloud.com",
    "spotify.com",
    "codepen.io",
    "github.com",
    # Add new providers here
}
```

## 📚 Related Documentation

- **[Authentication Setup](../../getting-started/authentication-setup.md)** - JWT token configuration
- **[System Architecture](../../architecture/system-architecture.md)** - Overall system design
- **[Testing Strategy](../../development/testing-strategy.md)** - Testing methodology
- **[OpenAPI Documentation](http://localhost:8000/docs)** - Interactive API explorer

## 🆕 Changelog

### Version 0.1.0 (Current)
- ✅ Initial oEmbed proxy implementation
- ✅ 10 supported providers (YouTube, Vimeo, Twitter, etc.)
- ✅ Redis-backed caching with memory fallback
- ✅ JWT authentication integration
- ✅ Rate limiting (20 requests/minute per user)
- ✅ HTML sanitization security
- ✅ Comprehensive test coverage (≥90%)

### Planned Features
- 🔄 Additional providers (TikTok, LinkedIn, etc.)
- 🔄 Webhook support for cache invalidation
- 🔄 Analytics dashboard
- 🔄 Custom embed templates
- 🔄 Batch embed processing

---

**💡 Need Help?** Check the [interactive API documentation](http://localhost:8000/docs) for live testing, or review the [getting started guide](../../getting-started/developer-onboarding.md) for setup assistance.
