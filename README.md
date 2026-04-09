# Praxo-PICOS

**Praxo Personal Intelligence Operating System** -- your second brain for macOS. Captures context from email, calendar, screen activity, documents, and notes, then makes it searchable and actionable. Everything runs locally -- your data never leaves your machine.

## Quick Start (2 minutes)

### One-line install:

```bash
curl -fsSL https://raw.githubusercontent.com/Brianletort/Praxo-PICOS/v0.3.4/scripts/install.sh | bash
```

This automatically:
- Installs Python and Node.js if needed (via Homebrew)
- Downloads and sets up Praxo-PICOS
- Downloads the Qdrant vector database
- Creates the `picos` command

The installer is pinned to the `v0.3.4` release by default, so users get a reproducible build instead of whatever happens to be on `main`.

### Launch:

```bash
picos
```

Then open **http://127.0.0.1:3100** in your browser. The smart onboarding wizard will guide you through setup.

### Grant Full Disk Access (for email and calendar)

To read your Mail and Calendar data, macOS requires Full Disk Access:

1. Open **System Settings > Privacy & Security > Full Disk Access**
2. Click the **+** button
3. Navigate to your terminal app (Terminal.app or iTerm) and add it
4. Restart `picos`

## What's Included

Everything runs locally on your machine -- no cloud services required.

| Component | Description |
|-----------|-------------|
| **Qdrant** | Vector database for semantic search (bundled binary) |
| **FastAPI** | Backend API with SQLite and FTS5 full-text search |
| **Next.js** | Web dashboard with smart onboarding |
| **MCP Server** | 5 tools for AI assistant integration |

## Features

- **5 data sources**: Mail, Calendar, Screenpipe, Documents, Obsidian Vault
- **Automatic extraction**: Background pipeline runs every 15 minutes
- **Full-text search**: BM25-ranked search across all indexed data
- **AI assistant chat**: Natural language search over your personal knowledge base
- **Smart onboarding**: Auto-detects Obsidian vaults, Screenpipe, Docker, and Agent Zero
- **Health Center**: Real-time monitoring of all services with one-click repair
- **Self-healing**: Crashed services restart automatically with exponential backoff
- **Config validation**: Path checks, port validation, and helpful error messages

## Architecture

| Service | Port | Description |
|---------|------|-------------|
| API server | 8865 | FastAPI backend with SQLite + FTS5 |
| Web dashboard (source install) | 3100 | Next.js dev server used by `picos` |
| Web dashboard (packaged runtime) | 3777 | Next.js standalone runtime used by the desktop app |
| Qdrant | 6733 | Vector search |
| MCP server | 8870 | AI tool integration |

All data is stored at `~/Library/Application Support/Praxo-PICOS/`.

## Optional: Agent Zero (AI assistant)

For a smarter AI assistant, install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and enable Agent Zero in Settings. Praxo-PICOS will manage the Docker container for you.

## Development

```bash
git clone https://github.com/Brianletort/Praxo-PICOS.git
cd Praxo-PICOS
make bootstrap
make dev-api    # Terminal 1: API on :8865
make dev-web    # Terminal 2: Web on :3100
```

### Testing

```bash
make test               # Unit + contract tests
make regression         # Full regression suite
cd apps/web && npm run e2e   # Playwright E2E tests
```

## macOS Desktop App

The latest GitHub release includes unsigned internal-use `.dmg` and `.pkg` installer assets for Apple Silicon Macs.

Because they are unsigned, macOS may quarantine them. If that happens:

```bash
xattr -dr com.apple.quarantine "/Applications/Praxo-PICOS.app"
```

Or right-click the app and choose **Open** once to bypass Gatekeeper for internal testing.

A signed and notarized desktop installer is still pending Apple Developer ID signing. The versioned install script above remains the most reliable path.

## License

Proprietary. All rights reserved.
