## Relevant Files

- `src/eduhub/open_data/__init__.py` – Package initialisation.
- `src/eduhub/open_data/endpoints.py` – FastAPI router exposing public `/data` endpoints.
- `src/eduhub/open_data/models.py` – Pydantic response models for public content.
- `src/eduhub/open_data/serializers.py` – Helpers to convert Plone objects into public schemas.
- `src/eduhub/open_data/pagination.py` – Offset/limit & cursor pagination utilities.
- `src/eduhub/open_data/cache.py` – Redis (or in-memory) caching helpers.
- `src/eduhub/open_data/rate_limit.py` – Thin wrapper around existing rate-limit middleware.
- `src/eduhub/open_data/benchmarks.py` – pytest-benchmark suite for latency targets.
- `src/eduhub/open_data/tests/` – Test suite for Open Data API.
- `src/eduhub/plone_integration.py` – Add read-only helpers for bulk public queries.
- `tests/fixtures/sample_public_content.json` – Fixture with anonymised Plone items.
- `tests/fixtures/pagination_edge_cases.json` – Fixture for pagination corner cases.
- `docs/api/endpoints/open-data.md` – Endpoint documentation.
- `.env.example` – Add `OPEN_DATA_CACHE_TTL`, `OPEN_DATA_RATE_LIMIT`.
- **Dependencies / Integration Points** – Existing rate-limit middleware, Redis cache, PloneClient, logging system.
- **Sample Fixtures** – Public content JSON, pagination edge-case payloads, benchmark baseline data.

### Notes

- Endpoints are **public read-only**; no authentication required but rate-limited.
- All external Plone calls are mocked in CI to ensure deterministic tests.
- Acceptance target: **average list request ≤ 50 ms** (cache hit) measured via pytest-benchmark.

---

## Tasks — Phase 6 Detailed Sub-Tasks

- [x] **6.1 Public Content Endpoint Scaffold**
  _Risk & Mitigation_: **Scope creep** → start with two core endpoints only; add more after baseline stabilises.
  - [x] 6.1.1 Create `open_data` router with `GET /data/items` and `GET /data/item/{uid}`.
  - [x] 6.1.2 Register router in `src/eduhub/main.py` under tag "Open Data".
  - [x] 6.1.3 Add OpenAPI docs with examples and 200 / 404 responses.
  - [x] 6.1.4 **TEST** (`pytest`, `fastapi.testclient`) : calling `/data/items` returns 200 OK with list payload stubbed by fixture.
  - [x] 6.1.5 **TEST** (`pytest`, `fastapi.testclient`) : unknown UID on `/data/item/{uid}` returns 404 JSON error when Plone mock raises 404.

- [x] **6.2 Data Serialization & Response Models**
  _Risk & Mitigation_: **Inconsistent field mapping** → lock schema via strict Pydantic models.
  - [x] 6.2.1 Implement `ItemPublic` and `ItemListResponse` models in `models.py` (`Config.strict = True`).
  - [x] 6.2.2 Create `serializers.py` with `to_public(item: dict) -> ItemPublic`.
  - [x] 6.2.3 Add unit tests for edge cases: missing optional fields, unexpected extra keys.
  - [x] 6.2.4 **TEST** (`pytest`) : serializer raises `ValidationError` on invalid Plone data (mocked).
  - [x] 6.2.5 **TEST** (`pytest`) : round-trip (Plone → serializer → jsonable encoder) matches expected fixture.

- [x] **6.3 Query Filtering, Search & Pagination**
  _Risk & Mitigation_: **Expensive queries** → delegate heavy search to Plone, enforce sane limits.
  - [x] 6.3.1 Define query parameters (`search`, `portal_type`, `path`, `limit`, `offset`, `cursor`).
  - [x] 6.3.2 Implement `pagination.py` with offset & opaque cursor helpers.
  - [x] 6.3.3 Integrate parameters into `PloneClient.search_content` call (async, mocked in tests).
  - [x] 6.3.4 Update `/data/items` endpoint to return `next_cursor` when more data available.
  - [x] 6.3.5 **TEST** (`pytest`, `fastapi.testclient`) : requesting `limit=5` returns at most 5 items and valid `next_cursor`.
  - [x] 6.3.6 **TEST** (`pytest`) : pagination edge-case fixture yields stable ordering and no duplicates when iterating cursors.

- [x] **6.4 Caching, Rate Limiting & Performance Benchmarks**
  _Risk & Mitigation_: **Cache stampede** → use Redis with per-URL mutex and exponential back-off on miss.
  - [x] 6.4.1 Implement `cache.py` with `get(key)`, `set(key, ttl)` + in-memory fallback.
  - [x] 6.4.2 Wire caching into endpoints: serve cached JSON for identical query strings.
  - [x] 6.4.3 Add `rate_limit.py` thin wrapper configuring 60 req/min per IP via existing middleware.
  - [x] 6.4.4 Write `benchmarks.py` using `pytest-benchmark` to assert cache-hit latency ≤ 10 ms.
  - [x] 6.4.5 **TEST** (`pytest-asyncio`, `respx`) : cache hit avoids outbound HTTP call (assert `PloneClient.search_content` not awaited).
  - [x] 6.4.6 **TEST** (`pytest-benchmark`) : benchmark passes target thresholds (< 50 ms list, < 20 ms item detail).

- [x] **6.5 Automated Testing & Documentation**
  _Risk & Mitigation_: **Docs drift** → CI validates doc build & example snippets.
  - [x] 6.5.1 Achieve ≥ 90 % coverage for `open_data` package (unit + integration tests).
  - [x] 6.5.2 Generate `docs/api/endpoints/open-data.md` via OpenAPI export + hand-written examples.
  - [x] 6.5.3 Add CI step to run `mkdocs build` and fail on warnings.
  - [x] 6.5.4 Update `scripts/quick_integration_test.py` to include public data workflow.
  - [x] 6.5.5 **TEST** (`pytest`, CI) : `tox -e py39,py311` passes all suites with new package.
  - [x] 6.5.6 **TEST** (`mkdocs`, GitHub Actions) : documentation build passes and includes `/data` endpoints section.

---
