#!/usr/bin/env bash
set -euo pipefail

echo "=== Importing signing certificates ==="

KEYCHAIN_PASSWORD="${KEYCHAIN_PASSWORD:-$(openssl rand -base64 32)}"
KEYCHAIN_PATH="$RUNNER_TEMP/build.keychain-db"

if [ -z "${MACOS_CERT_P12_BASE64:-}" ]; then
  echo "MACOS_CERT_P12_BASE64 not set -- skipping cert import"
  exit 0
fi

echo "Creating temporary keychain..."
security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"

echo "Importing certificate..."
CERT_PATH="$RUNNER_TEMP/certificate.p12"
echo "$MACOS_CERT_P12_BASE64" | base64 --decode > "$CERT_PATH"

security import "$CERT_PATH" \
  -P "${MACOS_CERT_PASSWORD:-}" \
  -A \
  -t cert \
  -f pkcs12 \
  -k "$KEYCHAIN_PATH"

security list-keychain -d user -s "$KEYCHAIN_PATH"
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"

rm -f "$CERT_PATH"

echo "=== Certificates imported ==="
