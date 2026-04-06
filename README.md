# Praxo-PICOS

Praxo Personal Intelligence Operating System.

## Repo layout
- apps/web — Next.js UI
- apps/desktop — Electron desktop shell (later)
- services/api — FastAPI backend
- services/workers — Extractors, indexing, orchestrators
- packages/shared — Cross-surface types, schemas, constants
- tests — All test layers
- docs — Architecture, standards, runbooks

## Local ports
- API / dashboard: 8865
- Web dev: 3100
- Web packaged: 3777
- MCP: 8870
- Qdrant HTTP: 6733
- Qdrant gRPC: 6734

## Quick start
```bash
make bootstrap
make dev-api    # starts API on 8865
make dev-web    # starts web on 3100
make test       # runs all tests
```
