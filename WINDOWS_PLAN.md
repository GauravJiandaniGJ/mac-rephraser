# Windows Port — Architecture Plan (not yet implemented)

Windows support is not a packaging-only task: the menubar UI (`rumps`) and all
`osascript` calls (clipboard keystrokes, notifications, dialogs) are Mac-only.
This documents what a port needs so it can be picked up later. Estimated
effort: **2–3 days** including testing.

## What already works on Windows (no changes)

| Module | Why |
|--------|-----|
| `api.py` | Pure OpenAI client code |
| `keychain_helper.py` | `keyring` targets Windows Credential Manager automatically |
| `logger.py` | Already branches per-platform (`%LOCALAPPDATA%\Rephrase\logs`) |
| `pyperclip` | Cross-platform clipboard read/write |
| `pynput` hotkey listener | Works on Windows; Ctrl+Alt+R is a natural mapping |

## What needs replacing

| Mac piece | Windows replacement |
|-----------|---------------------|
| `rumps` menubar (icon, menus, checkmarks) | `pystray` + `Pillow` system-tray icon |
| osascript Cmd+C / Cmd+V simulation | `pynput.keyboard.Controller` sending Ctrl+C / Ctrl+V |
| osascript notifications | `winotify` (or pystray's built-in notify) |
| osascript input dialog (API key) | `tkinter.simpledialog` (stdlib, no new dependency) |
| Edit-menu copy fallback | Drop it — keystroke simulation is the norm on Windows |

Also: `config.py` and `usage_stats.py` hardcode `~/.config/rephrase/` — extract
a `get_config_dir()` helper following the pattern `logger.py` already uses
(`%APPDATA%\Rephrase` on Windows, `~/.config/rephrase` elsewhere).

## Proposed structure — one repo, thin platform layer

```
platform_impl/
├── __init__.py      # selects mac/win by sys.platform
├── base.py          # interface: tray_app, notify, prompt_secret,
│                    #            copy_selection, paste_text
├── mac.py           # current rumps + osascript code moves here
└── win.py           # pystray + pynput Controller + tkinter
```

`rephrase.py` keeps the core workflow (hotkey → copy → API → paste) and calls
through the interface. `api.py`, `config.py`, `usage_stats.py`,
`keychain_helper.py`, `logger.py` stay shared and untouched.

## Windows-specific gotchas to pre-empt

- **Elevated windows**: pynput can't see keystrokes typed into apps running as
  Administrator; the hotkey silently won't fire there. Document it.
- **SmartScreen**: an unsigned `.exe` shows "Windows protected your PC" →
  users click **More info → Run anyway**. Real fix is code signing
  (Azure Trusted Signing ~$10/month is the cheap route in 2026); for internal
  distribution, documenting the bypass is acceptable.
- **Startup at login**: no LaunchAgent equivalent needed — drop a shortcut in
  `shell:startup` or add a registry Run key; make it an installer option.
- **Clipboard timing**: Ctrl+C propagation is slower in some apps (Office);
  keep the existing retry loop from `clipboard_helper.py`.

## Packaging

PyInstaller: `pyinstaller --onefile --noconsole --name Rephrase rephrase.py`
(plus hidden-import flags for `pystray._win32` and keyring's Windows backend).
Build on a Windows machine or VM — PyInstaller does not cross-compile.
