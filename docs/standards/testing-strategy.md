# Testing Strategy

## Required layers

| Layer | Tool | Scope | When |
|-------|------|-------|------|
| Unit | pytest / Vitest | Pure logic, parsers, normalizers | Every PR |
| Integration | pytest + httpx | IO boundaries, API endpoints, DB | Every PR |
| Contract | pytest / Vitest | Schemas, payloads, env, config | Every PR |
| E2E | Playwright | Full user workflows | PR (web changes) + nightly |
| Regression | pytest + Playwright | Bug-fix coverage, never-deleted | Every PR + nightly |
| Performance | pytest-benchmark | Startup, search, indexing budgets | Nightly |
| Data quality | pytest + golden fixtures | Extraction correctness, freshness | Nightly |

## Coverage targets

- Python branch coverage: 85% minimum (enforced by pyproject.toml)
- Frontend line coverage: 80% minimum (enforced by vitest.config.ts)
- Every bug fix MUST add a regression test before or with the fix

## Rules

- No flaky test is accepted as normal. Fix or quarantine with a linked issue.
- Contract changes require docs updates in the same PR.
- Regression tests live in `tests/regression/` and must never be deleted.
- Performance baselines are tracked as JSON in `tests/regression/performance/baselines/`.
- Golden fixtures for DQ live in `tests/fixtures/golden/`.

## CI enforcement

- `ci-fast.yml`: unit + contract + smoke (every PR)
- `ci-e2e.yml`: Playwright E2E (web changes)
- `ci-nightly.yml`: regression + performance + integration + macOS smoke
- Regression monotonicity: CI checks that `tests/regression/` file count never decreases
