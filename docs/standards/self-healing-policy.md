# Self-Healing Policy

## Service health checks

| Service | Check method | Interval | Timeout |
|---------|-------------|----------|---------|
| API (FastAPI) | GET /health | 10 sec | 3 sec |
| Workers | Internal heartbeat | 30 sec | 5 sec |
| Qdrant | GET /healthz | 10 sec | 3 sec |
| Web UI | GET / | 15 sec | 5 sec |
| Agent Zero (Docker) | Container inspect + health | 30 sec | 10 sec |
| MCP Server | GET /health | 15 sec | 3 sec |

## Restart policy

- On health check failure: retry 3 times with 2-second intervals
- If still failing: restart the service
- Restart with exponential backoff: 1s, 2s, 4s, 8s, 16s (max)
- After 5 restart attempts: mark service as "needs attention" and surface to user
- Log every restart attempt with timestamp and reason

## Port conflict resolution

1. Detect port in use via lsof/netstat
2. If owned by another PICOS process: kill stale process
3. If owned by external process: alert user with process name and suggest action
4. Never silently change ports -- user must be informed

## Permission recovery

- On extraction failure due to permission: check TCC database
- Surface missing permission in Health Center with guided fix
- Open correct System Settings pane via Apple URI scheme
- Re-check after user returns to app

## Rollback

- Before any update: snapshot current service versions
- After failed update: restore from snapshot
- Log rollback reason for diagnostics
