# 5-Day Modernization Sprint Plan
### Plone CMS / Legacy Django → EduHub (Modern Education Portal)

> Status: **Day 3 of 7-day sprint** – two days already spent on codebase archaeology & dev-env setup.
> Goal: deliver **six rubric-scored features** that convert an ageing Python CMS into a sleek, API-first portal for city-government communications teams.

---
### Prerequisites

Before Day 1 begins, clone and bootstrap the upstream Plone repositories:

```bash
git clone https://github.com/plone/Products.CMFPlone.git
git clone https://github.com/plone/buildout.coredev.git
cd buildout.coredev
python3 -m venv .venv && source .venv/bin/activate
python bootstrap.py
bin/buildout
```

These steps provide a clean, Python 3-ready Plone skeleton that EduHub will extend.
---
## 1  Are Plone 4/5 & Django 1.x Sites Still in Use?

Absolutely. Thousands of municipal, NGO and intranet sites still rely on them because:
• long-tail of custom add-ons and workflows built over years
• editorial UI familiar to non-technical staff
• budget constraints blocking commercial CMS migration

But they show their age:
• Python 2 remnants, blocking modern libraries
• server-side templates only; no SPA interactivity
• no first-class REST/GraphQL API → mobile apps impossible
• brittle FTP/SCP deployments and hand-edited config

---

## 2  Target User Segment

**Education-Program & Summer-Camp Administrators** who publish schedules, curriculum updates and student announcements across web & mobile.

Pain points solved:
• Out-of-date editorial UI slows last-minute curriculum tweaks
• Difficult to push updates to parents’ mobile devices or hallway signage
• Manual deployments cause downtime during live camp sessions
• Lack of SSO forces staff and volunteers to juggle multiple accounts

---

## 3  The Six Features (graded items)

### Option A – Coding Camp Administrators (Web-First)

| 1 | **Python 3.11 + Async Upgrade Harness**
User Value – Future-proofs the codebase and shaves ~15 % off average page-render time in the browser dashboards campers use every day.
Complexity – Medium
Python-Centric Work – `2to3` pass + tox matrix; pytest ensures parity
Work Plan – Create `feat/python311` branch, run `pyupgrade`, adjust tox/GitHub Actions, swap `requests` → `httpx`, wrap blocking views with `@sync_to_async`, benchmark with `pytest-benchmark`, merge after perf gate passes.

| 2 | **OAuth2 / SSO Gateway**
User Value – One-click login with Google Workspace or Azure AD so instructors never reset passwords during busy camp mornings; centralised audit trail for camp admins.
Complexity – Medium
Python-Centric Work – FastAPI auth façade issuing JWT to Plone/Django
Work Plan – Spin up FastAPI service on `/auth/*`, configure Google & Azure providers, issue short-lived JWT + refresh token, patch Plone/Django middleware to accept JWT, add unit tests & README setup notes.

| 3 | **Headless JSON API (REST + GraphQL)**
User Value – Powers the React admin panel and future integrations (e.g. hallway display dashboards) from a single canonical data source—mobile apps can be added later with zero backend changes.
Complexity – High
Python-Centric Work – Django-Ninja + Strawberry GraphQL exposing CMS objects
Work Plan – Serializers for `Post`, `Schedule`, `Alert`; CRUD endpoints with pagination & caching; GraphQL Playground; Postman collection; pytest API tests; OpenAPI spec.

| 4 | **React Admin SPA**
User Value – Browser-based drag-and-drop editing with live preview lets non-technical staff publish last-minute room changes in seconds; interns learn quickly.
Complexity – High
Python-Centric Work – Vite + React-TS app consuming API; embedded in Plone via iframe
Work Plan – Scaffold Vite project, integrate OAuth flow, build schedule editor (react-beautiful-dnd), live preview component, CI build, embed via `/@@iframe-spa`, add Cypress e2e tests, write onboarding doc.

