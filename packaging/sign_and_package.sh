#!/usr/bin/env bash
set -euo pipefail

echo "=== Signing and packaging Praxo-PICOS ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"

APP_PATH="${APP_PATH:-$DIST_DIR/desktop/mac-arm64/Praxo-PICOS.app}"
PKG_OUT="${PKG_OUT:-$DIST_DIR/Praxo-PICOS.pkg}"
SIGN_ID_APP="${SIGN_ID_APP:-}"
SIGN_ID_INSTALLER="${SIGN_ID_INSTALLER:-}"
ENTITLEMENTS="$SCRIPT_DIR/entitlements.plist"

if [ ! -d "$APP_PATH" ]; then
  echo "ERROR: App bundle not found at $APP_PATH"
  echo "Run packaging/assemble_app.sh first."
  exit 1
fi

if [ -n "$SIGN_ID_APP" ]; then
  echo "Signing app bundle with: $SIGN_ID_APP"

  find "$APP_PATH/Contents" -type f \( -perm -111 -o -name "*.dylib" -o -name "*.so" -o -name "*.node" \) -print0 \
    | while IFS= read -r -d '' f; do
        /usr/bin/codesign --force --timestamp --options runtime \
          --entitlements "$ENTITLEMENTS" \
          --sign "$SIGN_ID_APP" "$f" 2>/dev/null || true
      done

  /usr/bin/codesign --force --timestamp --options runtime \
    --entitlements "$ENTITLEMENTS" \
    --sign "$SIGN_ID_APP" "$APP_PATH"

  echo "Verifying signature..."
  /usr/bin/codesign --verify --deep --strict --verbose=2 "$APP_PATH"
else
  echo "SIGN_ID_APP not set -- skipping code signing (dev build)"
fi

if [ -n "$SIGN_ID_INSTALLER" ]; then
  echo "Building signed installer package..."
  /usr/bin/productbuild \
    --sign "$SIGN_ID_INSTALLER" \
    --component "$APP_PATH" /Applications \
    "$PKG_OUT"
  echo "Installer: $PKG_OUT"
else
  echo "SIGN_ID_INSTALLER not set -- building unsigned package (dev build)"
  /usr/bin/productbuild \
    --component "$APP_PATH" /Applications \
    "$PKG_OUT"
  echo "Unsigned installer: $PKG_OUT"
fi

echo "=== Signing and packaging complete ==="
