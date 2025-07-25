# Deployment Considerations & Strategy

_Last updated: Thu (aligns with Sunday 20:00 submission deadline)_

## 1. System Components

| Layer | Technology | Notes |
|-------|------------|-------|
| **Frontend** | React 18 + Vite build (static assets) | Admin SPA served over HTTPS |
| **API Gateway** | FastAPI (Python 3.11, async) | Bridges React ↔ Plone |
| **Legacy CMS** | Plone (Zope, Python 3) | Runs as a long-lived WSGI process |
| **Datastores** | ZODB (Plone), PostgreSQL (content search, new features), Redis (caching) | Postgres also required for Supabase |
| **Worker/Tasks** | Celery (async tasks, WebSocket alerts) | Optional in MVP |

These pieces have **different hosting characteristics**—some are static, some are serverless-friendly, others must stay in a long-running container.

---

## 2. Deployment Goals

1. **Fast turnaround** – simple flow that can be set up before **Sunday 20:00**.
2. **Low ops overhead** – managed services / PaaS preferred over hand-rolled Kubernetes.
3. **Scalable enough** – handle municipal-scale traffic, but not "hyperscale".
4. **Blue-green or instant rollback** – bad deploys must be reversible in seconds.
5. **Cost-aware** – free tier or low-cost entry level for demo.

---

## 3. Hosting Options

### 3.1 Frontend (React SPA)

| Option | Pros | Cons |
|--------|------|------|
| **Vercel** | GitHub integration, instant preview URLs, free hobby tier, global edge CDN | Sever-side rendering not required, but Vercel Functions _can_ proxy API calls if needed |
| Netlify | Similar to Vercel, but team already uses Vercel | — |
| S3 + CloudFront | Durable, cheap | Extra setup, no instant preview |

➡ **Recommendation:** **Vercel** – fastest path, fits existing workflow.

### 3.2 FastAPI + Plone Stack

| Option | Pros | Cons |
|--------|------|------|
| **Render (Docker deploy)** | Build from `Dockerfile` on push, free preview envs, managed Postgres add-on, simple secrets UI | Paid instance for >550 MB RAM; still container-based |
| Fly.io | Global deployment, Postgres as a service, Docker or `fly launch` | Learning curve if unfamiliar |
| DigitalOcean App Platform | Click-ops UI, managed DBs | Paid tier for private container registry |
| AWS ECS / EKS | Full control | Overkill for sprint timeline |

➡ **Recommendation:** **Render** (or **Fly.io** if team already has experience).
We already have a multi-stage `Dockerfile`; Render can build & run it with a **single service**.

### 3.3 Backend-as-a-Service (Supabase vs Firebase)

| Feature | Supabase | Firebase |
|---------|----------|----------|
| SQL DB | Postgres (native) ✅ | Cloud Firestore / RTDB (NoSQL) ❌ |
| Auth | JWT w/ social providers | Firebase Auth |
| Edge / Functions | Deno-based | Cloud Functions |
| Realtime | Built on Postgres `LISTEN/NOTIFY` | WebSocket channel |

**Why Supabase is a maybe:**

* Our project **already** needs PostgreSQL—for Plone search indexing, upcoming features (alerts, schedules, etc.). Supabase can host this DB and provide auth/realtime _without extra ops_.
* Supabase **cannot** host Plone (requires ZODB & long-running WSGI).
  You’d still deploy Plone in a container platform (Render/Fly).

**Verdict:**
Use **Supabase** _optionally_ for:

1. Central Postgres instance (replace self-hosted DB).
2. Auth service for the React SPA (JWT compatible with FastAPI middleware).
3. Realtime channels (e.g., broadcast alerts).

Skip if Postgres is already bundled in your container platform or if time is tight.

---

## 4. Recommended Hybrid Deployment

| Component | Platform | Rationale |
|-----------|----------|-----------|
| React SPA | **Vercel** | Instant previews, CDN-backed, zero-config |
| FastAPI + Plone | **Render** (Docker) | Single Docker service, easy secrets, auto-deploy from GitHub |
| PostgreSQL | **Supabase** _or_ Render Postgres add-on | Choose Supabase if you want its auth & realtime features |
| Redis | Render free Redis add-on (or embedded in Docker Compose locally) | Low-latency caching |
| Celery Worker | Optional second Docker service on Render | Scales independently |

---

## 5. CI/CD Flow

1. **GitHub Actions**
   * Build & test (lint, pytest, coverage).
   * On `main` branch:
     - `docker build` → push to registry (ghcr.io).
     - Trigger Render deploy via API.
2. **Vercel** auto-builds the SPA on push to `main` of `gui/` folder (or separate repo).
3. **Environment variables / secrets** stored in GitHub and synced to Render & Vercel.
4. **Blue-green strategy** (Render "preview → promote" or Fly.io releases) enables **1-click rollback**.

---

## 6. Rollback & Disaster Recovery

* **Frontend:** Re-deploy previous Vercel build (UI toggle).
* **Backend:** Promote previous Render release or `fly deploy --strategy immediate`.
* **Database:** Supabase point-in-time recovery / automated backups.
* **ZODB (Plone):** Nightly `repozo` backups shipped to S3 via cron.

---

## 7. Next Steps

1. Decide **Supabase vs platform-provided Postgres** by _Friday noon_.
2. Configure Render infrastructure-as-code (`render.yaml`) in `infra/` folder.
3. Add GitHub Actions job to trigger Render deploy (`render-deploy`) and Vercel build hook.
4. Document secrets required (`.github/SECRETS.md`) and update `.env.example`.
5. Smoke-test staging URLs before Sunday cut-off.

---

## 8. FAQ

**Q:** _Can we deploy everything on Vercel?_
**A:** Vercel is great for static or serverless workloads, but long-running **Plone** processes exceed its execution model and memory limits.

**Q:** _Why not Firebase?_
**A:** Firebase’s NoSQL store doesn’t mesh with our Postgres-centric stack, and we’d lose SQL features needed by legacy reports.

**Q:** _Is Kubernetes worth it?_
**A:** Not for a weekend sprint—container PaaS solutions give 80 % of the benefit with 10 % of the effort.

---

_Questions or concerns? Open an issue or ping **#eduhub-devops** on Slack._