| 5 | **Dockerised CI/CD Pipeline**
User Value – Blue-green deployments keep the camp website online during peak registration; instant rollbacks reduce stress on the small IT crew.
Complexity – Medium/High
Python-Centric Work – Dockerfile, GitHub Actions, Helm chart
Work Plan – Multi-stage Dockerfile, docker-compose for local dev, GH Actions (build, test, push, helm-upgrade), Helm chart with blue/green switch & health probes, secrets via GitHub OIDC, rollback docs.

| 6 | **Real-Time Alert Broadcasting (Browser & Slack)**
User Value – Emergency or schedule change alerts pop up in every open browser tab and Slack channel within seconds, fulfilling duty-of-care requirements without building a separate mobile app.
Complexity – High
Python-Centric Work – FastAPI WebSocket hub + Slack webhook, optional email fallback
Work Plan – Build `/ws/alerts` hub with FastAPI + `uvicorn`, Slack sender, admin UI to compose alerts, Playwright tests for multi-client broadcast, load-test with Locust.

#### Backup / Swap-In Features (choose any if a core feature slips)

| 7 | **Onboarding Wizard**
User Value – Step-by-step setup helps first-time camp admins configure branding, term dates and roles in under five minutes.
Complexity – Medium/High
Work Plan – React wizard component backed by REST endpoints, progress saved in localStorage, server-side validation, Cypress tests.

| 8 | **CSV Schedule Importer**
User Value – Staff can bulk-upload room schedules from Excel, avoiding tedious manual entry during crunch time.
Complexity – Medium
Work Plan – Upload endpoint accepting CSV, pandas validation, async task to create Schedule objects, admin feedback UI, unit tests with sample CSV files.


### Option B – District-Level Education Administrators

| 1 | **School SIS Sync (PowerSchool / InfiniteCampus)**
User Value – Auto-imports rosters & grades; no more CSV juggling
Complexity – Medium
Python-Centric Work – Celery worker pulls SIS API, normalises to Plone types

| 2 | **Role-Based Workflow Templates**
User Value – Principals approve, teachers draft, district publishes seamlessly
Complexity – Low-Medium
Python-Centric Work – Pre-configured Dexterity types & workflow definitions

| 3 | **Timetable Builder SPA**
User Value – Drag-and-drop scheduling; exports to ICS / Google Calendar
Complexity – Medium
Python-Centric Work – React (Vite) front-end; FastAPI backend; ICS generator

| 4 | **Parent Notification Hub**
User Value – Email/SMS alerts for schedule or policy changes
Complexity – Medium
Python-Centric Work – Twilio integration, Celery tasks, WebSocket broadcast

| 5 | **Rich-Media Embeds (oEmbed)**
User Value – Paste a YouTube/Vimeo link, auto-embed with caption
Complexity – Low
Python-Centric Work – oEmbed micro-service & media proxy

| 6 | **Compliance Dashboard (FERPA / GDPR)**
User Value – Surfaces personal-data footprint; export & delete requests
Complexity – Medium
Python-Centric Work – Plone add-on that maps data models, generates reports


### Option C – Municipal Library Content Managers

| 1 | **ISBN Auto-Import & Catalog Sync**
User Value – Creates book pages from ISBN; nightly sync with ILS
Complexity – Medium
Python-Centric Work – OpenLibrary API client; MARC-to-Plone field mapper

| 2 | **Public Events Booking Calendar**
User Value – Patrons reserve rooms & programs online
Complexity – Medium
Python-Centric Work – FullCalendar React widget; FastAPI booking endpoints

| 3 | **Federated Search**
User Value – Single search across archives, images, external APIs
Complexity – Medium
Python-Centric Work – Elasticsearch index; GraphQL aggregator layer

| 4 | **Patron Progressive Web App (PWA)**
User Value – Offline reading lists, due-date push reminders
Complexity – Medium
Python-Centric Work – Workbox PWA scaffold; REST endpoints for sync

| 5 | **Self-Service Kiosk Mode**
User Value – Touch-friendly UI for in-library terminals
Complexity – Low-Medium
Python-Centric Work – Tailwind UI skin; session-timeout middleware

| 6 | **Open Data API Endpoints**
User Value – Developers build mash-ups with library datasets
Complexity – Low
Python-Centric Work – Django-Ninja API; API-key management & rate limiting

