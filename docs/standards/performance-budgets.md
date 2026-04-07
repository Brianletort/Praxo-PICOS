# Performance Budgets

## Initial budgets (v1)

| Metric | Budget | Measurement |
|--------|--------|-------------|
| App cold start (Electron) | < 5 seconds | Time from launch to UI visible |
| API health endpoint | < 50ms p95 | pytest-benchmark |
| Web dev startup | < 10 seconds | Time from `npm run dev` to ready |
| Search latency (hybrid) | < 500ms p95 | pytest-benchmark with 10k records |
| Indexing throughput | > 100 records/sec | pytest-benchmark batch indexing |
| Memory usage (idle) | < 500 MB RSS | Measured after 1 hour idle |

## Rules

- PRs run smoke performance checks only (fast subset)
- Nightly CI runs full performance suite
- Regressions > 20% from baseline fail CI
- Baselines stored in `tests/regression/performance/baselines/*.json`
- Baseline updates require explicit PR with justification

## Measurement methodology

- All benchmarks run on clean state (fresh temp directories)
- Minimum 5 iterations for timing stability
- Report p50, p95, p99
- Compare against stored baseline JSON
