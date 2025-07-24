# GUI Development Strategy – React Admin SPA

This document explains **when** and **how** we will build the graphical user interface (GUI) for the EduHub project—specifically the React-based Admin Single-Page Application (SPA) described in Option A, Section 3 of the 5-day plan.

---

## 1. Position in the Overall Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project bootstrap & initial setup (backend skeleton, CI, "Hello World") | ✅ Done |
| 2 | Python 3.11 + Async upgrade harness | ⏳ In-progress |
| 3 | OAuth2 / SSO gateway (JWT issuance) | ⏳ Queued |
| 4 | Headless JSON API (REST + GraphQL) | ⏳ Queued |
| **5** | **React Admin SPA (GUI)** | 🚧 _This document_ |
| 6 | Dockerised CI/CD pipeline | ⏳ Queued |
| 7 | Real-time alert broadcasting | ⏳ Queued |
| 8 | QA hardening, docs, final demo | ⏳ Queued |

The SPA work **cannot start in earnest until Phases 3 & 4 are at least API-stable**, because the GUI consumes those endpoints for authentication and content management.
Given our **Thursday → Sunday 20:00 submission window**, the tasks below are mapped to individual days rather than weeks.

---

## 2. High-Level Timeline

| Day | Target Date | Milestone | Key Details |
|-----|-------------|-----------|-------------|
| **Day 0 – Thu (today)** | Today, 23:59 | Backend MVP ready | OAuth flow smoke-tested; CRUD REST endpoints for Post & Schedule stable. |
| **Day 1 – Fri** | Tomorrow, 23:59 | Front-end scaffold & component prototype | Vite + React-TS project created; ESLint + Prettier; Storybook running; core layout & auth context prototyped. |
| **Day 2 – Sat** | Saturday, 23:59 | CRUD views & live preview | Implement Post list/detail, Schedule editor (drag-and-drop); live preview via GraphQL subscription; Lighthouse perf ≥ 85. |
| **Day 3 – Sun** | Sunday, 20:00 (submission) | Polish & QA freeze | Role-based UI hiding, Cypress happy-path flows green in CI, accessibility pass (WCAG AA), bundle < 150 kB; docs updated, tag release. |

> All end-of-day targets assume local time and hard stop on **Sunday 20:00** for submission.

---

## 3. Prerequisites & Dependencies

1. **Auth** – `/auth/*` endpoints must issue short-lived JWT and refresh tokens accepted by the backend.
2. **API** – REST + GraphQL endpoints for `Post`, `Schedule`, `Alert`.
3. **CORS & CSRF** – Backend configured for SPA domain.
4. **Design System** – Brand guidelines or Tailwind config decided.
5. **CI/CD** – Front-end build/publish flow (Phase 6) ready for staging.

---

## 4. Development Approach

1. **Technology Stack**
   * React 18 + TypeScript
   * Vite build tool
   * React Router v6
   * Tailwind CSS (with DaisyUI components)
   * React Query + Axios (or generated API client) for data
   * Storybook for isolated UI work
   * Cypress for e2e tests

2. **Incremental, Feature-Flagged Releases**
   * Main branch always deployable; SPA behind `/@@iframe-spa`.
   * Use feature flags (e.g. LaunchDarkly stub) to hide incomplete sections.

3. **Component-Driven Design**
   * Atomic design hierarchy (Atoms → Molecules → Organisms → Pages).
   * Each component lives with its `.test.tsx` and `.stories.tsx`.

4. **State Management**
   * Context API for auth/session.
   * React Query caches server state; keep Redux out unless complexity demands.

5. **Performance & Accessibility Gates**
   * Lighthouse score ≥ 90 (perf, a11y).
   * Bundle < 150 kB initial JS (gzip).

---

## 5. Collaboration & Review Workflow

1. **Branch Naming**
   `gui/<feature>` (e.g., `gui/login-page`, `gui/post-crud`)

2. **Pull Request Checklist**
   - Unit tests passing (`npm test`)
   - Storybook snapshot updated (`npm run storybook:build`)
   - Cypress spec(s) added/updated
   - Design review screenshot attached
   - Conventional Commit message (`feat(gui): add login page`)

3. **Design Sign-Off**
   UX lead reviews Figma link or GIF in PR; comments resolved before merge.

---

## 6. CI/CD Integration

* **CI**: Front-end jobs will run in the existing GitHub Actions workflow:
  1. Install deps → lint → unit tests
  2. Build Storybook static site
  3. Run Cypress (headless)
  4. Upload build artifact

* **CD**: Phase 6 adds Docker multi-stage build:
  * Stage 1 – `npm build` → static assets
  * Stage 2 – Nginx Alpine serving `/admin/*` routes

---

## 7. Exit Criteria for Phase 5

- [ ] Login & logout flows work against OAuth gateway
- [ ] CRUD for Posts & Schedules fully functional
- [ ] Live preview updates within <500 ms of save
- [ ] Lighthouse perf & a11y scores ≥ 90
- [ ] E2E suite stable in CI
- [ ] Documentation added to `/docs/gui_development_strategy.md` (this file) and `README`

Once all boxes are ticked, we proceed to Phase 6 (CI/CD hardening).

---

_Questions? Ping the `#eduhub-frontend` Slack channel or open a GitHub discussion._
