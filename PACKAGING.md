# Packaging & Release Guide (maintainers)

How to build and distribute the Rephrase `.app` / `.dmg`. End-user install steps live in [INSTALL.md](INSTALL.md).

## Cutting a release

1. Bump `__version__` in `version.py`.
2. Run the build (creates an isolated venv, runs the test suite, builds, signs, makes the dmg):
   ```bash
   # Public release: Developer ID + notarization (one-time setup below)
   REPHRASE_SIGN_IDENTITY="Developer ID Application: <Name> (<TEAMID>)" \
   REPHRASE_NOTARY_PROFILE=rephrase-notary \
   ./build_mac.sh

   # Quick internal/colleague build (ad-hoc signature, "Open Anyway" needed)
   ./build_mac.sh
   ```
3. Smoke-test `dist/Rephrase.app` locally: **quit any running dev instance first** (two instances fight over the hotkey), open the app, grant permissions, run "Test Rephrase" from the menu, then a real ⌃⌥R rephrase.
4. Publish: `gh release create v<version> dist/Rephrase-<version>.dmg` (or share via Slack/Drive along with a link to INSTALL.md).

The build never depends on shell state: `build_mac.sh` resolves a fully-qualified Python ≥ 3.10 (default `~/.pyenv/versions/3.11.9/bin/python3`, override with `REPHRASE_PYTHON=`) and builds in a throwaway `build-venv/`. This is deliberate — pyenv shims and stale activated venvs caused the original broken installs.

## How the bundle avoids past problems

| Past problem | Fix in the bundle |
|--------------|-------------------|
| System Python 3.9 can't parse `str \| None` | py2app embeds a full Python 3.11 runtime in the .app |
| pyenv shims / wrong venv | End users have no Python involvement at all |
| Permissions granted to Terminal, lost on reinstall | Stable `CFBundleIdentifier` (`com.gauravjiandani.rephrase`) so TCC grants stick to the app |
| osascript failing silently in a bundle | `NSAppleEventsUsageDescription` in Info.plist triggers a proper Automation prompt |
| keyring backend discovery failing when frozen | `keychain_helper.py` pins the macOS backend when `sys.frozen` is set |

## Known limitations (ad-hoc builds only)

- **Ad-hoc signature changes on every rebuild** → after installing an update, users may need to re-grant Accessibility / Input Monitoring. Goes away with Developer ID signing (below).
- **"Open Anyway" dance on first install** (macOS 15+ removed the right-click → Open bypass). Also goes away with signing + notarization.
- **arm64 only** when built on Apple Silicon. Intel Macs need a separate build on an Intel machine or a `universal2` toolchain — revisit only if someone actually has an Intel Mac.
- The packaged app shares `~/.config/rephrase/` and the Keychain entry (`rephrase-app`) with a dev checkout — settings carry over automatically.

## Signing + notarization (public releases)

This is **not** App Store submission. "Developer ID" distribution is Apple's track for apps distributed directly (DMG downloads); notarization is an automated malware scan (~minutes), no human review, no store listing. (App Store submission is off the table anyway: the sandbox it requires blocks the System Events keystroke simulation this app is built on — see the WhisperPad 2.4.5 rejection, April 2026.)

One-time setup:
1. Join the Apple Developer Program ($99/yr) if not already enrolled.
2. In the developer portal (or Xcode → Settings → Accounts → Manage Certificates), create a **Developer ID Application** certificate and install it in your Keychain. Verify with `security find-identity -v -p codesigning` — a "Developer ID Application: …" entry must appear (an "Apple Development: …" cert is not sufficient for distribution).
3. Create an app-specific password at appleid.apple.com, then store notarization credentials once:
   ```bash
   xcrun notarytool store-credentials rephrase-notary \
     --apple-id <apple-id-email> --team-id <TEAMID> --password <app-specific-password>
   ```

Per release, no script edits needed — pass the identity and profile as env vars:
```bash
REPHRASE_SIGN_IDENTITY="Developer ID Application: <Name> (<TEAMID>)" \
REPHRASE_NOTARY_PROFILE=rephrase-notary \
./build_mac.sh
```
The script signs with hardened runtime + `entitlements.plist` (the unsigned-executable-memory / library-validation exceptions an embedded CPython needs), notarizes the dmg, and staples the ticket.

After this: users just double-click to install (no "Open Anyway"), and permission grants persist across updates because the signature is stable.

## Windows

Not built yet — see [WINDOWS_PLAN.md](WINDOWS_PLAN.md) for the architecture and effort estimate.
