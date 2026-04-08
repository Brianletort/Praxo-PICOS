#!/usr/bin/env bash
set -euo pipefail

echo "=== Assembling Praxo-PICOS all-in-one bundle ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"

mkdir -p "$DIST_DIR"

# 1. Build Python venv with all dependencies
echo "[1/4] Building Python venv..."
rm -rf "$DIST_DIR/venv"
python3 -m venv "$DIST_DIR/venv"
source "$DIST_DIR/venv/bin/activate"
pip install --upgrade pip -q
pip install "$REPO_ROOT" -q
deactivate
echo "  Python venv ready ($(du -sh "$DIST_DIR/venv" | cut -f1))"

# 2. Build Next.js standalone
echo "[2/4] Building Next.js standalone..."
cd "$REPO_ROOT/apps/web"
npm install --ignore-scripts 2>/dev/null || npm install
npm run build
echo "  Next.js standalone ready"

# 3. Verify Qdrant binary
echo "[3/4] Checking Qdrant binary..."
QDRANT_BIN="$REPO_ROOT/apps/desktop/vendor/qdrant"
if [ -f "$QDRANT_BIN" ]; then
  echo "  Qdrant binary found ($(du -sh "$QDRANT_BIN" | cut -f1))"
else
  echo "  WARNING: Qdrant binary not found at $QDRANT_BIN"
  echo "  Download it: curl -sL https://github.com/qdrant/qdrant/releases/latest/download/qdrant-aarch64-apple-darwin.tar.gz | tar xz -C apps/desktop/vendor/"
fi

# 4. Build Electron app
echo "[4/4] Building Electron DMG..."
cd "$REPO_ROOT/apps/desktop"
npm install 2>/dev/null || true
npm run build

echo ""
echo "=== Build complete ==="
ls -lh "$DIST_DIR/desktop/"*.dmg 2>/dev/null || echo "No DMG found"
ls -lh "$DIST_DIR/desktop/"*.zip 2>/dev/null || echo "No ZIP found"
