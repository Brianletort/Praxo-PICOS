# Praxo-PICOS

**Praxo Personal Intelligence Operating System** -- your second brain for macOS. Captures, organizes, and surfaces your work context from email, calendar, screen activity, documents, and notes.

## Installation (macOS)

### Step 1: Download

Download `Praxo-PICOS-0.3.0-arm64.dmg` from the [latest release](https://github.com/Brianletort/Praxo-PICOS/releases/latest).

### Step 2: Install

Open the DMG and drag **Praxo-PICOS** to your Applications folder.

### Step 3: Allow the app to run

Since this app is not yet notarized by Apple, macOS will block it on first launch. To fix this:

**Option A (recommended):** Right-click the app in Applications, select "Open", then click "Open" in the dialog.

**Option B (terminal):** Run this command once:
```bash
xattr -dr com.apple.quarantine /Applications/Praxo-PICOS.app
```

### Step 4: Launch and set up

Launch Praxo-PICOS. The onboarding wizard will:
- Auto-detect your Obsidian vaults and suggest the best path
- Let you choose which data sources to enable
- Configure your AI provider
- Start all background services automatically

### Step 5: Grant Full Disk Access (for Mail and Calendar)

To read your email and calendar, macOS requires Full Disk Access:

1. The app will prompt you to open System Settings
2. Go to **Privacy & Security > Full Disk Access**
3. Find **Praxo-PICOS** and toggle it on
4. Restart the app

## What's included

The DMG bundles:

- Next.js web dashboard (standalone server -- no Node.js install needed)
- Qdrant vector database (native ARM64 binary)
- FastAPI backend server
- MCP server for AI assistant integration
- Electron desktop shell with service supervisor and self-healing

### One requirement: Python 3.12+

The backend runs on Python. If you don't have it:
```bash
# Install via Homebrew (recommended):
brew install python@3.14

# Or download from python.org
```

On first launch, the app automatically creates a Python environment and installs all dependencies. This takes ~30 seconds and only happens once.

## Features

- **5 data sources**: Mail, Calendar, Screenpipe, Documents, Obsidian Vault
- **Automatic extraction**: Background pipeline runs every 15 minutes
- **Full-text search**: FTS5-powered search across all your data
- **AI assistant chat**: Search your memories with natural language
- **MCP server**: 5 tools for Agent Zero integration
- **Health Center**: Live service monitoring with self-healing
- **Smart onboarding**: Auto-detects installed tools and suggests configuration
- **Self-healing**: Crashed services restart automatically with exponential backoff

## Architecture

| Component | Port | Description |
|-----------|------|-------------|
| API server | 8865 | FastAPI backend with SQLite + FTS5 |
| Web dashboard | 3777 | Next.js standalone server |
| MCP server | 8870 | FastMCP with 5 tools |
| Qdrant | 6733 | Vector search (bundled binary) |
| Agent Zero | 50001 | Optional Docker companion |

All data stays on your machine at `~/Library/Application Support/Praxo-PICOS/`.

## Optional: Agent Zero (AI assistant)

For a smarter AI assistant, install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and enable Agent Zero in Settings. The app will manage the Docker container for you.

## Developer Setup (run from source)

```bash
git clone https://github.com/Brianletort/Praxo-PICOS.git
cd Praxo-PICOS
make bootstrap          # Install Python + Node dependencies
make dev-api            # Start API on :8865
make dev-web            # Start web UI on :3100
# Open http://127.0.0.1:3100
```

### Requirements for development

- Python 3.12+
- Node.js 20+
- Docker (optional, for Qdrant and Agent Zero)

### Testing

```bash
make test               # Python + web unit tests
make regression         # Full regression suite
cd apps/desktop && npm test  # Desktop tests
cd apps/web && npm run e2e   # Playwright E2E tests
```

## License

Proprietary. All rights reserved.
