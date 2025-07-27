# Developer Onboarding Cheat-Sheet

Welcome to the EduHub modernization sprint!
This page distills the **must-know** facts for working productively in this repo.

## 1. Repository Layout (High-Level)

| Path | Purpose |
|------|---------|
| `src/` | Backend FastAPI code (Python packages). |
| `frontend/` | React frontend application (TypeScript/Vite). |
| `tests/` | Pytest suites (mirrors structure under `src/`). |
| `docs/` | Project documentation (plans, design notes, this guide). |
| `tasks/` | PRDs & task lists for each phase. |
| `scripts/` | Utility scripts for testing and population. |
| `docker-compose.yml` | Multi-service dev stack (API, Plone, DB, Redis). |
| `.github/workflows/` | CI pipelines (lint, test, build, deploy). |

## 2. Python Versions & Virtual Envs

* Backend: **Python 3.11** (required)
* Frontend: **Node.js 18+** (for React/Vite)
* Create backend venv:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

* Install frontend dependencies:

```bash
cd frontend
npm install
```

* Use **`tox`** to test against both versions:

```bash
tox                # runs all envs
tox -e py311       # single env
```

## 3. Auth0 Setup (Required)

**CRITICAL**: Authentication is already configured and working.

### Test Accounts:
- **Admin**: admin@example.com
- **Student**: student@example.com  
- **Developer**: dev@example.com

### Auth0 Configuration (already set up):
```bash
AUTH0_DOMAIN=dev-1fx6yhxxi543ipno.us.auth0.com
AUTH0_CLIENT_ID=s05QngyZXEI3XNdirmJu0CscW1hNgaRD
AUTH0_ALGORITHMS=["RS256"]
```

### Login Flow:
1. Visit `http://localhost:8001` (frontend)
2. Click login and use test credentials
3. You'll be routed to appropriate dashboard based on role

### Detailed Setup:
See `docs/getting-started/authentication-setup.md` for complete Auth0 configuration instructions.

## 4. Docker & Compose

Local full-stack:

```bash
# Start backend services
docker-compose up -d   # Postgres, Redis, Plone

# Start FastAPI (separate terminal)
uvicorn src.eduhub.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (separate terminal)  
cd frontend && npm run dev
```

*The first build can take a while—grab a coffee ☕️.*

Common commands:

| Action | Command |
|--------|---------|
| rebuild images | `docker compose build` |
| view logs | `docker compose logs -f [service]` |
| stop stack | `docker compose down` |

## 5. Running Tests

```bash
pytest -q                # fast feedback
pytest -q tests/hello.py # single file

# Integration testing (Auth0 + Plone)
python scripts/quick_integration_test.py
```

* Async tests use **pytest-asyncio**; mark with `@pytest.mark.asyncio`.

Coverage & benchmarks run automatically in CI.

## 6. Code Quality Gates

Tool | Invocation | CI Gate
-----|------------|--------
Black | `black .` | must pass
Isort | `isort .` | must pass
Mypy | `mypy src/` | warnings fail CI
Flake8 (via Ruff soon) | `flake8` | advisory
Pre-commit | `pre-commit run -a` | auto-fix hooks

Tip: install the git hook once:

```bash
pre-commit install
```

## 7. Commit & Branch Strategy

* **Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:` …).
* Feature branches from `main`, PR via GitHub.

Example:

```
feat(api): add /hello endpoint

Adds async FastAPI route /hello returning JSON {"msg":"Hello World"}.
Updates tests and OpenAPI docs.
```

## 8. Current Project Status

**Completed Phases**:
- ✅ **Phase 2**: OAuth2 Authentication with Auth0
- ✅ **Phase 3**: Role-Based Access Control (admin/student dashboards)
- ✅ **Phase 4**: CSV Schedule Importer 
- ✅ **Phase 5**: Rich Media Embeds (oEmbed)
- ✅ **Phase 6**: Open Data API endpoints
- ✅ **Phase 7**: Role-Based Workflow Templates
- ✅ **Phase 8**: Real-Time Alert Broadcasting (WebSockets)

**Current Focus**: Plone CMS integration for all features

## 9. Environment Variables

1. Duplicate `.env.example` → `.env`.
2. Fill in secrets (DB passwords, OAuth keys).
   *Never commit real secrets.*
3. Docker Compose automatically loads `.env`.

**Required Auth0 Variables:**
```bash
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_CLIENT_ID=your_client_id_here
AUTH0_ALGORITHMS=["RS256"]
```

## 10. Useful Make Targets (coming soon)

```make
make dev     # build & start compose stack
make fmt     # black + isort
make lint    # static checks
make clean   # remove __pycache__, build artifacts
```

## 11. Testing the Full System

### Quick Start:
1. Start backend: `docker-compose up -d && uvicorn src.eduhub.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Visit: `http://localhost:8001`
4. Login with test credentials (admin@example.com or student@example.com)

### Feature Testing:
- **Admin Dashboard**: Schedule import, workflow management, alerts
- **Student Dashboard**: Course viewing, media resources, workflow requests
- **API Testing**: Visit `http://localhost:8000/docs` for Swagger UI
- **WebSocket Alerts**: Real-time notifications between dashboards

### Plone Integration:
- Plone runs on `http://localhost:8080/Plone` (when started)
- Courses and announcements are fetched from Plone
- Fallback to mock data when Plone is unavailable

---

Happy hacking!
Questions? Open an issue or check the authentication setup guide for Auth0 troubleshooting.
