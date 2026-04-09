# Praxo-PICOS

**Praxo Personal Intelligence Operating System** -- your second brain for macOS. Captures context from email, calendar, screen activity, documents, and notes, then makes it searchable and actionable. Everything runs locally -- your data never leaves your machine.

## Quick Start (2 minutes)

### One-line install:

```bash
curl -fsSL https://raw.githubusercontent.com/Brianletort/Praxo-PICOS/main/scripts/install.sh | bash
```

This automatically:
- Installs Python and Node.js if needed (via Homebrew)
- Downloads and sets up Praxo-PICOS
- Downloads the Qdrant vector database
- Creates the `picos` command

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
| Web dashboard | 3100 | Next.js with smart UI |
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

## macOS Desktop App (Coming Soon)

A signed and notarized `.dmg` installer is in development. The current release uses the install script above for maximum compatibility across macOS versions.

## License

Proprietary. All rights reserved.
