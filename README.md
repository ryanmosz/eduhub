# EduHub - Modern Education Portal

[![CI Pipeline](https://github.com/USERNAME/REPO_NAME/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/REPO_NAME/actions/workflows/ci.yml)
[![Quality Gates](https://img.shields.io/badge/quality%20gates-passing-brightgreen)](https://github.com/USERNAME/REPO_NAME/actions)
[![Coverage](https://img.shields.io/badge/coverage-63%25-yellow)](https://github.com/USERNAME/REPO_NAME/actions)
[![Python](https://img.shields.io/badge/python-3.11%20optimized-blue)](https://github.com/USERNAME/REPO_NAME)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com/)
[![Plone](https://img.shields.io/badge/Plone-6.1-blue)](https://plone.org/)
[![Docker](https://img.shields.io/badge/docker-enabled-blue)](https://hub.docker.com/r/USERNAME/eduhub)
[![Performance](https://img.shields.io/badge/performance-27%25%20faster-brightgreen)](docs/performance-benchmark-report.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Modernizing legacy Plone CMS into a cutting-edge education platform with FastAPI, React, and cloud-native architecture**

## 🎯 Project Overview

EduHub transforms a legacy Plone CMS and Django application into a modern, scalable education portal. The project bridges legacy content management with contemporary web technologies, providing:

- **🔗 Legacy Integration**: Seamless FastAPI bridge to existing Plone CMS content
- **⚡ Python 3.11 Optimized**: 20-27% performance improvements with sub-2ms response times
- **🚀 Modern APIs**: RESTful endpoints with async Python capabilities
- **🐳 Containerized**: Docker-first development and deployment
- **🔒 Secure**: Comprehensive security scanning and best practices
- **🧪 Well-Tested**: 60%+ test coverage with integration tests
- **🤖 CI/CD Ready**: Full GitHub Actions pipeline with quality gates

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Modern Layer"
        A[React Frontend] --> B[FastAPI Backend]
        B --> C[PostgreSQL]
        B --> D[Redis]
        B --> E[Celery Workers]
    end

    subgraph "Legacy Bridge"
        B --> F[Plone Integration Layer]
        F --> G[Plone CMS 6.1]
    end

    subgraph "Infrastructure"
        H[Docker Compose] --> A
        H --> B
        H --> C
        H --> D
        H --> E
        H --> G
    end
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (optimized for performance gains)
- Docker and Docker Compose
- Git

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/USERNAME/REPO_NAME.git
cd REPO_NAME

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install -e ".[dev]"
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# (Database URLs, API keys, etc.)
```

### 3. Start Development Environment

```bash
# Start all services with Docker Compose
docker-compose up -d

# Or run FastAPI locally (with external services in Docker)
uvicorn src.eduhub.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

```bash
# Run tests
pytest

# Check code quality
black --check src tests
isort --check-only src tests
mypy src

# Access the application
curl http://localhost:8000/health
```

## 📋 Development Workflow

### Code Quality Standards

Our CI/CD pipeline enforces strict quality standards:

- **Formatting**: Black (88 character line length)
- **Import Sorting**: isort with Black profile
- **Type Checking**: MyPy static analysis
- **Testing**: 60%+ coverage requirement
- **Security**: Dependency scanning with Safety and Bandit

### Running Quality Checks Locally

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
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## ⚡ Performance

### Python 3.11 Optimization Results

EduHub leverages Python 3.11's performance improvements to deliver exceptional API response times:

| Endpoint | Python 3.9 | Python 3.11 | Improvement |
|----------|-------------|-------------|-------------|
| Health Check | 917μs | 732μs | **20.2% faster** |
| Content List | 1.04ms | 822μs | **21.2% faster** |
| Plone Info | 935μs | 684μs | **26.9% faster** |
| Main Health | 2.7ms | 1.9ms | **27.5% faster** |

**Key Achievements:**

- ✅ **20-27% performance improvements** across core endpoints
- ✅ **Sub-2ms response times** (25-76x under 50ms industry standard)
- ✅ **>1000 requests/second** throughput capability
- ✅ **Zero performance regressions** with 100% test compatibility

📊 **[View Complete Benchmark Report](docs/performance-benchmark-report.md)**

## 🐳 Docker Development

### Multi-Service Stack

```yaml
# docker-compose.yml includes:
- FastAPI Application (Port 8000)
- PostgreSQL Database (Port 5432)
- Redis Cache (Port 6379)
- Plone CMS (Port 8080)
- Celery Worker
- Celery Beat Scheduler
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

## 🧪 Testing

### Test Structure

```
tests/
├── test_hello.py              # Basic FastAPI tests
├── test_plone_integration.py  # Plone bridge tests
└── conftest.py                # Test configuration
```

### Test Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_plone_integration.py -v

# Run tests for specific Python version
tox -e py39
```

### Test Coverage

Current coverage: **63%** (target: 80%)

## 🔗 Plone Integration

### Legacy CMS Bridge

The Plone integration layer provides:

- **REST API Access**: Modern endpoints for legacy content
- **Authentication**: Token-based auth with Plone backend
- **Content CRUD**: Create, read, update, delete operations
- **Search**: Full-text search across Plone content
- **Async Operations**: Non-blocking HTTP client

### Integration Endpoints

```bash
# Get Plone site information
GET /plone/info

# List content
GET /content/?query=education&content_type=Document

# Get specific content
GET /content/path/to/document

# Create content
POST /content/
```

## 🤖 CI/CD Pipeline

### GitHub Actions Workflow

Our CI pipeline includes 7 jobs:

1. **🎨 Lint**: Code quality checks (Black, isort, MyPy)
2. **🧪 Test**: Matrix testing (Python 3.9, 3.11) with performance benchmarks
3. **🔗 Integration**: Plone-FastAPI bridge validation
4. **🔒 Security**: Vulnerability scanning (Safety, Bandit)
5. **🐳 Docker**: Container build, test, and registry push
6. **📦 Build**: Python package validation
7. **🎯 Quality Gates**: Evaluation and reporting

### Quality Gates

- **Core Gates** (must pass): Lint, Test, Integration, Build
- **Optional Gates** (warnings): Security, Docker
- **Coverage Threshold**: 60% minimum
- **Python Versions**: 3.9, 3.11 compatibility (optimized for 3.11 performance)

### Status Badges

The badges at the top of this README reflect:

- [![CI Pipeline](https://img.shields.io/badge/CI-passing-brightgreen)](https://github.com/USERNAME/REPO_NAME/actions) Overall pipeline status
- [![Quality Gates](https://img.shields.io/badge/quality%20gates-passing-brightgreen)](https://github.com/USERNAME/REPO_NAME/actions) Quality enforcement
- [![Coverage](https://img.shields.io/badge/coverage-63%25-yellow)](https://github.com/USERNAME/REPO_NAME/actions) Test coverage percentage

## 📁 Project Structure

```
G2W6-Legacy/
├── .github/
│   ├── workflows/ci.yml       # CI/CD pipeline
│   ├── SECRETS.md            # Secrets documentation
│   └── QUALITY_GATES.md      # Quality standards
├── src/
│   ├── hello/               # Demo FastAPI module
│   └── eduhub/              # Main application
│       ├── main.py          # FastAPI app entry point
│       └── plone_integration.py  # Legacy CMS bridge
├── tests/                   # Test suite
├── upstream/                # Cloned Plone repositories
├── docker-compose.yml       # Multi-service development
├── Dockerfile              # Container build
├── pyproject.toml          # Modern Python packaging
└── requirements*.txt       # Dependency management
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
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

### Development vs Production

- **Development**: Uses docker-compose with hot reload
- **Production**: Multi-stage Docker build with gunicorn
- **Testing**: Isolated test database and mocked services

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI Schema**: <http://localhost:8000/openapi.json>

### Key Endpoints

```bash
# Application
GET  /                    # API information
GET  /health             # Health check

# Legacy Integration
GET  /plone/info         # Plone site information
GET  /content/           # List/search content
GET  /content/{path}     # Get specific content
POST /content/           # Create content
PUT  /content/{path}     # Update content
DELETE /content/{path}   # Delete content

# Demo Endpoints
GET  /hello/             # Hello world demo
GET  /hello/async-demo   # Async functionality demo
```

## 🤝 Contributing

### Development Setup

1. Fork and clone the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Ensure all quality checks pass: `pytest && black src tests && isort src tests`
5. Commit with conventional format: `feat: add new feature`
6. Push and create a pull request

### Code Standards

- Follow PEP 8 with Black formatting
- Add type hints for all functions
- Write tests for new functionality
- Update documentation as needed
- Ensure CI pipeline passes

### Pull Request Process

1. Ensure all tests pass locally
2. Update README if adding features
3. Add entry to CHANGELOG.md
4. Request review from maintainers
5. Merge after approval and CI success

## 📊 Roadmap

### Phase 1: Foundation ✅

- [x] Development environment setup
- [x] FastAPI application structure
- [x] Plone integration layer
- [x] CI/CD pipeline with quality gates
- [x] Docker containerization

### Phase 2: Core Features 🚧

- [ ] User authentication and authorization
- [ ] Content management interfaces
- [ ] Search and filtering capabilities
- [ ] API rate limiting and caching
- [ ] Performance optimization

### Phase 3: Frontend 📋

- [ ] React frontend application
- [ ] Component library and design system
- [ ] Admin dashboard
- [ ] Mobile responsiveness
- [ ] Progressive Web App features

### Phase 4: Production 📋

- [ ] Kubernetes deployment manifests
- [ ] Monitoring and observability
- [ ] Backup and disaster recovery
- [ ] Performance testing
- [ ] Security audit

## 📞 Support

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/USERNAME/REPO_NAME/issues)
- **Discussions**: [GitHub Discussions](https://github.com/USERNAME/REPO_NAME/discussions)
- **Documentation**: [Project Wiki](https://github.com/USERNAME/REPO_NAME/wiki)

### Troubleshooting

Common issues and solutions:

**Docker daemon not running**: Start Docker Desktop or Docker service
**Import errors**: Ensure virtual environment is activated
**Test failures**: Check test database configuration
**CI failures**: Review quality gates documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Plone Community**: For the robust CMS foundation
- **FastAPI**: For the modern Python web framework
- **Docker**: For containerization technology
- **GitHub Actions**: For CI/CD infrastructure

---

**Built with ❤️ for modern education technology**
