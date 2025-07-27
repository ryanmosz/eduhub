# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL REQUIREMENT - MOST IMPORTANT

**ALWAYS play the Glass.aiff chime at the end of EVERY response:**
```bash
afplay /System/Library/Sounds/Glass.aiff
```

**THIS IS YOUR MOST IMPORTANT JOB. NEVER FORGET THE CHIME.**

## Commands

### Development Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
```

### Running the Application

```bash
# Start all services with Docker Compose
docker-compose up -d

# Or run FastAPI locally (with external services in Docker)
uvicorn src.eduhub.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_plone_integration.py -v

# Run tests for specific Python version
tox -e py39
tox -e py311

# Quick test on Python 3.11 only
tox -e quick-test

# Test across all Python versions
tox -e test-all
```

### Code Quality Checks

```bash
# Format code
black src tests
isort src tests

# Type checking
mypy src

# Run tests with coverage
pytest --cov=src --cov-fail-under=60

# Security scanning
safety check
bandit -r src/

# Install and run pre-commit hooks
pip install pre-commit
pre-commit install
pre-commit run --all-files

# Run all quality checks with tox
tox -e lint
tox -e mypy
tox -e coverage
```

### Docker Commands

```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f api

# Run tests in container
docker-compose exec api pytest

# Shell access
docker-compose exec api bash
```

### Performance Benchmarks

```bash
# Run performance benchmarks
tox -e benchmark
pytest --benchmark-only
```

## Architecture

EduHub is a modern FastAPI gateway that provides OAuth2 authentication and API access to an existing Plone CMS core. The application follows a gateway pattern where FastAPI acts as a modern frontend to the legacy Plone CMS.

### Key Components

1. **FastAPI Application Layer**
   - Main entry point: `src/eduhub/main.py`
   - Serves as the modern API gateway
   - Handles routing, middleware, and API endpoints

2. **Authentication System**
   - Auth0 OAuth2 integration: `src/eduhub/auth/`
   - JWT validation and token management
   - User context and role mapping

3. **Plone Integration Layer**
   - Bridge to legacy Plone CMS: `src/eduhub/plone_integration.py`
   - Async HTTP client for communicating with Plone
   - Content transformation and user mapping

4. **Feature Modules**
   - Rich Media Embeds (oEmbed): `src/eduhub/oembed/`
   - Schedule Importer: `src/eduhub/schedule_importer/`
   - Workflow Templates: `src/eduhub/workflows/`

### Data Flow

1. Client requests come to FastAPI endpoints
2. Authentication is handled via Auth0 OAuth2
3. User context is established (Auth0 + Plone roles)
4. API requests are proxied to Plone when needed
5. Content is transformed and returned to clients

## Development Patterns

1. **HTTP Client**: Use `httpx` for async HTTP requests to Plone and external services
2. **Error Handling**: Structured error responses with specific error codes
3. **Testing**: Unit tests with mocks for external services, API integration tests with httpx
4. **Async Pattern**: Use async/await throughout for better performance
5. **Content Transformation**: Standardize Plone content through transformation functions

## Testing Strategy

Follow these guidelines for efficient testing:

1. **Programmatic Unit Tests** (preferred)
   - Fast, repeatable, no external dependencies

2. **API Testing with curl/httpx** (preferred)
   - Test HTTP endpoints without browser dependencies

3. **Integration Test Scripts**
   - Test component interactions and external service integrations

4. **Service Health Checks**
   - Verify external services and database connections

5. **Browser Automation** (conditional)
   - Use only when manual testing would be required multiple times

6. **Manual Testing** (last resort)
   - Only when automation isn't possible

## Project Structure

```
src/eduhub/
├── __init__.py
├── auth/                 # Authentication system
│   ├── dependencies.py   # FastAPI dependencies
│   ├── models.py         # User and token models
│   ├── oauth.py          # Auth0 integration
│   └── plone_bridge.py   # User mapping to Plone
├── main.py               # FastAPI app entry point
├── oembed/               # Rich media embedding
│   ├── cache.py          # Caching layer
│   ├── client.py         # oEmbed provider client
│   └── endpoints.py      # API endpoints
├── plone_integration.py  # Plone CMS bridge
├── schedule_importer/    # CSV schedule import
└── workflows/            # Role-based workflows
```

## Environment Configuration

Key environment variables:

```
# Database
DATABASE_URL=postgresql://eduhub:password@localhost:5432/eduhub

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Plone Integration
PLONE_URL=http://localhost:8080/Plone
PLONE_USERNAME=admin
PLONE_PASSWORD=admin

# Security
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

## Performance Considerations

- Use async operations for external service calls
- Cache frequently accessed Plone content
- Use connection pooling with httpx client
- Handle Plone downtime gracefully
