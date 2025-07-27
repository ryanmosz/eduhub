# EduHub

A modern educational platform demonstrating enterprise architecture patterns by transforming legacy Plone CMS into a scalable web application with FastAPI, React, and real-time features.

## Why This Project?

Learning Group Administrators rely on decades-old content management systems. This project shows how to modernize legacy infrastructure without disrupting operations, using a gateway pattern to bridge old and new technologies while adding contemporary features like OAuth2, real-time alerts, and workflow automation.

## Key Features & User Stories

### 🔐 **OAuth2 Authentication**
*"As a student, I can log in once and access all university services"*
- Single sign-on via Auth0
- Role-based permissions (Student, Instructor, Admin)
- Seamless Plone CMS integration

### 📊 **CSV Schedule Import**
*"As an admin, I can bulk import course schedules without manual entry"*
- Drag-and-drop CSV upload
- Real-time validation feedback
- Automatic Plone content creation

### 🎥 **Rich Media Embedding**
*"As an instructor, I can embed YouTube videos directly in course content"*
- oEmbed protocol support
- Cached responses for performance
- Works with YouTube, Vimeo, X

### 📚 **Open Data API**
*"As a developer, I can access public university data without authentication"*
- RESTful endpoints for courses and events
- Rate-limited to prevent abuse
- JSON/CSV export formats

### 🔄 **Workflow Templates**
*"As a department head, I can standardize content approval processes"*
- Pre-built workflows for common tasks
- Visual state tracking
- Role-based task assignment

### 🚨 **Real-time Alerts**
*"As a student, I receive instant notifications about schedule changes"*
- WebSocket live updates
- Multi-channel delivery (web, email, Slack)
- Priority-based routing

## Quick Start

```bash
# Clone and setup
git clone https://github.com/ryanmosz/eduhub.git
cd eduhub
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Configure environment
cp .env.example .env

# Start services
docker-compose up -d

# Access at http://localhost:8000
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   React UI  │────▶│ FastAPI Gate │────▶│  Plone CMS  │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴───────┐
                    │              │
                ┌───▼───┐     ┌───▼───┐
                │ Redis │     │  PG   │
                └───────┘     └───────┘
```

## Testing

```bash
pytest                          # Run tests
pytest --cov=src --cov-report=html  # Coverage report
black src tests                 # Format code
mypy src                       # Type checking
```

## API Documentation

- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Performance

Python 3.11 optimizations deliver 20-27% faster response times:
- Health endpoint: 732μs (was 917μs)
- Content list: 822μs (was 1.04ms)
- Sub-2ms for all core operations

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Vercel (frontend) and Render (backend) instructions.

## License

MIT
