## Relevant Files

- `src/eduhub/oembed/__init__.py` – Package initialisation.
- `src/eduhub/oembed/endpoints.py` – FastAPI router exposing `/embed` proxy endpoint(s).
- `src/eduhub/oembed/client.py` – Async HTTP client handling upstream oEmbed requests & caching.
- `src/eduhub/oembed/cache.py` – Redis (or in-memory) caching utilities for embed responses.
- `src/eduhub/oembed/models.py` – Pydantic models for request/response validation.
- `src/eduhub/oembed/security.py` – Domain allow-list, HTML sanitiser utilities.
- `src/eduhub/oembed/tests/` – Test suite for oEmbed feature.
- `src/eduhub/plone_integration.py` – Helper to inject embed HTML into Plone content responses.
- `tests/fixtures/sample_oembed_urls.json` – Valid/invalid URL fixture set.
- `tests/fixtures/sample_embed_response.json` – Saved oEmbed provider payload used in mocks.
- `.env.example` – Add `OEMBED_ALLOWED_PROVIDERS`, `OEMBED_CACHE_TTL`.
- **Dependencies / Integration Points** – Existing auth middleware (`get_current_user`), Redis service from Docker-Compose, PloneClient for content updates.
- **Sample Fixtures** – Local image/video URLs, mock provider responses for offline CI testing.

### Notes

- **Tooling context**: Tests use `pytest`, `pytest-asyncio`, `fastapi.testclient.TestClient`, and `respx` to mock external HTTP calls.
- **Benchmarks / Acceptance targets**: Cache hit latency `< 10 ms`; cache miss round-trip (network mocked) `< 300 ms`.
- All external HTTP calls MUST be stubbed in CI to avoid flaky tests.

---

## Tasks

Below are the detailed tasks required to deliver the **Rich-Media Embeds (oEmbed)** feature.

- [ ] **5.1 oEmbed Proxy Endpoint**
  _Risk & Mitigation_: Malformed URLs or untrusted domains → validate against allow-list & return 422 quickly.
  - [ ] 5.1.1 Scaffold `oembed` router; mount under `/embed` in `src/eduhub/main.py`.
  - [ ] 5.1.2 Implement `GET /embed?url=` with URL param validation (Pydantic `HttpUrl` + domain allow-list).
  - [ ] 5.1.3 Fetch oEmbed JSON via `oembed.client.fetch_embed()`, convert to sanitized HTML snippet (`bleach`).
  - [ ] 5.1.4 **TEST** (pytest + TestClient + respx): valid YouTube URL returns 200 with `{"html": "<iframe…"`}.
  - [ ] 5.1.5 **TEST** (pytest): disallowed domain returns HTTP 422 with error message "Provider not allowed".

- [ ] **5.2 Embed Retrieval & Caching Layer**
  _Risk & Mitigation_: Third-party rate-limits → add Redis cache & exponential back-off.
  - [ ] 5.2.1 Implement `oembed.client.fetch_embed(url)` with async `httpx` and per-provider endpoint resolution.
  - [ ] 5.2.2 Add `oembed.cache.get/set` wrappers (Redis preferred, fallback to in-memory dict).
  - [ ] 5.2.3 Store successful responses for `OEMBED_CACHE_TTL` seconds; serve cached HTML on hit.
  - [ ] 5.2.4 **TEST** (pytest-asyncio + respx): verify cache hit avoids outbound HTTP (respx assertion).
  - [ ] 5.2.5 **TEST** (benchmark): cache-hit path completes `< 10 ms` (pytest-benchmark).
  - [ ] 5.2.6 Document back-off strategy in code comments & README snippet.

- [ ] **5.3 Plone Content Integration**
  _Risk & Mitigation_: HTML injection could break pages → run sanitizer before storing.
  - [ ] 5.3.1 Extend `transform_plone_content()` to replace raw URLs with `<iframe>` embed HTML where applicable.
  - [ ] 5.3.2 Provide utility `inject_oembed(html:str) -> str` using regex to detect media links.
  - [ ] 5.3.3 Update content create/update endpoints to call injection util when `content_type=="Document"`.
  - [ ] 5.3.4 **TEST** (pytest + monkeypatch): posting Plone content with YouTube URL returns rendered embed HTML.
  - [ ] 5.3.5 **TEST** (pytest): sanitizer strips `<script>` tags from malicious oEmbed payloads.

- [ ] **5.4 Error Handling, Security & Rate Limiting**
  _Risk & Mitigation_: Abuse via rapid calls → integrate existing rate-limit middleware & per-IP quotas.
  - [ ] 5.4.1 Add `oembed/security.py` with HTML sanitization (`bleach`) and domain allow/deny lists.
  - [ ] 5.4.2 Integrate project-wide rate-limit middleware for `/embed` (20 req/min per IP).
  - [ ] 5.4.3 Map upstream HTTP failures (4xx/5xx/timeout) to meaningful FastAPI `HTTPException`s.
  - [ ] 5.4.4 **TEST** (pytest + respx): provider timeout raises 504 Gateway Timeout to caller.
  - [ ] 5.4.5 **TEST** (pytest): exceeding rate-limit returns HTTP 429 with `Retry-After` header.

- [ ] **5.5 Automated Testing & Documentation**
  _Risk & Mitigation_: Docs drift vs code → add doc CI job validating examples.
  - [ ] 5.5.1 Write unit tests for `client.py`, `cache.py`, `security.py` (target ≥ 90 % coverage).
  - [ ] 5.5.2 Create `tests/test_endpoints.py` covering success, validation and error paths (uses respx mocks).
  - [ ] 5.5.3 Generate OpenAPI docs; ensure `/embed` endpoint shows query params & auth requirements.
  - [ ] 5.5.4 Add section to `docs/api/endpoints/oembed.md` with usage samples & provider list.
  - [ ] 5.5.5 **TEST** (CI workflow): run `pytest -q` on py39 & py311 tox envs → expect 100 % pass.
  - [ ] 5.5.6 **TEST** (doc build): `mkdocs build` succeeds and includes oEmbed docs without warnings.

---