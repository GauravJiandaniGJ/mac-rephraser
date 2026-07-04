# How to generate `Rephrase-x.y.z.exe` (Windows build)

Two ways to get the exe. **Option A needs no Windows machine and no setup** —
prefer it. Option B is the manual fallback.

## Option A — Let GitHub build it (recommended)

Every push to the `windows` branch automatically builds the exe on a real
Windows machine via GitHub Actions (`.github/workflows/build-windows.yml`).
The run also executes the full test suite on Windows first.

1. Open the repo on GitHub → **Actions** tab → **Build Windows exe**.
2. Click the latest green run (or press **Run workflow** to trigger a fresh
   one from the `windows` branch).
3. Scroll to **Artifacts** at the bottom of the run page and download
   **Rephrase-windows** (a zip containing `Rephrase-x.y.z.exe`).
4. Unzip and share the exe together with `WINDOWS_INSTALL.md`.

Notes:
- Artifacts expire after ~90 days — re-run the workflow anytime to rebuild.
- To release a new version: bump `__version__` in `version.py`, commit, push
  to the `windows` branch, download the new artifact.

## Option B — Build manually on a Windows machine

Requirements: any Windows 10/11 machine, [Python 3.10+](https://www.python.org/downloads/)
(tick **"Add python.exe to PATH"** in the installer), and
[Git](https://git-scm.com/download/win).

```bat
git clone https://github.com/GauravJiandaniGJ/mac-rephraser.git
cd mac-rephraser
git checkout windows
build_windows.bat
```

The script is fully self-contained: it creates an isolated venv
(`build-venv\`), installs dependencies, **runs the test suite** (build aborts
if any test fails), runs PyInstaller, and produces:

```
dist\Rephrase-x.y.z.exe
```

If it fails, the error is printed above the `BUILD FAILED` line — send that
output to the maintainer.

## After building (either option): smoke test before sharing

The exe must be smoke-tested once on a real Windows session (CI builds it but
cannot click the tray icon):

1. Double-click the exe → SmartScreen → **More info → Run anyway**.
2. The **R** tray icon appears (check the ^ overflow area).
3. First-run dialog asks for an OpenAI API key → paste one → OK.
4. Right-click tray icon → **Test Rephrase** → a toast with rephrased text
   should appear.
5. Select text in Notepad → **Ctrl+Alt+R** → text gets replaced.
6. Check the menu items: switching Model/Tone/Seniority shows a moving
   check mark.

All good? Share the exe + `WINDOWS_INSTALL.md` with colleagues (pin in Slack
or Drive — build artifacts are not stored in git).

## What NOT to do

- Don't build on macOS/Linux — PyInstaller cannot cross-compile.
- Don't commit `dist\`, `build\`, or `build-venv\` (they're gitignored).
- Don't rename the exe to something without a version — colleagues end up
  with mystery builds.
- Don't share the exe before the smoke test above has passed once.
