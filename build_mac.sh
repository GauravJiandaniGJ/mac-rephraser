#!/bin/bash
# Build Rephrase.app and a distributable .dmg.
#
# Uses fully-qualified interpreter paths throughout so the build never
# depends on shell state (pyenv shims, already-activated venvs) - the root
# cause of the broken manual installs this packaging effort replaces.
#
# Usage:
#   ./build_mac.sh
#   REPHRASE_PYTHON=/path/to/python3 ./build_mac.sh   # override interpreter
#
# Signing (defaults to ad-hoc so colleague builds need no secrets):
#   REPHRASE_SIGN_IDENTITY="Developer ID Application: Name (TEAMID)" \
#   REPHRASE_NOTARY_PROFILE=rephrase-notary \
#   ./build_mac.sh
#
# One-time setup for the signed path is documented in PACKAGING.md.
#
# Output: dist/Rephrase-<version>.dmg (notarized + stapled when the
# signing env vars are set)

set -euo pipefail

cd "$(dirname "$0")"

# --- Locate a Python >= 3.10 (never trust the shell's python3) ---------------
PYTHON="${REPHRASE_PYTHON:-$HOME/.pyenv/versions/3.11.9/bin/python3}"
if [ ! -x "$PYTHON" ]; then
    PYTHON="$(command -v python3 || true)"
fi
if [ -z "$PYTHON" ] || ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    echo "ERROR: Python >= 3.10 required. Set REPHRASE_PYTHON=/path/to/python3" >&2
    exit 1
fi
echo "==> Using Python: $PYTHON ($("$PYTHON" --version 2>&1))"

VERSION="$("$PYTHON" -c 'from version import __version__; print(__version__)')"
echo "==> Building Rephrase v$VERSION"

# --- Fresh, isolated build environment ---------------------------------------
rm -rf build dist build-venv
"$PYTHON" -m venv build-venv
build-venv/bin/pip install --quiet --upgrade pip
build-venv/bin/pip install --quiet -r requirements.txt py2app pytest

# --- Tests must pass before building (CLAUDE.md rule) -------------------------
echo "==> Running tests"
build-venv/bin/python -m pytest tests/ -v

# --- Build the .app ------------------------------------------------------------
echo "==> Running py2app"
build-venv/bin/python setup.py py2app

# --- Sign ----------------------------------------------------------------------
# Developer ID + hardened runtime when REPHRASE_SIGN_IDENTITY is set,
# otherwise ad-hoc (Apple Silicon requires *a* signature to launch at all).
SIGN_IDENTITY="${REPHRASE_SIGN_IDENTITY:-}"
if [ -n "$SIGN_IDENTITY" ]; then
    echo "==> Signing with Developer ID: $SIGN_IDENTITY"
    codesign --force --deep --options runtime \
        --entitlements entitlements.plist \
        --sign "$SIGN_IDENTITY" dist/Rephrase.app
else
    echo "==> Signing (ad-hoc - set REPHRASE_SIGN_IDENTITY for a release build)"
    codesign --force --deep --sign - dist/Rephrase.app
fi
codesign --verify --deep --strict dist/Rephrase.app

# --- Package as .dmg -----------------------------------------------------------
DMG="dist/Rephrase-${VERSION}.dmg"
echo "==> Creating $DMG"
hdiutil create -volname "Rephrase" -srcfolder dist/Rephrase.app -ov -format UDZO "$DMG"

# --- Notarize + staple (release builds only) -----------------------------------
NOTARY_PROFILE="${REPHRASE_NOTARY_PROFILE:-}"
if [ -n "$NOTARY_PROFILE" ]; then
    if [ -z "$SIGN_IDENTITY" ]; then
        echo "ERROR: REPHRASE_NOTARY_PROFILE requires REPHRASE_SIGN_IDENTITY (ad-hoc builds cannot be notarized)" >&2
        exit 1
    fi
    echo "==> Notarizing (profile: $NOTARY_PROFILE)"
    xcrun notarytool submit "$DMG" --keychain-profile "$NOTARY_PROFILE" --wait
    echo "==> Stapling notarization ticket"
    xcrun stapler staple "$DMG"
    xcrun stapler validate "$DMG"
fi

echo ""
echo "Done: $DMG"
if [ -n "$NOTARY_PROFILE" ]; then
    echo "Notarized + stapled - users can double-click to install."
else
    echo "Unsigned-for-distribution build: users need the 'Open Anyway' step (INSTALL.md)."
fi
echo "Share that file with users. Install steps for them: INSTALL.md"
