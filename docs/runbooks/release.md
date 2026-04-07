# Release Process

## Prerequisites

- Apple Developer Program membership
- Developer ID Application certificate
- Developer ID Installer certificate
- Notarization credentials stored in Keychain profile

## Local release build

```bash
# 1. Assemble
bash packaging/assemble_app.sh

# 2. Sign (set env vars first)
export SIGN_ID_APP="Developer ID Application: YOUR NAME (TEAMID)"
export SIGN_ID_INSTALLER="Developer ID Installer: YOUR NAME (TEAMID)"
bash packaging/sign_and_package.sh

# 3. Notarize
bash packaging/notarize_and_staple.sh dist/Praxo-PICOS.pkg
```

## CI release (GitHub Actions)

Push a version tag to trigger the release workflow:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Required GitHub secrets:
- `MACOS_CERT_P12_BASE64` - Base64-encoded .p12 certificate
- `MACOS_CERT_PASSWORD` - Certificate password
- `SIGN_ID_APP` - Developer ID Application identity
- `SIGN_ID_INSTALLER` - Developer ID Installer identity
- `NOTARY_KEYCHAIN_PROFILE` - Keychain profile name for notarytool

## QA checklist

- [ ] Install via PKG on macOS Tahoe
- [ ] Install via PKG on macOS Sequoia
- [ ] Install via PKG on macOS Sonoma
- [ ] Gatekeeper allows launch without warning
- [ ] All services start on first launch
- [ ] Onboarding wizard completes
- [ ] Health center shows all green
- [ ] Search returns results
