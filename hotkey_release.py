"""Hotkey-release detection for the Windows app.

Pure logic split out from rephrase_win.py so it is importable and testable on
any platform (rephrase_win.py itself refuses to import off win32 and pulls in
Windows-only deps like pystray/winotify).

The Windows app tracks which keys are currently held and, after the Ctrl+Alt+R
hotkey fires, waits until those keys are released before sending Ctrl+C. Copying
while 'r' is still held would type 'r' into (and overwrite) the selected text.
"""

from pynput import keyboard

# The modifier keys that make up the hotkey. Any of these being held means the
# hotkey has not been fully released yet.
_CTRL_KEYS = frozenset({keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r})
_ALT_KEYS = frozenset(
    {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}
)

# 'r' can surface in a few forms depending on modifier state: a plain 'r', its
# uppercase, or the Ctrl-translated control char '\x12' (Ctrl+R) that Windows
# reports while Ctrl is held.
_R_CHARS = frozenset({"r", "R", "\x12"})

# How long to wait for keys to be released before giving up and copying anyway.
# A backstop for the rare case the OS drops a key-release event, so the app
# never hangs forever.
HOTKEY_RELEASE_TIMEOUT = 5.0


def hotkey_keys_released(pressed: set) -> bool:
    """True when none of Ctrl, Alt, or the 'r' key are currently held.

    `pressed` is the live set of pynput Key/KeyCode values seen as down.
    """
    if pressed & _CTRL_KEYS or pressed & _ALT_KEYS:
        return False
    for key in pressed:
        if getattr(key, "char", None) in _R_CHARS:
            return False
    return True
