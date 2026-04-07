# Praxo-PICOS

**Praxo Personal Intelligence Operating System** — a commercial-grade macOS desktop app that captures, organizes, and surfaces your work context from email, calendar, screen activity, documents, and notes.

## Architecture

- **Desktop shell**: Electron app with service supervisor, self-healing, tray icon
- **Web UI**: Next.js dashboard with onboarding, health center, settings, memory search
- **Backend API**: FastAPI with SQLite + Qdrant for data persistence and vector search
- **Workers**: Extractors for Mail, Calendar, Screenpipe, Documents, Obsidian vault
- **MCP server**: FastMCP with 5 tools for Agent Zero integration
- **Agent Zero**: Managed Docker companion for AI assistant chat

## Repo layout

| Directory | Purpose |
|-----------|---------|
| `apps/web` | Next.js dashboard (port 3100 dev, 3777 prod) |
| `apps/desktop` | Electron shell with supervisor + self-healing |
| `services/api` | FastAPI backend (port 8865) |
| `services/workers` | Extractors, indexing, data flow monitor |
| `packages/shared` | Runtime contracts, shared constants |
| `tests/` | Unit, integration, contract, regression, performance |
| `docs/` | Standards, architecture, runbooks |
| `packaging/` | macOS signing, notarization, release scripts |
| `infra/` | Docker compose for Qdrant |
| `.github/workflows/` | CI: fast, e2e, nightly, regression, release |

## Local ports

| Service | Port |
|---------|------|
| API / dashboard | 8865 |
| Web dev | 3100 |
| Web packaged | 3777 |
| MCP server | 8870 |
| Qdrant HTTP | 6733 |
| Qdrant gRPC | 6734 |

## Quick start

```bash
make bootstrap          # Python venv + Node deps
make dev-api            # Start API on :8865
make dev-web            # Start web UI on :3100
make test               # Run unit + contract tests
make regression         # Full regression suite
make regression-fast    # Fast subset for PRs
```

## Testing

- **108+ Python tests** (unit, contract, regression, performance, data quality)
- **8 Vitest tests** (component + integration)
- **21 Node tests** (supervisor, self-healing, Docker manager)
- **5 CI workflows** (fast, e2e, nightly, regression-pr, regression-nightly)
- **Regression monotonicity**: test count never decreases

## Release

```bash
git tag v0.1.0 && git push origin v0.1.0  # Triggers macos-release workflow
```

See `docs/runbooks/release.md` for signing and notarization details.
