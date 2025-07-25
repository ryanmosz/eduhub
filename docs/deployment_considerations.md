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

* **Not Recommended** – Technical or timeline constraints make this option risky for the weekend delivery.

### 3.5 Why the "Enterprise Plone" Advice Still Matters

You shared a summary of how large companies deploy Plone (dedicated
servers, Kubernetes, managed hosting, etc.).  Although our project is *much*
smaller in scope and time-boxed to a weekend sprint, the same principles
influence our choices:

* **Security & Updates** – Even a hobby deployment must let us patch Plone
  quickly (managed add-ons or Docker rebuilds).
* **Stateful ZODB** – Plone’s object database lives *inside* the container
  filesystem unless we mount persistent volumes or use an external storage
  backend.  Any host we choose must support persistent volumes/snapshots.
* **Reverse Proxy & Caching** – Plone benefits from a fronting proxy (e.g.
  Nginx or Traefik).  Platforms like Render and Fly.io provide this out of
  the box.
* **CI/CD & Rollback** – The advice about GitHub Actions, Docker, and blue-green
  deployments maps directly onto our existing pipeline and Sunday deadline.
* **Vertical vs Horizontal Scaling** – We won’t cluster Plone this weekend,
  but knowing it *can* scale vertically (bigger container) or horizontally
  (multiple instances behind a load-balancer) means our chosen host should
  not block future growth.

### 3.6 Minimum-Viable Deployment Stack for the Weekend Sprint

| Layer | Platform | Rationale |
|-------|----------|-----------|
| **React SPA** | **Vercel** (static hosting) | Free tier, instant previews, zero server maintenance. |
| **FastAPI + Plone** | **Render** *(Docker service with persistent disk)* | One-click deploy from Dockerfile, built-in TLS, free preview envs, supports 512 MB+ RAM needed by Plone, easy secrets UI. |
| **Database** | **Render Postgres add-on** (initially) | Zero extra accounts, 1-click provisioning; can migrate to Supabase later if we need its auth/realtime features. |
| **Redis (optional cache)** | Skip for MVP | Plone performs acceptably without Redis for a demo; add later if benchmarks demand it. |

**Why not Kubernetes / AWS ECS?**
Too much YAML, cluster setup, and IAM wiring for a 4-day sprint.

**Why not Supabase for *everything*?**
Supabase is excellent for Postgres + Auth, but it cannot run the
stateful Plone process. We can still point our FastAPI code at a
Supabase Postgres later without changing the container host.

**Deployment Flow Recap**

1. GitHub push → GitHub Actions builds & tests.
2. On `main` branch success:
   * `docker build` and push to `ghcr.io`.
   * Call Render Deploy Hook → Render pulls the new image, spins up
     replacement container, performs health-check, and promotes it live.
3. Vercel auto-builds the SPA from `/frontend` (or top-level) and deploys
   to the CDN.
4. Rollback = click "Redeploy previous" on Render *or* Vercel.

With this stack, we meet the Sunday 20:00 deadline **and** keep a clean
growth path for future scaling.

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

## 9. Final Deployment Decision & Timeline

### Locked-In Stack

| Layer | Platform | Status |
|-------|----------|--------|
| **Frontend (React Admin SPA)** | **Vercel** – static hosting | ✅ Locked |
| **Backend (FastAPI + Plone)** | **Render** – Docker service with persistent disk | ✅ Locked |
| **Database** | Render Postgres add-on | ✅ Locked |
| **Cache / Realtime** | None for MVP (may add Redis & WebSocket hub in Phase 7) | ⏳ Later |

This combination minimises ops overhead while meeting the Sunday 20:00 deadline:
* Vercel handles the SPA as a pure static site with global CDN.
* Render runs the long-lived FastAPI + Plone container and the Postgres add-on.

### Deployment Order & Alignment with Project Phases

| Project Phase (see `tasks/tasks-overall-project-plan.md`) | When We Deploy | What Gets Deployed | Target Platform |
|-----------------------------------------------------------|----------------|--------------------|-----------------|
| **Phase 2 – Python 3.11 + Async Upgrade Harness** | After phase completion (tests green) | First backend image (FastAPI + Plone) | **Render** |
| **Phase 3 – OAuth2 / SSO Gateway** | Immediately after gateway endpoints pass CI | Updated backend image | **Render** |
| **Phase 4 – Headless JSON API** | After REST & GraphQL endpoints stabilise | Backend image | **Render** |
| **Phase 5 – React Admin SPA** | End of Day 2 in GUI schedule | Initial SPA build (static) | **Vercel** |
| **Phase 6 – Dockerised CI/CD Pipeline** | During phase | GitHub → Render & Vercel hooks wired for automatic deploys | Both |
| **Phase 7 – Realtime Alert Broadcasting** | After WebSocket hub passes load-tests | Backend image (adds WebSocket + Slack) | **Render** |
| **Phase 8 – QA & Final Demo (Sunday ≤ 20:00)** | Final cut-off | Last successful backend image + SPA build | Render & Vercel |

### CI/CD Flow Snapshot

1. **Backend**
   * `main` branch → GitHub Actions → build & push Docker image → trigger **Render Deploy Hook**.
   * Render runs health-checks; if green, it promotes the new container.

2. **Frontend**
   * `main` branch in `/frontend` (or dedicated repo) → Vercel auto-builds and caches assets → deploys to global CDN.

3. **Rollback**
   * Render: "Promote previous" button or CLI.
   * Vercel: redeploy prior build.

With this locked-in plan, every phase has a clear deployment target and the entire stack can be live—and rollback-ready—before the Sunday deadline.
