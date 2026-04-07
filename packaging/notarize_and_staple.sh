#!/usr/bin/env bash
set -euo pipefail

echo "=== Notarizing and stapling ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"

ARTIFACT="${1:-$DIST_DIR/Praxo-PICOS.pkg}"
KEYCHAIN_PROFILE="${NOTARY_KEYCHAIN_PROFILE:-notarytool-profile}"

if [ ! -f "$ARTIFACT" ]; then
  echo "ERROR: Artifact not found at $ARTIFACT"
  exit 1
fi

echo "Submitting $ARTIFACT for notarization..."
xcrun notarytool submit "$ARTIFACT" \
  --keychain-profile "$KEYCHAIN_PROFILE" \
  --wait

echo "Stapling ticket..."
xcrun stapler staple "$ARTIFACT"

echo "Verifying staple..."
xcrun stapler validate "$ARTIFACT"

echo "=== Notarization complete ==="
