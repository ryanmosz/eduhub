# Open Data API Documentation

## Overview

The Open Data API provides public, read-only access to published CMS content through RESTful endpoints. The API is designed for high performance with aggressive caching and rate limiting.

## Base URL

```
https://api.eduhub.example.com/data
```

## Authentication

**No authentication required** - All endpoints are publicly accessible. However, rate limiting is enforced per IP address.

## Rate Limiting

- **Limit**: 60 requests per minute per IP address
- **Headers**: Rate limit information is included in response headers
- **429 Response**: When limit exceeded, includes `Retry-After` header

## Content Types

All endpoints return `application/json` and accept the following content types for published content:

- `Document` - Text documents and pages
- `News Item` - News articles and announcements
- `Event` - Calendar events and meetings
- `File` - Downloadable files
- `Image` - Image assets
- `Folder` - Content containers
- `Collection` - Content aggregations

## Security & Privacy

- Only **published** content is accessible
- Private, draft, or internal content is automatically filtered out
- Sensitive metadata fields are excluded from responses
- All responses are cached for performance

---

## Endpoints

### GET /data/items

List published content items with pagination and filtering.

#### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `search` | string | No | Search query (min 2 chars, max 100) | `"python programming"` |
| `portal_type` | string | No | Filter by content type | `"Document"` |
| `limit` | integer | No | Items per page (1-100, default 25) | `50` |
| `cursor` | string | No | Pagination cursor for next page | `"eyJvZmZzZXQ..."` |

#### Response Format

```json
{
  "items": [
    {
      "uid": "abc123-def456",
      "title": "Welcome to EduHub",
      "description": "Learn about our educational programs",
      "portal_type": "Document",
      "url": "https://eduhub.example.com/welcome",
      "created": "2024-01-15T10:30:00Z",
      "modified": "2024-01-20T14:45:00Z",
      "metadata": {
        "subject": ["education", "welcome"],
        "language": "en"
      }
    }
  ],
  "total": 150,
  "limit": 25,
  "offset": 0,
  "has_more": true,
  "next_cursor": "eyJvZmZzZXQiOjI1LCJ0aW1lc3RhbXAiOiIyMDI0In0="
}
```

#### Examples

**Basic request:**
```bash
curl "https://api.eduhub.example.com/data/items"
```

**Search for programming content:**
```bash
curl "https://api.eduhub.example.com/data/items?search=programming&limit=10"
```

**Filter by content type:**
```bash
curl "https://api.eduhub.example.com/data/items?portal_type=News%20Item"
```

**Paginate through results:**
```bash
curl "https://api.eduhub.example.com/data/items?cursor=eyJvZmZzZXQiOjI1LCJ0aW1lc3RhbXAiOiIyMDI0In0="
```

---

### GET /data/item/{uid}

Retrieve a specific content item by its unique identifier.

#### Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `uid` | string | Yes | Unique content identifier (min 3 chars) | `"abc123-def456"` |

#### Response Format

```json
{
  "uid": "abc123-def456",
  "title": "Welcome to EduHub",
  "description": "Learn about our comprehensive educational programs",
  "portal_type": "Document",
  "url": "https://eduhub.example.com/welcome",
  "created": "2024-01-15T10:30:00Z",
  "modified": "2024-01-20T14:45:00Z",
  "metadata": {
    "subject": ["education", "welcome"],
    "language": "en",
    "effective": "2024-01-15T10:30:00Z"
  }
}
```

#### Examples

**Get specific content item:**
```bash
curl "https://api.eduhub.example.com/data/item/abc123-def456"
```

---

## Error Responses

All error responses follow a consistent format:

```json
{
  "error": "error_type",
  "message": "Human-readable error description",
  "details": {
    "additional": "context"
  }
}
```

### Common Error Types

#### 422 Unprocessable Entity
Invalid request parameters.

```json
{
  "error": "invalid_parameters",
  "message": "Search query must be at least 2 characters",
  "details": {
    "parameter": "search",
    "value": "a"
  }
}
```

#### 404 Not Found
Content item not found or not public.

```json
{
  "error": "not_found",
  "message": "Content item with UID 'xyz789' not found or not public",
  "details": {
    "uid": "xyz789"
  }
}
```

