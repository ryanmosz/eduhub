## Relevant Files

- `docs/plone_django_web_platform_5day_plan.md` – Source roadmap and feature descriptions.
- `src/` – Core application code (FastAPI, integration layers, SPA embedding).
- `tests/` – Pytest suites to be expanded per phase.
- `.github/workflows/ci.yml` – CI pipeline to evolve with new stages (lint, test, build, deploy).
- `Dockerfile`, `docker-compose.yml` – Container build & multi-service dev stack.
- `tasks/` – Phase-specific task lists (this file + upcoming detailed lists).

### Notes

1. Each phase below will later receive its own `tasks/tasks-phase-X-*.md` document with expanded parent/sub-tasks.
2. Features correspond to *Option A* in Section 3 of the 5-day sprint plan (web-app focus, no mobile-specific work).
3. "✅" indicates a phase already completed or nearly done; unchecked items are upcoming.

## Tasks — High-Level Phases

- [x] **1.0 Project Bootstrap & Initial Setup** (✅ Completed)
  - Dev environment, repo scaffolding, CI baseline, "Hello World" endpoints.

- [x] **2.0 Python 3.11 + Async Upgrade Harness**
  - Migrate codebase to Python 3.11, introduce async I/O, ensure backward compatibility.

- [ ] **3.0 OAuth2 / SSO Gateway**
  - Implement FastAPI auth façade for Google Workspace & Azure AD; issue JWT accepted by legacy layers.

- [ ] **4.0 Headless JSON API (REST + GraphQL)**
  - Expose CMS objects via Django-Ninja REST and Strawberry GraphQL endpoints.

- [ ] **5.0 React Admin SPA**
  - Build Vite + React-TS admin panel consuming the new APIs; embed via Plone iframe route.

- [ ] **6.0 Dockerised CI/CD Pipeline**
  - Extend CI to build/push Docker images and deploy via Helm blue-green strategy.

- [ ] **7.0 Real-Time Alert Broadcasting (Browser & Slack)**
  - FastAPI WebSocket hub plus Slack integration for instant notifications.

- [ ] **8.0 Quality Assurance, Documentation & Final Demo**
  - Increase test coverage ≥ 85 %, polish docs, record demo GIF, validate rubric checklist, tag v1.0.0.
