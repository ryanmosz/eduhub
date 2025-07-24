## Relevant Files

- `pyproject.toml`, `tox.ini`, `requirements*.txt` – Version targets, dependencies, tooling.
- `src/` – All runtime code requiring syntax & async refactors.
- `tests/` – Ensure parity across Python 3.9 and 3.11.
- `.github/workflows/ci.yml` – Add matrix strategy updates.
- `docs/` – Migration playbook & performance reports.

### Notes

This list contains **parent tasks only**. After reviewing, reply "Go" and we will expand each into detailed sub-tasks.

## Tasks — Phase 2 Parent Tasks

- [ ] **2.1 Branch & Environment Setup**
  - Create `feat/python311-upgrade` branch; prepare tox environments for py39, py311.

- [ ] **2.2 Automated Syntax Migration**
  - Run `lib2to3` (legacy sweep) and `pyupgrade --py39-plus`; commit machine changes.

- [ ] **2.3 Dependency Audit & Updates**
  - Use `caniusepython3` to identify blockers; upgrade/replace unsupported libraries.

- [ ] **2.4 Async-Ready Refactor Pass**
  - Replace blocking I/O libs (`requests` → `httpx`), wrap legacy sync views with `@sync_to_async`, add Celery async tasks.

- [ ] **2.5 Test Matrix & Parity Gate**
  - Ensure all unit & integration tests pass on both Python versions via tox and CI matrix.

- [ ] **2.6 Performance & Profiling Benchmark**
  - Measure key endpoints; target ≥ 15 % latency improvement vs. 3.9 baseline.

- [ ] **2.7 Documentation & Merge**
  - Draft "Python 3.11 Migration Playbook", update README badges, open PR for code review & merge to `main`.