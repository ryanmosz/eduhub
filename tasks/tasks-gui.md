### Relevant Files

- `frontend/package.json` – Lists front-end dependencies (React, Vite, **tailwindcss@^4**, shadcn/ui, Auth0 SDK).
- `frontend/vite.config.ts` – Vite build/serve configuration with Tailwind plugin.
- `frontend/tailwind.config.js` – Tailwind CSS v4 configuration (content paths, theme).
- `frontend/postcss.config.js` – PostCSS pipeline (tailwindcss, autoprefixer).
- `frontend/src/components/` – Shared UI components (ShadCN primitives + project-specific composites).
- `frontend/src/pages/` – Feature pages consuming APIs (import, embeds, data, workflows, alerts).
- `frontend/.env.example` – API_BASE_URL, AUTH0_*, etc.

#### Dependencies / Integration Points

- FastAPI endpoints from Phases 3-8 (`/auth`, `/import/schedule`, `/embed`, `/data`, `/workflows`, `/alerts/ws`).
- Auth0 tenant for OAuth2.
- WebSocket hub for real-time alerts.

#### Sample Fixtures

- `tests/fixtures/mock_api_responses.json` – MSW mock payloads for API calls.
- `tests/fixtures/sample_csv_schedule.csv` – Used in Schedule Import wizard tests.

### Notes

Reply **"Go"** to generate detailed sub-tasks (Phase-2).
Each parent task includes a brief *Risk & Mitigation* line.

## Tasks — Phase 9 Parent Tasks

- [ ] **9.1 Front-End Scaffold & Tooling Setup**
  *Risk & Mitigation*: Misconfigured styling pipeline ⇒ lock in **Tailwind v4** and run `tailwindcss --validate` in CI.
  - [ ] 9.1.1 Bootstrap Vite + React-TS project in `/frontend` (`npm create vite@latest`) — supports Phase 2 (Python 3.11 upgraded toolchain).
  - [ ] 9.1.2 Install **tailwindcss@^4**, `postcss`, `autoprefixer`, run `npx tailwindcss init -p`, configure `tailwind.config.js` (paths = `src/**/*.{ts,tsx}`) — supports Phase 5 (Rich-Media Embeds UI needs utility classes).
  - [ ] 9.1.3 Initialise ShadCN UI (`npx shadcn-ui@latest init`) and scaffold primitives (Button, Card) in `src/components/ui` — supports all GUI work (Phases 4-8).
  - [ ] 9.1.4 Add ESLint (typescript, react, tailwind-class-sorting), Prettier & Husky hook running `yarn lint:fix` — supports every phase.
  - [ ] 9.1.5 Create `.github/workflows/frontend.yml` with steps `yarn install`, `yarn lint`, `yarn test`, `yarn build`; deploy to Vercel on `main` & preview on PRs — enables "deploy early" pledge across Phases 3-8.

- [ ] **9.2 Authentication, Routing & State Management**
  *Risk & Mitigation*: Token mis-alignment ⇒ reuse Auth0 React SDK, same audience/issuer.
  - [ ] 9.2.1 Add React-Router v6 routes (`/`, `/login`, `/dashboard`, feature pages).
  - [ ] 9.2.2 Integrate Auth0 React SDK; read `VITE_AUTH0_*` env vars — supports Phase 3 (OAuth2/SSO Gateway).
  - [ ] 9.2.3 Create `<ProtectedRoute>` wrapper to gate private pages — supports Phase 3.
  - [ ] 9.2.4 Implement `UserProvider` that parses JWT roles/claims; expose `useUser()` hook — supports Phase 7 (Role-Based Workflows).
  - [ ] 9.2.5 Add MSW mocks for `/auth/login`, `/auth/user` so GUI works before backend is ready — keeps parallel workstreams unblocked (Phases 3-5).

- [ ] **9.3 Feature Screens & Component Library (ShadCN + Tailwind v4)**
  *Risk & Mitigation*: Accidental Tailwind v3 snippets ⇒ ESLint plugin `@tailwindcss/no-custom-classname`.
  - [ ] 9.3.1 Build "CSV Schedule Import" wizard page with file-drop & preview table — supports Phase 4 (CSV Schedule Importer).
  - [ ] 9.3.2 Create `EmbedPreview` component rendering sanitized oEmbed HTML — supports Phase 5 (Rich-Media Embeds).
  - [ ] 9.3.3 Implement "Open Data" list & detail pages with pagination controls — supports Phase 6 (Open Data API).
  - [ ] 9.3.4 Develop "Workflow Templates" admin screen with apply dialog & status chips — supports Phase 7 (Role-Based Workflows).
  - [ ] 9.3.5 Extract reusable UI primitives: Table, Modal, Toast, Badge — shared across Phases 4-8.
  - [ ] 9.3.6 Add Storybook (or Ladle) for component docs; auto-publish on Vercel preview.

- [ ] **9.4 Real-Time Alerts & WebSocket Integration**
  *Risk & Mitigation*: WS reconnection flood ⇒ use exponential back-off & cap retries.
  - [ ] 9.4.1 Implement `useWebSocket(url)` hook with back-off reconnect — supports Phase 8 (Real-Time Alert Broadcasting).
  - [ ] 9.4.2 Create `ToastNotification` component that listens to alert stream — supports Phase 8.
  - [ ] 9.4.3 Add unread-alert badge in header & mark-as-read mutation.
  - [ ] 9.4.4 Provide mock WS server in dev via MSW "mock-socket" so GUI works without backend.
  - [ ] 9.4.5 Integration smoke test: connect, receive mock alert, toast appears — proves Phase 8 UI readiness.

- [ ] **9.5 Testing, CI/CD & Production Build Pipeline**
  *Risk & Mitigation*: Flaky E2E tests ⇒ MSW for HTTP, mock-socket for WS, Playwright retries.
  - [ ] 9.5.1 Configure React-Testing-Library + Vitest; aim ≥ 90 % component coverage.
  - [ ] 9.5.2 Add MSW handlers for all API paths (`/auth`, `/embed`, `/data`, `/import`, `/alerts`) — supports Phases 3-8.
  - [ ] 9.5.3 Write Playwright E2E: login → import CSV preview → embed preview → receive alert — spans Phases 3, 4, 5, 8.
  - [ ] 9.5.4 Gate `frontend.yml` with `yarn test --coverage && yarn build` before Vercel deploy.
  - [ ] 9.5.5 Add Lighthouse-CI GitHub Action to assert PWA & performance scores ≥ 80.
  - [ ] 9.5.6 Document local dev scripts (`yarn dev`, `yarn test:watch`, `yarn storybook`) in README.
