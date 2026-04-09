#!/usr/bin/env bash
set -euo pipefail

# Praxo-PICOS Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/Brianletort/Praxo-PICOS/v0.3.4/scripts/install.sh | bash

INSTALL_DIR="${PICOS_INSTALL_DIR:-$HOME/Applications/Praxo-PICOS}"
REPO_URL="${PICOS_REPO_URL:-https://github.com/Brianletort/Praxo-PICOS.git}"
PICOS_GIT_REF="${PICOS_GIT_REF:-v0.3.4}"
QDRANT_VERSION="v1.17.1"
QDRANT_URL="https://github.com/qdrant/qdrant/releases/download/${QDRANT_VERSION}/qdrant-aarch64-apple-darwin.tar.gz"

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║        Praxo-PICOS Installer         ║"
echo "  ║   Personal Intelligence OS for Mac   ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# --- Check prerequisites ---

check_command() {
  command -v "$1" &>/dev/null
}

checkout_release_ref() {
  git fetch --tags origin
  git checkout "$PICOS_GIT_REF"
  if git show-ref --verify --quiet "refs/remotes/origin/$PICOS_GIT_REF"; then
    git pull --ff-only origin "$PICOS_GIT_REF"
  fi
}

install_homebrew() {
  echo "→ Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || true)"
}

PYTHON=""
for cmd in python3.14 python3.13 python3.12 python3; do
  if check_command "$cmd"; then
    ver=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
    major=$(echo "$ver" | cut -d. -f1)
    minor=$(echo "$ver" | cut -d. -f2)
    if [ "$major" -ge 3 ] && [ "$minor" -ge 12 ]; then
      PYTHON="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "⚠  Python 3.12+ not found."
  if check_command brew; then
    echo "→ Installing Python 3.14 via Homebrew..."
    brew install python@3.14
    PYTHON="python3.14"
  else
    install_homebrew
    brew install python@3.14
    PYTHON="python3.14"
  fi
fi
echo "✓  Python: $($PYTHON --version)"

if ! check_command node; then
  echo "⚠  Node.js not found."
  if check_command brew; then
    echo "→ Installing Node 20 via Homebrew..."
    brew install node@20
  else
    install_homebrew
    brew install node@20
  fi
fi
echo "✓  Node: $(node --version)"
echo "✓  npm: $(npm --version)"

if ! check_command git; then
  echo "⚠  Git not found."
  xcode-select --install 2>/dev/null || true
  echo "   Please install Xcode Command Line Tools and re-run."
  exit 1
fi
echo "✓  Git: $(git --version | head -1)"

# --- Clone or update ---

if [ -d "$INSTALL_DIR/.git" ]; then
  echo ""
  echo "→ Updating existing installation at $INSTALL_DIR..."
  cd "$INSTALL_DIR"
  checkout_release_ref
else
  echo ""
  echo "→ Cloning Praxo-PICOS $PICOS_GIT_REF to $INSTALL_DIR..."
  mkdir -p "$(dirname "$INSTALL_DIR")"
  git clone "$REPO_URL" "$INSTALL_DIR"
  cd "$INSTALL_DIR"
  checkout_release_ref
fi

# --- Python environment ---

echo ""
echo "→ Setting up Python environment..."
if [ ! -d ".venv" ]; then
  $PYTHON -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip -q
pip install -e ".[dev]" -q
echo "✓  Python dependencies installed"

# --- Node dependencies ---

echo ""
echo "→ Installing web dashboard dependencies..."
cd apps/web
npm install --ignore-scripts 2>/dev/null || npm install
cd "$INSTALL_DIR"
echo "✓  Web dependencies installed"

# --- Qdrant ---

echo ""
echo "→ Setting up Qdrant vector database..."
QDRANT_BIN="$INSTALL_DIR/apps/desktop/vendor/qdrant"
if [ ! -f "$QDRANT_BIN" ]; then
  mkdir -p "$(dirname "$QDRANT_BIN")"
  echo "   Downloading Qdrant ${QDRANT_VERSION}..."
  curl -sL "$QDRANT_URL" | tar xz -C "$(dirname "$QDRANT_BIN")"
  chmod +x "$QDRANT_BIN"
fi
echo "✓  Qdrant ready"

# --- Create launch command ---

LAUNCH_SCRIPT="$INSTALL_DIR/scripts/picos"
chmod +x "$LAUNCH_SCRIPT" 2>/dev/null || true

# --- Add to PATH ---

SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
  SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
  SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
  if ! grep -q "Praxo-PICOS" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Praxo-PICOS" >> "$SHELL_RC"
    echo "export PATH=\"$INSTALL_DIR/scripts:\$PATH\"" >> "$SHELL_RC"
    echo "✓  Added 'picos' command to PATH (restart your terminal or run: source $SHELL_RC)"
  fi
fi

# --- Done ---

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║       Installation Complete!         ║"
echo "  ╚══════════════════════════════════════╝"
echo ""
echo "  To start Praxo-PICOS:"
echo ""
echo "    $LAUNCH_SCRIPT"
echo ""
echo "  Or if you've restarted your terminal:"
echo ""
echo "    picos"
echo ""
echo "  Then open: http://127.0.0.1:3100"
echo ""
