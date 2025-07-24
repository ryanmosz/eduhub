# EduHub API Documentation Structure

This document defines the structure and standards for EduHub API documentation.

## 📋 API Documentation Standards

### Documentation Hierarchy
```
docs/api/
├── overview.md              # API overview and getting started
├── authentication.md        # Auth flows and security
├── endpoints/              # Individual endpoint documentation
│   ├── content/
│   │   ├── list-content.md
│   │   ├── get-content.md
│   │   ├── create-content.md
│   │   ├── update-content.md
│   │   └── delete-content.md
│   ├── users/
│   │   ├── register.md
│   │   ├── login.md
│   │   ├── profile.md
│   │   └── permissions.md
│   └── search/
│       ├── content-search.md
│       └── user-search.md
├── schemas/                # Data models and schemas
│   ├── content-models.md
│   ├── user-models.md
│   └── error-responses.md
├── examples/               # Code examples and tutorials
│   ├── getting-started.md
│   ├── content-management.md
│   └── integration-examples.md
└── changelog/              # API version changes
    ├── v1.0.md
    └── migration-guides.md
```

## 🚀 API Overview Template

### Current API Status
- **Base URL**: `http://localhost:8000` (development)
- **API Version**: v1.0
- **Authentication**: JWT Bearer tokens
- **Content Type**: `application/json`
- **Rate Limiting**: TBD (Future implementation)

### Available Endpoints

#### Content Management
```http
# List content with search and filtering
GET    /content/
GET    /content/?query={search_term}&content_type={type}&limit={limit}

# Get specific content by path
GET    /content/{path}

# Create new content
POST   /content/

# Update existing content  
PUT    /content/{path}

# Delete content
DELETE /content/{path}
```

#### Plone Integration
```http
# Get Plone site information
GET    /plone/info

# Health check for Plone connectivity
GET    /health
```

#### Application
```http
# API root information
GET    /

# Application health check
GET    /health

# OpenAPI schema
GET    /openapi.json

# Interactive documentation
GET    /docs
GET    /redoc
```

## 📝 Endpoint Documentation Template

### Standard Endpoint Documentation Format

```markdown
# Endpoint Name

Brief description of what this endpoint does.

## Request

### HTTP Method and URL
```http
POST /api/v1/example/{id}
```

### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Unique identifier for the resource |

### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | integer | No | 25 | Maximum number of results |
| offset | integer | No | 0 | Number of results to skip |

### Headers
| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Yes | Bearer {token} |
| Content-Type | Yes | application/json |

### Request Body
```json
{
  "title": "Example Title",
  "description": "Example description",
  "metadata": {
    "category": "example",
    "tags": ["tag1", "tag2"]
  }
}
```

## Response

### Success Response (200 OK)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Example Title",
  "description": "Example description", 
  "created_at": "2024-01-20T10:30:00Z",
  "updated_at": "2024-01-20T10:30:00Z",
  "metadata": {
    "category": "example",
    "tags": ["tag1", "tag2"]
  }
}
```

### Error Responses
| Status Code | Description | Response Body |
|-------------|-------------|---------------|
| 400 | Bad Request | `{"detail": "Invalid request data"}` |
| 401 | Unauthorized | `{"detail": "Authentication required"}` |
| 403 | Forbidden | `{"detail": "Insufficient permissions"}` |
| 404 | Not Found | `{"detail": "Resource not found"}` |
| 500 | Internal Server Error | `{"detail": "Internal server error"}` |

## Examples

### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/example/123" \
  -H "Authorization: Bearer your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Example Title",
    "description": "Example description"
  }'
```

### Python Example
```python
import httpx

async def create_example():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/example/123",
            headers={
                "Authorization": "Bearer your_token_here",
                "Content-Type": "application/json"
            },
            json={
                "title": "Example Title",
                "description": "Example description"
            }
        )
        return response.json()
```

### JavaScript Example
```javascript
const response = await fetch('http://localhost:8000/api/v1/example/123', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your_token_here',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Example Title',
    description: 'Example description'
  })
});

const data = await response.json();
```
```

## 🔒 Authentication Documentation Template

### Authentication Overview
EduHub uses JWT (JSON Web Token) based authentication with integration to legacy Plone user management.

