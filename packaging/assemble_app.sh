#!/usr/bin/env bash
set -euo pipefail

echo "=== Assembling Praxo-PICOS app bundle ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"

mkdir -p "$DIST_DIR"

echo "Building frontend..."
cd "$REPO_ROOT/apps/web"
npm ci
npm run build

echo "Building backend venv..."
cd "$REPO_ROOT"
python3 -m venv "$DIST_DIR/venv"
source "$DIST_DIR/venv/bin/activate"
pip install --upgrade pip
pip install .
deactivate

echo "Building Electron app..."
cd "$REPO_ROOT/apps/desktop"
npm ci
npm run build:dir

echo "=== Assembly complete ==="
echo "Output: $DIST_DIR/"
ls -la "$DIST_DIR/"
