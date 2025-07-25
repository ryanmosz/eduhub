## Relevant Files

- `docs/plone_5day_plan.md` – Source roadmap and feature descriptions.
- `tasks/tasks-overall-project-plan-addendum.md` – Strategic implementation decisions, testing methodology, and GUI approach.
- `tasks/tasks-phase-3-oauth2-sso-gateway.md` – Detailed OAuth2/SSO implementation subtasks.
- `src/` – Core application code (FastAPI, integration layers, SPA embedding).
- `tests/` – Pytest suites to be expanded per phase.
- `.github/workflows/ci.yml` – CI pipeline to evolve with new stages (lint, test, build, deploy).
- `Dockerfile`, `docker-compose.yml` – Container build & multi-service dev stack.
- `tasks/` – Phase-specific task lists (this file + upcoming detailed lists).

### Notes

1. Each phase below will later receive its own `tasks/tasks-phase-X-*.md` document with expanded parent/sub-tasks.
2. Features correspond to refined *Option A* selection based on weekend MVP timeline and user value analysis.
3. "✅" indicates a phase already completed or nearly done; unchecked items are upcoming.
4. **Strategic Context**: See `tasks-overall-project-plan-addendum.md` for detailed implementation strategy, testing methodology, and GUI approach decisions.
5. **Feature Prioritization**: Phases 3-8 are core MVP features (6 required to pass). Phases 9-12 are conditional enhancements based on available time.

## Tasks — High-Level Phases

- [x] **1.0 Project Bootstrap & Initial Setup** (✅ Completed)
  - Dev environment, repo scaffolding, CI baseline, "Hello World" endpoints.

- [x] **2.0 Python 3.11 + Async Upgrade Harness**
  - Migrate codebase to Python 3.11, introduce async I/O, ensure backward compatibility.

- [ ] **3.0 OAuth2 / SSO Gateway**
  - Implement FastAPI auth façade with Auth0; issue JWT accepted by legacy layers.

- [ ] **4.0 CSV Schedule Importer**
  - Build file upload endpoint for bulk program schedule imports; transform CSV to Plone content.

- [ ] **5.0 Rich-Media Embeds (oEmbed)**
  - Add YouTube/Vimeo embedding capability via oEmbed protocol integration.

- [ ] **6.0 Open Data API Endpoints**
  - Expose CMS objects via FastAPI REST endpoints for public data access.

- [ ] **7.0 Role-Based Workflow Templates**
  - Implement pre-configured Plone workflow templates for educational program management.

- [ ] **8.0 Real-Time Alert Broadcasting (Browser & Slack)**
  - FastAPI WebSocket hub plus Slack integration for instant notifications.

### **Conditional Features (Time Permitting)**

- [ ] **9.0 React Admin SPA**
  - Build Vite + React-TS admin panel consuming the new APIs (replaces basic Swagger UI).

- [ ] **10.0 Headless JSON API (REST + GraphQL)**
  - Expand API with comprehensive GraphQL schema and advanced REST endpoints.

- [ ] **11.0 Dockerised CI/CD Pipeline**
  - Extend CI to build/push Docker images and deploy via Helm blue-green strategy.

- [ ] **12.0 Quality Assurance, Documentation & Final Demo**
  - Increase test coverage ≥ 85 %, polish docs, record demo GIF, validate rubric checklist, tag v1.0.0.