#### 429 Too Many Requests
Rate limit exceeded.

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded: 60 requests per minute",
  "details": {
    "limit": 60,
    "window_seconds": 60,
    "retry_after": 30
  }
}
```

#### 500 Internal Server Error
Server-side error occurred.

```json
{
  "error": "internal_error",
  "message": "An internal error occurred while fetching content",
  "details": {
    "endpoint": "list_items"
  }
}
```

---

## Usage Examples

### JavaScript (Fetch API)

```javascript
// List recent news items
async function getNews() {
  const response = await fetch(
    'https://api.eduhub.example.com/data/items?portal_type=News%20Item&limit=10'
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.items;
}

// Get specific content
async function getContent(uid) {
  const response = await fetch(
    `https://api.eduhub.example.com/data/item/${uid}`
  );

  if (response.status === 404) {
    return null; // Content not found
  }

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// Handle pagination
async function getAllDocuments() {
  let allItems = [];
  let cursor = null;

  do {
    const url = cursor
      ? `https://api.eduhub.example.com/data/items?portal_type=Document&cursor=${cursor}`
      : 'https://api.eduhub.example.com/data/items?portal_type=Document';

    const response = await fetch(url);
    const data = await response.json();

    allItems.push(...data.items);
    cursor = data.has_more ? data.next_cursor : null;

  } while (cursor);

  return allItems;
}
```

### Python (requests)

```python
import requests
from typing import List, Dict, Optional

class OpenDataClient:
    def __init__(self, base_url: str = "https://api.eduhub.example.com"):
        self.base_url = base_url

    def list_items(
        self,
        search: Optional[str] = None,
        portal_type: Optional[str] = None,
        limit: int = 25,
        cursor: Optional[str] = None
    ) -> Dict:
        """List content items with filtering."""
        params = {"limit": limit}

        if search:
            params["search"] = search
        if portal_type:
            params["portal_type"] = portal_type
        if cursor:
            params["cursor"] = cursor

        response = requests.get(f"{self.base_url}/data/items", params=params)
        response.raise_for_status()
        return response.json()

    def get_item(self, uid: str) -> Optional[Dict]:
        """Get specific content item by UID."""
        response = requests.get(f"{self.base_url}/data/item/{uid}")

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()

    def search_all(self, query: str, portal_type: Optional[str] = None) -> List[Dict]:
        """Search all content, handling pagination automatically."""
        all_items = []
        cursor = None

        while True:
            data = self.list_items(
                search=query,
                portal_type=portal_type,
                cursor=cursor
            )

            all_items.extend(data["items"])

            if not data["has_more"]:
                break

            cursor = data["next_cursor"]

        return all_items

# Usage examples
client = OpenDataClient()

# Get recent news
news = client.list_items(portal_type="News Item", limit=10)
print(f"Found {len(news['items'])} news items")

# Search for programming content
programming_docs = client.search_all("programming", portal_type="Document")
print(f"Found {len(programming_docs)} programming documents")

# Get specific content
content = client.get_item("abc123-def456")
if content:
    print(f"Title: {content['title']}")
else:
    print("Content not found")
```

### cURL Examples

```bash
# Basic listing
curl -X GET "https://api.eduhub.example.com/data/items" \
  -H "Accept: application/json"

# Search with pagination
curl -X GET "https://api.eduhub.example.com/data/items?search=education&limit=5" \
  -H "Accept: application/json"

# Get specific item
curl -X GET "https://api.eduhub.example.com/data/item/abc123-def456" \
  -H "Accept: application/json"

# Filter by type
curl -X GET "https://api.eduhub.example.com/data/items?portal_type=Event" \
  -H "Accept: application/json"

# Handle errors gracefully
curl -X GET "https://api.eduhub.example.com/data/item/nonexistent" \
  -H "Accept: application/json" \
  -w "HTTP Status: %{http_code}\n"
```

---

## Performance & Caching

### Cache Behavior

- **Cache Duration**: 1 hour for list endpoints, 2 hours for individual items
- **Cache Keys**: Based on all query parameters
- **Cache Hits**: ~10ms response time
- **Cache Misses**: ~50ms response time

### Performance Tips

1. **Use appropriate page sizes**: Balance between too many requests and large payloads
2. **Leverage caching**: Identical requests within cache window are served instantly
3. **Use cursors for pagination**: More efficient than offset-based pagination
4. **Filter early**: Use `portal_type` to reduce result sets
5. **Implement client-side caching**: Cache responses on your end for better UX

### Rate Limiting Best Practices

1. **Respect rate limits**: Monitor response headers for limit information
2. **Implement exponential backoff**: When hitting rate limits, back off gracefully
3. **Batch requests efficiently**: Use pagination to get multiple items efficiently
4. **Cache aggressively**: Reduce API calls by caching on your end

---

## Integration with Plone CMS

The Open Data API integrates seamlessly with Plone CMS:

### Content Synchronization

- **Real-time**: Content changes in Plone appear in API within cache TTL
- **Automatic filtering**: Only published content is exposed
- **Metadata mapping**: Plone fields are mapped to public-safe schema

### Supported Plone Features

- **Workflow states**: Only "published" and "public" content is included
- **Content types**: All standard Plone content types supported
- **Search**: Integrated with Plone's search infrastructure
- **Metadata**: Safe subset of Plone metadata fields

### Content Security

- **Publication workflow**: Respects Plone's publication workflow
- **Field filtering**: Sensitive fields are automatically excluded
- **Access control**: Private content is never exposed

---

## Troubleshooting

### Common Issues

**Q: I'm getting 422 errors for search queries**
A: Ensure search queries are at least 2 characters and no more than 100 characters.

**Q: Content isn't appearing in search results**
A: Check that content is published in Plone and not marked as "exclude from navigation".

**Q: Rate limit errors (429)**
A: Implement exponential backoff and consider caching responses client-side.

**Q: Pagination isn't working correctly**
A: Use the `next_cursor` value from previous responses, don't construct cursors manually.

**Q: Getting 500 errors**
A: Check server status and try again. If persistent, contact support.

### Getting Help

- **Documentation**: [API Reference](https://api.eduhub.example.com/docs)
- **Status Page**: [status.eduhub.example.com](https://status.eduhub.example.com)
- **Support**: [support@eduhub.example.com](mailto:support@eduhub.example.com)

---

## Changelog

### v1.0.0 (2024-01-26)
- Initial release
- List and get item endpoints
- Cursor-based pagination
- Rate limiting (60 req/min)
- Comprehensive caching
- Full Plone CMS integration
