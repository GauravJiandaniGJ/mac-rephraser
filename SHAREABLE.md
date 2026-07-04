# Sharing Rephrase with a colleague (macOS)

The one-page routine for giving Rephrase to any Mac colleague.

## What to send

Send the **`.dmg`**, never the bare `Rephrase.app`. A `.app` is secretly a
folder — sending it through Slack/Drive/AirDrop unzipped strips executable
permissions and symlinks and the app arrives broken. The dmg is a single file
that preserves everything.

1. Grab `dist/Rephrase-<version>.dmg` (or rebuild it with `./build_mac.sh`).
2. Send it together with a link to [INSTALL.md](INSTALL.md).

That's all a colleague needs — no Terminal, no Python, no git.

## What they do (summary of INSTALL.md)

1. Open the dmg, drag **Rephrase** to Applications.
2. First launch: System Settings → Privacy & Security → **"Open Anyway"**
   (one-time, until the app is notarized).
3. Grant **Accessibility** and **Input Monitoring** to Rephrase.
4. Paste their OpenAI API key into the first-run dialog.
5. Select text anywhere → **Ctrl + Option + R**.

## Caveats

- **Keep the dmg somewhere handy** (pinned Slack message, Drive folder) —
  `dist/` is a build artifact and is not in git.
- **Apple Silicon only.** The build is arm64; it won't run on an old Intel
  Mac.
- **After app updates**, colleagues may need to re-grant the two permissions
  (ad-hoc signature changes per build). This and the "Open Anyway" step both
  disappear once Developer ID signing is set up — see
  [PACKAGING.md](PACKAGING.md).

## Cutting a new version

```bash
# in a checkout of the packaging branch
vim version.py        # bump __version__
./build_mac.sh        # tests → build → sign → dist/Rephrase-<version>.dmg
```
