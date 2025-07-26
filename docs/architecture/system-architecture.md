# EduHub Architecture Documentation

> **Executive Summary**
> EduHub is a *modern shell* (FastAPI + async Python 3.11, Docker-first) wrapped **around** a proven but aging **Plone CMS** core.
> All new functionality—APIs, auth, CSV import, real-time alerts, React SPA—is built in the modern layer, while content &
> workflow logic stay in Plone.  A lightweight HTTP bridge keeps the two worlds in sync so we can ship user-visible wins
> in days (not months) without a risky big-bang migration.

This document outlines the architectural decisions, technical design, and system integration patterns for the EduHub modern education portal.

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architectural Principles](#architectural-principles)
3. [Technology Stack](#technology-stack)
4. [System Architecture](#system-architecture)
5. [Integration Patterns](#integration-patterns)
6. [Data Architecture](#data-architecture)
7. [Security Architecture](#security-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Quality Assurance](#quality-assurance)
10. [Performance Considerations](#performance-considerations)
11. [Scalability Design](#scalability-design)
12. [Technical Decisions](#technical-decisions)

## 🎯 System Overview

EduHub modernizes a legacy Plone CMS and Django application into a contemporary education platform while preserving existing content and functionality.

### Core Objectives
- **Legacy Preservation**: Maintain access to existing Plone content **via a thin async HTTP bridge (PloneClient)**.
- **Modern Interface**: Provide contemporary web experience **through FastAPI endpoints and a React Admin SPA**.
- **API-First Design**: Enable future integrations and frontend flexibility **(REST + upcoming GraphQL)**.
- **Scalable Foundation**: Support growth and feature evolution **using Docker, container PaaS (Render), and stateless design**.
- **Developer Experience**: Ensure maintainable, testable codebase **with Python 3.11, type hints, and automated CI gates**.

### Strategic Approach
```mermaid
graph TB
    subgraph "Legacy System"
        A[Plone CMS 6.1] --> B[Existing Content]
        A --> C[User Management]
        A --> D[Workflow Engine]
    end

    subgraph "Bridge Layer"
        E[FastAPI Integration] --> F[REST API Translation]
        E --> G[Authentication Bridge]
        E --> H[Content Transformation]
    end

    subgraph "Modern Layer"
        I[React Frontend] --> J[Modern UI/UX]
        I --> K[Responsive Design]
        I --> L[Interactive Features]
    end

    A --> E
    E --> I
```

## 🏗️ Architectural Principles

### 1. **Evolutionary Architecture**
- **Gradual Migration**: Incremental modernization without big-bang replacement
- **Backward Compatibility**: Maintain existing functionality during transition
- **Feature Parity**: Ensure modern layer matches legacy capabilities
- **Future Flexibility**: Design for easy addition of new features

### 2. **API-First Design**
- **Decoupled Systems**: Separate frontend and backend concerns
- **Multiple Clients**: Support web, mobile, and integration consumers
- **Versioning Strategy**: Maintain API compatibility across updates
- **Documentation Driven**: OpenAPI specifications guide development

### 3. **Quality by Design**
- **Automated Testing**: Comprehensive test coverage at all levels
- **Code Quality**: Enforced standards via CI/CD pipeline
- **Security First**: Built-in security scanning and best practices
- **Performance Monitoring**: Observability and metrics collection

### 4. **Cloud-Native Principles**
- **Containerization**: Docker-first development and deployment
- **Microservices Ready**: Modular design enabling service extraction
- **Stateless Design**: Horizontal scaling capabilities
- **Environment Parity**: Consistent dev/staging/production environments

## 🔧 Technology Stack

### Backend Technologies
```yaml
Core Framework: FastAPI 0.115+
Language: Python 3.9+ (development on 3.13)
Database: PostgreSQL 14+
Cache: Redis 7+
Task Queue: Celery 5.4+
ORM: SQLAlchemy 2.0+
Migrations: Alembic 1.14+
HTTP Client: httpx 0.28+ (async)
Validation: Pydantic 2.10+
```

### Legacy Integration
```yaml
CMS: Plone 6.1
Integration: REST API bridge
Authentication: Token-based auth
Content Access: HTTP client with connection pooling
Data Format: JSON transformation layer
```

### Development Tools
```yaml
Package Management: pip + pyproject.toml
Code Formatting: Black 24.0+
Import Sorting: isort 5.13+
Type Checking: MyPy 1.13+
Testing: pytest 8.3+ with asyncio support
Coverage: pytest-cov 6.0+
Security: Safety + Bandit
Multi-env Testing: tox 4.23+
Pre-commit: pre-commit 4.0+
```

### Infrastructure
```yaml
Containerization: Docker + Docker Compose
CI/CD: GitHub Actions
Registry: Docker Hub
Monitoring: (Future: Prometheus + Grafana)
Logging: (Future: ELK Stack)
```

## 🏛️ System Architecture

### High-Level Architecture
```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser] --> B[React SPA]
        C[Mobile App] --> D[Native UI]
        E[API Clients] --> F[Integration Layer]
    end

    subgraph "API Gateway Layer"
        G[FastAPI Application]
        H[Authentication Middleware]
        I[Rate Limiting]
        J[Request Validation]
    end

    subgraph "Service Layer"
        K[Content Service] --> L[Plone Integration]
        M[User Service] --> N[Auth Provider]
        O[Search Service] --> P[Search Engine]
        Q[Notification Service] --> R[Message Queue]
    end

    subgraph "Data Layer"
        S[PostgreSQL] --> T[Application Data]
        U[Redis] --> V[Cache + Sessions]
        W[Plone CMS] --> X[Legacy Content]
    end

    subgraph "Infrastructure"
        Y[Docker Compose] --> Z[Local Development]
        AA[Kubernetes] --> BB[Production Deployment]
    end

    B --> G
    D --> G
    F --> G

    G --> H
    H --> I
    I --> J

    J --> K
    J --> M
    J --> O
    J --> Q

    K --> S
    M --> S
    O --> S
    Q --> U

    L --> W
```

### Service Architecture
```mermaid
graph LR
    subgraph "FastAPI Services"
        A[Main Application] --> B[Content API]
        A --> C[User API]
        A --> D[Search API]
        A --> E[Admin API]
    end

    subgraph "Integration Services"
        F[Plone Bridge] --> G[Content Sync]
        F --> H[Auth Integration]
        F --> I[Media Handling]
    end

    subgraph "Background Services"
        J[Celery Worker] --> K[Content Processing]
        J --> L[Email Notifications]
        J --> M[Report Generation]
    end

    B --> F
    C --> H
    D --> G
    E --> F

    F --> J
```

## 🧩 Legacy Integration with Plone

EduHub treats Plone as a *system-of-record* and surfaces its data through a **Bridge Layer**:

| Layer | Responsibility | Key Module / File |
|-------|----------------|-------------------|
| FastAPI Adapter | Defines REST endpoints consumed by React, CSV importer, etc. | `src/eduhub/main.py` |
| PloneClient | Async HTTP client, token auth, retry & error handling | `src/eduhub/plone_integration.py` |
| Transformation | Converts Plone’s JSON (ZODB) shape → `PloneContent` Pydantic model | `transform_plone_content()` |
| Auth Mapping | (Phase 3) Maps Auth0 user → Plone user/roles | `auth/plone_bridge.py` *(planned)* |

**Request Flow**

```mermaid
sequenceDiagram
    participant UI as React / Swagger / CLI
    participant API as FastAPI Layer
    participant Bridge as PloneClient
    participant Plone as Plone CMS

    UI->>API: GET /content/?query=Math
    API->>Bridge: search_content(...)
    Bridge->>Plone: /Plone/@search?q=Math
    Plone-->>Bridge: JSON results
    Bridge-->>API: Parsed dict
    API-->>UI: List[PloneContent] (JSON)
```

**Why this matters**

1. **Zero data duplication** – avoids multi-source-of-truth problems.
2. **Incremental rollout** – we can re-platform feature-by-feature while editors keep using Plone UI.
3. **Performance** – async httpx + Redis caching (future) keep latency sub-2 ms (see benchmark report).

## 🔗 Integration Patterns

### Plone Integration Strategy

#### 1. **API Bridge Pattern**
```python
# PloneClient provides unified interface to legacy CMS
class PloneClient:
    async def get_content(self, path: str) -> Dict[str, Any]
    async def search_content(self, query: str) -> List[PloneContent]
    async def create_content(self, parent_path: str, data: Dict) -> PloneContent
    async def update_content(self, path: str, data: Dict) -> PloneContent
    async def delete_content(self, path: str) -> bool
```

#### 2. **Content Transformation**
```python
# Transform legacy Plone data to modern API format
def transform_plone_content(plone_data: Dict[str, Any]) -> PloneContent:
    return PloneContent(
        uid=plone_data.get("UID"),
        title=plone_data.get("title"),
        portal_type=plone_data.get("@type"),
        url=plone_data.get("@id"),
        # ... additional transformations
    )
```

#### 3. **Authentication Bridge**
- **Token-based authentication**: JWT tokens from Plone
- **Session management**: Redis-backed session storage
- **Permission mapping**: Legacy roles to modern permissions

#### 4. **Error Handling**
```python
class PloneAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
```

### Data Synchronization Patterns

#### 1. **Real-time Bridge** (Current)
- **Direct API calls**: Real-time queries to Plone
- **Caching layer**: Redis for frequently accessed content
- **Connection pooling**: Efficient HTTP client management

#### 2. **Event-Driven Sync** (Future)
- **Change detection**: Monitor Plone content modifications
- **Event streaming**: Pub/sub for content updates
- **Eventual consistency**: Asynchronous data synchronization

## 🗄️ Data Architecture

### Database Design

#### Primary Database (PostgreSQL)
```sql
-- User management and modern features
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Content metadata and modern extensions
CREATE TABLE content_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plone_uid VARCHAR(255) UNIQUE NOT NULL,
    tags JSONB,
    analytics JSONB,
    modern_features JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User activity and engagement
CREATE TABLE user_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    content_uid VARCHAR(255),
    activity_type VARCHAR(50) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Cache Layer (Redis)
```yaml
Sessions:
  key_pattern: "session:{session_id}"
  ttl: 24 hours

Content Cache:
  key_pattern: "content:{uid}"
  ttl: 1 hour

Search Results:
  key_pattern: "search:{query_hash}"
  ttl: 15 minutes

User Permissions:
  key_pattern: "perms:{user_id}"
  ttl: 5 minutes
```

#### Legacy Integration (Plone)
- **Content Storage**: Plone ZODB for existing content
- **User Management**: Plone's acl_users for legacy authentication
- **Workflow**: Plone's workflow engine for content states
- **File Storage**: Plone's blob storage for media files

### Data Flow Patterns

#### 1. **Read Operations**
```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI
    participant R as Redis
    participant P as Plone

    C->>F: GET /content/document
    F->>R: Check cache
    alt Cache Hit
        R->>F: Return cached data
        F->>C: JSON response
    else Cache Miss
        F->>P: Request content
        P->>F: Plone data
        F->>R: Cache result
        F->>C: Transformed JSON
    end
```

#### 2. **Write Operations**
```mermaid
sequenceDiagram
    participant C as Client
    participant F as FastAPI
    participant P as Plone
    participant R as Redis
    participant D as Database

    C->>F: POST /content/
    F->>P: Create content
    P->>F: Created content
    F->>D: Store metadata
    F->>R: Cache content
    F->>C: Success response
```

## 🔒 Security Architecture

### Authentication & Authorization

#### 1. **Multi-Layer Authentication**
```python
# JWT token validation
async def verify_token(token: str) -> Optional[User]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return await get_user(username)
    except JWTError:
        return None

# Plone integration authentication
async def authenticate_with_plone(username: str, password: str) -> Optional[str]:
    async with PloneClient() as client:
        return await client.authenticate(username, password)
```

#### 2. **Permission System**
```python
# Role-based access control
class Permission(Enum):
    READ_CONTENT = "content:read"
    WRITE_CONTENT = "content:write"
    ADMIN_ACCESS = "admin:access"

# FastAPI dependency for permission checking
async def require_permission(permission: Permission):
    def permission_dependency(current_user: User = Depends(get_current_user)):
        if not current_user.has_permission(permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return permission_dependency
```

### Security Measures

#### 1. **Input Validation**
- **Pydantic models**: Strict data validation at API boundaries
- **SQL injection prevention**: SQLAlchemy ORM with parameterized queries
- **XSS protection**: Content sanitization for rich text
- **CSRF protection**: Token-based CSRF prevention

#### 2. **Infrastructure Security**
- **HTTPS enforcement**: TLS encryption for all communications
- **Secret management**: Environment variables and secure storage
- **Container security**: Minimal base images and non-root users
- **Network security**: Isolated container networks

#### 3. **Monitoring & Auditing**
```python
# Security event logging
async def log_security_event(
    event_type: str,
    user_id: Optional[str],
    details: Dict[str, Any]
):
    await security_logger.log({
        "timestamp": datetime.utcnow(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details,
        "source_ip": request.client.host
    })
```

## 🚀 Deployment Architecture

### Development Environment
```yaml
Services:
  - FastAPI: Local development server with hot reload
  - PostgreSQL: Docker container with persistent volume
  - Redis: Docker container for cache and sessions
  - Plone: Docker container with buildout development instance

Networking:
  - FastAPI: http://localhost:8000
  - PostgreSQL: localhost:5432
  - Redis: localhost:6379
  - Plone: http://localhost:8080
```

### Production Architecture (Future)
```mermaid
graph TB
    subgraph "Load Balancer"
        A[nginx/HAProxy]
    end

    subgraph "Application Tier"
        B[FastAPI Pod 1]
        C[FastAPI Pod 2]
        D[FastAPI Pod N]
    end

    subgraph "Worker Tier"
        E[Celery Worker 1]
        F[Celery Worker 2]
    end

    subgraph "Data Tier"
        G[PostgreSQL Primary]
        H[PostgreSQL Replica]
        I[Redis Cluster]
        J[Plone Cluster]
    end

    subgraph "Storage"
        K[Persistent Volumes]
        L[Object Storage]
    end

    A --> B
    A --> C
    A --> D

    B --> G
    B --> I
    B --> J

    E --> I
    E --> G

    G --> K
    J --> K
    J --> L
```

## ✅ Quality Assurance

### Testing Strategy

#### 1. **Test Pyramid**
```
     ┌─────────────┐
     │   E2E Tests │  ←  Selenium, Playwright
     ├─────────────┤
     │Integration  │  ←  API testing, Database tests
     │   Tests     │
     ├─────────────┤
     │             │
     │ Unit Tests  │  ←  pytest, mocking
     │             │
     └─────────────┘
```

#### 2. **Test Categories**
- **Unit Tests**: Individual function/method testing
- **Integration Tests**: Service interaction testing
- **API Tests**: HTTP endpoint testing
- **Contract Tests**: API contract validation
- **Performance Tests**: Load and stress testing
- **Security Tests**: Vulnerability and penetration testing

#### 3. **Quality Gates**
```yaml
Core Gates (Must Pass):
  - Code formatting: Black, isort
  - Type checking: MyPy
  - Unit tests: 60%+ coverage
  - Integration tests: All passing
  - Build validation: Package builds successfully

Optional Gates (Warnings):
  - Security scan: Safety, Bandit
  - Performance tests: Benchmark compliance
  - Documentation: Coverage and accuracy
```

### Continuous Integration
```yaml
Pipeline Stages:
  1. Code Quality: Formatting, linting, type checking
  2. Testing: Unit, integration, security tests
  3. Build: Docker image creation and validation
  4. Deploy: Staging environment deployment
  5. Verify: Post-deployment testing
  6. Release: Production deployment (manual gate)
```

## ⚡ Performance Considerations

### Caching Strategy

#### 1. **Multi-Level Caching**
```python
# Application-level caching
@lru_cache(maxsize=1000)
def get_user_permissions(user_id: str) -> Set[str]:
    return fetch_user_permissions(user_id)

# Redis caching for API responses
async def get_content_with_cache(uid: str) -> PloneContent:
    cached = await redis.get(f"content:{uid}")
    if cached:
        return PloneContent.parse_raw(cached)

    content = await plone_client.get_content(uid)
    await redis.setex(f"content:{uid}", 3600, content.json())
    return content
```

#### 2. **Database Optimization**
```sql
-- Indexes for common query patterns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_content_metadata_plone_uid ON content_metadata(plone_uid);
CREATE INDEX idx_user_activity_user_id_created ON user_activity(user_id, created_at);

-- Partial indexes for active data
CREATE INDEX idx_users_active ON users(id) WHERE is_active = true;
```

#### 3. **Connection Pooling**
```python
# Database connection pooling
DATABASE_URL = "postgresql://user:pass@host:5432/db?pool_size=20&max_overflow=0"

# HTTP client connection pooling
async def create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        timeout=httpx.Timeout(30.0)
    )
```

### Async Architecture Benefits
- **Non-blocking I/O**: Concurrent request handling
- **Resource efficiency**: Better memory and CPU utilization
- **Scalability**: Handle more concurrent users
- **Responsive UX**: Faster response times

## 📈 Scalability Design

### Horizontal Scaling Patterns

#### 1. **Stateless Application Design**
```python
# Session storage in Redis, not in application memory
async def get_user_session(session_id: str) -> Optional[Session]:
    session_data = await redis.get(f"session:{session_id}")
    return Session.parse_raw(session_data) if session_data else None

# No shared mutable state between requests
class ContentService:
    def __init__(self, db_session: AsyncSession, plone_client: PloneClient):
        self.db = db_session
        self.plone = plone_client
```

#### 2. **Database Scaling Strategies**
- **Read Replicas**: Scale read operations
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: Indexed and optimized queries
- **Caching**: Reduce database load

#### 3. **Microservices Preparation**
```python
# Modular service design enables future extraction
class ContentService:
    async def get_content(self, uid: str) -> PloneContent: ...
    async def create_content(self, data: CreateContentRequest) -> PloneContent: ...

class UserService:
    async def authenticate(self, credentials: LoginRequest) -> User: ...
    async def get_user_permissions(self, user_id: str) -> Set[str]: ...

class SearchService:
    async def search_content(self, query: SearchRequest) -> SearchResults: ...
```

## 🎯 Technical Decisions

### Decision Log

#### 1. **FastAPI over Django/Flask**
**Decision**: Use FastAPI as the primary web framework
**Rationale**:
- Modern async/await support
- Automatic OpenAPI documentation
- Excellent performance characteristics
- Type hints integration
- Growing ecosystem and community

**Trade-offs**:
- ✅ Better performance and async support
- ✅ Modern development experience
- ❌ Smaller ecosystem than Django
- ❌ Less enterprise tooling

#### 2. **Bridge Pattern over Migration**
**Decision**: Build API bridge to Plone instead of full migration
**Rationale**:
- Preserve existing content and workflows
- Minimize risk of data loss
- Enable gradual modernization
- Maintain business continuity

**Trade-offs**:
- ✅ Lower risk approach
- ✅ Faster time to market
- ❌ Increased system complexity
- ❌ Dependency on legacy system

#### 3. **PostgreSQL over MongoDB**
**Decision**: Use PostgreSQL as primary database
**Rationale**:
- ACID compliance for critical data
- Excellent JSON support for flexible schemas
- Mature ecosystem and tooling
- Strong performance characteristics

**Trade-offs**:
- ✅ Data integrity and consistency
- ✅ Rich query capabilities
- ❌ Less flexible than document databases
- ❌ More complex schema management

#### 4. **Docker-First Development**
**Decision**: Use Docker for development and deployment
**Rationale**:
- Environment consistency
- Easy multi-service orchestration
- Production parity
- Simplified onboarding

**Trade-offs**:
- ✅ Consistent environments
- ✅ Easy service management
- ❌ Learning curve for developers
- ❌ Additional overhead

#### 5. **Quality Gates in CI/CD**
**Decision**: Implement strict quality gates with core/optional separation
**Rationale**:
- Maintain code quality standards
- Prevent regressions
- Enable confident deployments
- Balance strictness with pragmatism

**Trade-offs**:
- ✅ Higher code quality
- ✅ Fewer production issues
- ❌ Slower development velocity
- ❌ Potential developer friction

### Future Architectural Decisions

#### 1. **Frontend Framework Selection**
**Options**: React, Vue.js, Angular, Svelte
**Factors**: Team expertise, ecosystem, performance, learning curve

#### 2. **Microservices Transition**
**Timeline**: After initial MVP and user validation
**Services**: User management, content, search, notifications

#### 3. **Cloud Provider Selection**
**Options**: AWS, GCP, Azure, hybrid
**Factors**: Cost, features, compliance, team expertise

#### 4. **Monitoring and Observability**
**Options**: ELK Stack, Prometheus/Grafana, DataDog, New Relic
**Factors**: Cost, features, integration complexity

## 🗺️ Feature-to-Architecture Mapping

| ✅ Feature | Architectural Touch-points | Status |
|-----------|----------------------------|--------|
| **Python 3.11 + Async Upgrade** | Entire FastAPI layer, tox matrix, Dockerfile base image | *Complete* |
| **OAuth2 / SSO Gateway (Auth0)** | `auth/` package, FastAPI middleware, Plone role mapping | *In Progress (Phase 3)* |
| **CSV Schedule Importer** | FastAPI upload endpoint → Bridge `create_content()` | *Planned (Phase 4)* |
| **Rich-Media Embeds (oEmbed)** | FastAPI micro-service, cache layer | *Planned (Phase 4)* |
| **Open Data API** | Additional REST routes leveraging existing bridge | *Planned* |
| **Role-Based Workflows** | Uses Plone’s workflow engine via Bridge | *Planned* |
| **Real-Time Alert Broadcasting** | FastAPI WebSocket hub + Redis / Slack integration | *Planned* |
| **React Admin SPA** | Consumes FastAPI REST+GraphQL, Auth0 tokens | *Conditional* |

This mapping shows **where** each deliverable hooks into the stack, helping managers assess scope, risk, and resource allocation at a glance.

## 📚 Documentation Standards

### Architecture Documentation Maintenance
- **Decision Records**: Document architectural decisions with rationale
- **Diagram Updates**: Keep architecture diagrams current with system evolution
- **Review Process**: Regular architecture review sessions
- **Stakeholder Communication**: Clear communication of architectural changes

### Code Documentation
- **API Documentation**: Comprehensive OpenAPI specifications
- **Code Comments**: Document complex business logic and integration points
- **README Files**: Clear setup and usage instructions
- **Change Logs**: Detailed change tracking and migration guides

---

**This architecture provides a solid foundation for modernizing legacy education technology while maintaining reliability, security, and scalability for future growth.**
