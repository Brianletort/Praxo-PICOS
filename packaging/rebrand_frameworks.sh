#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_PATH="${APP_PATH:-$REPO_ROOT/dist/desktop/mac-arm64/Praxo-PICOS.app}"

if [ ! -d "$APP_PATH" ]; then
  echo "ERROR: App bundle not found at $APP_PATH"
  exit 1
fi

SQUIRREL_PLIST="$APP_PATH/Contents/Frameworks/Squirrel.framework/Versions/A/Resources/Info.plist"

if [ -f "$SQUIRREL_PLIST" ]; then
  echo "Rebranding Squirrel.framework to Praxo-PICOS identity..."
  defaults write "$SQUIRREL_PLIST" CFBundleName "Praxo-PICOS Updater"
  defaults write "$SQUIRREL_PLIST" CFBundleIdentifier "com.praxo.picos.updater"
  defaults write "$SQUIRREL_PLIST" NSHumanReadableCopyright "Copyright © 2026 Praxo"
  plutil -convert xml1 "$SQUIRREL_PLIST"
fi

echo "Re-signing app bundle..."
codesign --force --deep --sign - "$APP_PATH"

echo "Verifying signature..."
codesign --verify --deep --strict "$APP_PATH"

echo "Framework rebrand complete."