### Authentication Flow
```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant P as Plone
    
    C->>A: POST /auth/login {username, password}
    A->>P: Authenticate with Plone
    P->>A: User data + Plone token
    A->>A: Generate JWT token
    A->>C: JWT token + user info
    
    Note over C,A: For subsequent requests
    C->>A: API request with Authorization header
    A->>A: Validate JWT token
    A->>C: API response
```

### Token Format
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user-123",
    "username": "john_doe",
    "email": "john@example.com",
    "roles": ["authenticated"]
  }
}
```

### Using Authentication
```http
# Include in Authorization header
GET /api/v1/content/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 📊 Data Models Documentation Template

### Content Model
```json
{
  "uid": "string",           // Unique identifier from Plone
  "title": "string",         // Content title
  "description": "string",   // Optional content description
  "portal_type": "string",   // Plone content type (Document, News Item, etc.)
  "url": "string",          // Content URL/path
  "created": "datetime",     // Creation timestamp (ISO 8601)
  "modified": "datetime",    // Last modification timestamp (ISO 8601)
  "state": "string",        // Workflow state (published, private, etc.)
  "text": "string",         // Content body (HTML)
  "metadata": "object"      // Additional metadata from Plone
}
```

### User Model
```json
{
  "id": "string",           // Unique user identifier
  "username": "string",     // Username
  "email": "string",        // Email address
  "full_name": "string",    // Full display name
  "is_active": "boolean",   // Account active status
  "roles": ["string"],      // User roles/permissions
  "created_at": "datetime", // Account creation date
  "last_login": "datetime"  // Last login timestamp
}
```

### Error Response Model
```json
{
  "detail": "string",       // Error description
  "error_code": "string",   // Machine-readable error code
  "timestamp": "datetime",  // When the error occurred
  "path": "string",        // Request path that caused error
  "request_id": "string"   // Unique request identifier for debugging
}
```

## 🧪 Testing Documentation Template

### API Testing Examples

#### Unit Testing with pytest
```python
import pytest
from fastapi.testclient import TestClient
from eduhub.main import app

client = TestClient(app)

def test_get_content():
    response = client.get("/content/example-document")
    assert response.status_code == 200
    data = response.json()
    assert "uid" in data
    assert "title" in data
```

#### Integration Testing
```python
@pytest.mark.asyncio
async def test_plone_integration():
    async with PloneClient() as client:
        content = await client.get_content("example-document")
        assert content is not None
        assert content["title"] == "Expected Title"
```

## 📈 Performance Documentation Template

### Performance Characteristics
- **Average Response Time**: < 200ms for cached content
- **Throughput**: 1000+ requests/second (target)
- **Cache Hit Rate**: > 80% for content requests
- **Database Query Time**: < 50ms average

### Rate Limiting (Future)
```http
# Rate limit headers in responses
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642781400
```

## 🔄 Versioning Strategy

### API Versioning Approach
- **URL Versioning**: `/api/v1/`, `/api/v2/`
- **Backward Compatibility**: Maintain previous versions
- **Deprecation Notice**: 6-month deprecation cycle
- **Migration Guides**: Detailed upgrade documentation

### Version History
- **v1.0**: Initial API with Plone integration
- **v1.1**: (Future) Enhanced search capabilities
- **v2.0**: (Future) Microservices architecture

## 📚 SDK Documentation Template

### Official SDKs (Future)
- **Python**: `pip install eduhub-sdk`
- **JavaScript**: `npm install @eduhub/sdk`
- **PHP**: `composer require eduhub/sdk`

### SDK Usage Example
```python
from eduhub_sdk import EduHubClient

client = EduHubClient(
    base_url="https://api.eduhub.com",
    api_key="your_api_key"
)

# Get content
content = await client.content.get("document-path")

# Search content
results = await client.content.search(
    query="education",
    content_type="Document",
    limit=10
)
```

## 🔧 Development Guidelines

### API Design Principles
1. **RESTful Design**: Follow REST conventions
2. **Consistent Naming**: Use consistent endpoint naming
3. **Error Handling**: Provide clear error messages
4. **Documentation**: Keep documentation current
5. **Versioning**: Plan for API evolution

### Adding New Endpoints
1. **Design Review**: Architecture team approval
2. **OpenAPI Spec**: Define endpoint in OpenAPI
3. **Implementation**: Code with tests
4. **Documentation**: Complete endpoint documentation
5. **Review**: Code and documentation review

---

**This structure provides a comprehensive framework for documenting the EduHub API as it evolves and grows.** 