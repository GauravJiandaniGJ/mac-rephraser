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
# Output: dist/Rephrase-<version>.dmg

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

# --- Ad-hoc sign (Apple Silicon requires a signature; see PACKAGING.md for
# --- the Developer ID + notarization upgrade) ---------------------------------
echo "==> Signing (ad-hoc)"
codesign --force --deep --sign - dist/Rephrase.app
codesign --verify --deep dist/Rephrase.app

# --- Package as .dmg -----------------------------------------------------------
DMG="dist/Rephrase-${VERSION}.dmg"
echo "==> Creating $DMG"
hdiutil create -volname "Rephrase" -srcfolder dist/Rephrase.app -ov -format UDZO "$DMG"

echo ""
echo "Done: $DMG"
echo "Share that file with users. Install steps for them: INSTALL.md"