---

## 4  Day-by-Day Execution (Days 3-7)

| Day | Deliverables | AI Assist |
|-----|--------------|-----------|
| 3 | Python 3.11 branch compiles; tests green | ChatGPT fixing 2→3 edge cases |
| 4 | OAuth2 gateway + Swagger docs | GPT to scaffold FastAPI routes & unit tests |
| 5 | JSON API endpoints + React SPA skeleton | GPT to generate GraphQL schema & sample queries |
| 6 | Docker compose, GH Actions, k8s manifests | GPT to write CI YAML & Helm values |
| 7 | WebSocket alert module, Twilio worker, demo GIF | GPT to craft Celery task code & e2e Playwright tests |

---

## 5  Rubric Alignment

• **Legacy Understanding (20 pts)** – produce `architecture.md` diagramming Zope object db, add-on stack, new micro-services.
• **Six Features (50 pts)** – live demo: editor logs in via SSO, edits post in React SPA, content hits mobile PWA, alert broadcast works.
• **Technical Quality (20 pts)** – black/isort, pytest ≥ 85 %, async views < 50 ms median.
• **AI Utilisation (10 pts)** – commit `ai_prompts/`, link to ChatGPT diff discussions.

---

## 6  Proof-of-Completion Checklist

- [ ] `tox` matrix passes for py3.11 & 3.9
- [ ] OAuth login succeeds with test Azure tenant
- [ ] `/api/posts/` returns valid JSON & GraphQL playground works
- [ ] React SPA shows live preview, saves via API
- [ ] `kubectl rollout status civic-web` green in <30 s
- [ ] Emergency alert appears in two browser tabs & sends SMS in <5 s
- [ ] CI pipeline green; README demo GIF committed

Ship all ticks – earn full marks while keeping scope manageable.

<!-- Blank line preserved -->

### Implementation Deep-Dive: Python 3.11 + Async Upgrade Harness

The upgrade harness is a **repeatable workflow** that moves the legacy Plone/Django codebase from Python 3.9 → **3.11** and unlocks `async` views without breaking existing behaviour.

**1. Branch & Environment Setup**
1. `git switch -c feat/python311-upgrade`
2. Create new tox envs: `py39`, `py310`, `py311`.
3. Bump `python_requires` in *setup.cfg* to `>=3.9`.

**2. Automated Syntax Migration**
• Run `python -m lib2to3 path/to/project -w` for left-over Py2 idioms.
• Use `pyupgrade --py39-plus` across repo to enforce modern syntax (f-strings, `typing`).
• Commit with message: "chore: machine migration to py3.11-safe syntax".

**3. Dependency Audit**
• Add `caniusepython3[with_removals]==2024.*` to helpers; run to flag blockers.
• Pin or replace obsolete libs (e.g. `ujson` → `orjson`, `asynctest` → `pytest-asyncio`).

**4. Async-Ready Refactor Pass**
• Replace `requests` with `httpx` (async client).
• Identify I/O-bound Django / Plone views and wrap handlers with `@sync_to_async`.
• Add `async` tasks for long-running Plone transforms (e.g. image scaling) using Celery 5.

**5. Test Matrix & Parity Gate**
• Update `tox.ini`:

```ini
[tox]
envlist = py39, py311, lint, mypy
```

• In CI (GitHub Actions), run:

```yaml
strategy:
  matrix:
    python-version: [3.9, 3.11]
```

• All unit & integration tests **must** pass on both versions before merge.

**6. Performance & Profiling**
• Enable CPython 3.11’s `perf` counters, compare latency of key API endpoints.
• Target: ≥ 15 % speed-up over 3.9 baseline, median view time < 50 ms.

**7. Deliverables**
• PR labelled `feat/python311-upgrade` merged to *main*.
• Wiki page: "Python 3.11 Migration Playbook".
• CI badge shows green for py3.11.
• Changelog entry under "Unreleased → Added".

This harness becomes the **template** for future point-version upgrades (3.12, 3.13) and provides a safe runway for adopting fully-async Plone add-ons.
