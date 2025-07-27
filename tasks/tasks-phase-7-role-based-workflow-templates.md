## Relevant Files

- `src/eduhub/workflows/__init__.py` – Package initialisation.
- `src/eduhub/workflows/templates.py` – Pre-defined Plone workflow templates & role mappings.
- `src/eduhub/workflows/endpoints.py` – FastAPI router exposing `/workflows` management endpoints.
- `src/eduhub/workflows/models.py` – Pydantic models for workflow definitions, state transitions & permissions.
- `src/eduhub/workflows/services.py` – Business logic for applying templates to Plone instances.
- `src/eduhub/workflows/permissions.py` – Helpers for permission matrix validation.
- `src/eduhub/plone_integration.py` – Add helpers for workflow CRUD and role assignment.
- `tests/test_workflows/` – Test suite for workflow template feature.
- `tests/fixtures/sample_workflow_template.json` – Happy-path fixture.
- `tests/fixtures/invalid_workflow_template.json` – Edge-case / error fixture.
- `docs/api/endpoints/workflows.md` – Endpoint documentation.
- `.env.example` – Add `WORKFLOW_DEFAULT_TEMPLATE`.
- **Dependencies / Integration Points** – Auth middleware (role checks), PloneClient, rate-limit middleware, Redis cache for metadata.
- **Sample Fixtures** – JSON workflow templates, role-mapping tables, permission matrices.
- **Benchmarks / Acceptance Targets** – Apply a template to a fresh Plone site in ≤ 2 s; endpoint latency ≤ 100 ms.

### Notes

- Templates target common education-program workflows (Draft → Review → Published → Archived).
- Feature must queue changes if Plone is temporarily unavailable.
- All external Plone calls are mocked in CI to keep tests deterministic.

---

## Tasks — Phase 7 Detailed Sub-Tasks

- [ ] **7.1 Workflow Template Schema Design**
  _Risk & Mitigation_: Complex permission matrices → start with minimal viable schema; iterate after prototype review.
  - [ ] 7.1.1 Define `WorkflowTemplate` & `WorkflowState` Pydantic models in `models.py`.
  - [ ] 7.1.2 Draft JSON schema examples (`sample_workflow_template.json`, `invalid_workflow_template.json`).
        **TEST (pytest, pydantic)**: Loading valid sample passes model validation.
  - [ ] 7.1.3 Implement `templates.py` with two built-in templates (`simple_review`, `extended_review`).
  - [ ] 7.1.4 Document schema in `docs/api/endpoints/workflows.md` with JSON examples.
        **TEST (mkdocs build)**: Docs build passes with no warnings.
  - [ ] 7.1.5 Add mypy strict typing for new models & templates.

- [ ] **7.2 Plone Integration Layer Enhancements**
  _Risk & Mitigation_: API differences between Plone 5 & 6 → detect version at runtime and branch logic.
  - [ ] 7.2.1 Extend `PloneClient` with `get_workflows()`, `apply_workflow(template)` async helpers.
  - [ ] 7.2.2 Implement version detection (`/portal_migration/getVersion` endpoint).
        **TEST (pytest-asyncio, respx mock)**: Version detection returns correct enum for mocked responses.
  - [ ] 7.2.3 Handle workflow application via REST API for Plone 6 and XML-RPC fallback for Plone 5.
  - [ ] 7.2.4 Gracefully queue template application if Plone unreachable; persist queue in Redis.
        **TEST (pytest-asyncio)**: Simulate network failure → tasks pushed to queue and retried.
  - [ ] 7.2.5 Update logging & error mapping to `PloneAPIError`.

- [ ] **7.3 FastAPI Management Endpoints**
  _Risk & Mitigation_: Unauthorized template changes → enforce role checks (`admin`, `workflow_manager`) on every route.
  - [ ] 7.3.1 Scaffold router in `endpoints.py` under `/workflows` tag.
  - [ ] 7.3.2 Implement `POST /workflows/apply/{template_name}` (body optional overrides).
  - [ ] 7.3.3 Implement `GET /workflows/templates` returning available template metadata.
  - [ ] 7.3.4 Protect routes with `Depends(require_role("workflow_manager"))`.
        **TEST (pytest, fastapi.TestClient, JWT mock)**: Request without role returns 403.
  - [ ] 7.3.5 Integrate OpenAPI docs: security scheme, examples, response models.
        **TEST (pytest)**: `/openapi.json` contains `/workflows/apply/{template_name}` with 202/403 responses.

- [x] **7.4 Role & Permission Mapping Engine**
  _Risk & Mitigation_: Mismatched role names across systems → maintain central mapping table; add validation step.
  - [x] 7.4.1 Create `permissions.py` utility to translate EduHub roles → Plone roles.
  - [x] 7.4.2 Add validation step ensuring all roles in template exist in both systems.
        **TEST (pytest)**: Loading template with unknown role raises `RoleMappingError`.
  - [x] 7.4.3 Implement `services.apply_template()` that iterates states & transitions, applying permissions.
  - [x] 7.4.4 Benchmark permission application on dataset with 1000 items.
        **TEST (pytest-benchmark)**: Average apply time ≤ 500 ms.
  - [x] 7.4.5 Update `audit.log` with before/after role assignments for traceability.

- [x] **7.5 Automated Testing, Benchmarking & Documentation**
  _Risk & Mitigation_: Docs drift vs code → CI step builds MkDocs & fails on warnings.
  - [x] 7.5.1 Write unit tests covering ≥ 90 % of `workflows` package (`pytest`, `pytest-asyncio`, `respx` mocks).
  - [x] 7.5.2 Add integration test `tests/test_workflows/test_apply_template.py` simulating full HTTP flow with mocked Plone.
        **TEST (fastapi.TestClient + respx)**: Successful apply returns 202 and enqueues background job.
  - [x] 7.5.3 Add performance benchmark in `tests/test_workflows/benchmarks.py` measuring template apply latency.
        **TEST (pytest-benchmark)**: Ensure latency target (≤ 2 s) met.
  - [x] 7.5.4 Extend CI (`.github/workflows/ci.yml`) with new test path and MkDocs build.
  - [x] 7.5.5 Update `docs/api/endpoints/workflows.md` with curl examples and success/error payloads.
  - [x] 7.5.6 Final pass: run `tox -e py39,py311` → all tests & benchmarks pass.
        **TEST (CI)**: Workflow green on GitHub Actions.

---
