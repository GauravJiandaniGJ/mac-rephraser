"""Hotkey-release detection for the Windows app.

Pure logic split out from rephrase_win.py so it is importable and testable on
any platform (rephrase_win.py itself refuses to import off win32 and pulls in
Windows-only deps like pystray/winotify).

The Windows app tracks which keys are currently held and, after the
Ctrl+Shift+F9 hotkey fires, waits until those keys are released before sending
Ctrl+C. Copying while a modifier is still held can interfere with the copy.
"""

from pynput import keyboard

# The modifier keys that make up the hotkey. Any of these being held means the
# hotkey has not been fully released yet.
_CTRL_KEYS = frozenset({keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r})
_SHIFT_KEYS = frozenset(
    {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r}
)

# F9 is a function key, so unlike a letter it never surfaces as a character and
# has no Ctrl-translated control-char form to worry about. It is normally
# reported as the named Key.f9, but on some layouts/drivers pynput surfaces
# function keys as a raw KeyCode carrying the Win32 virtual-key code instead, so
# we also match by vk. F9's Win32 virtual-key code is 0x78 (120).
_F9_KEYS = frozenset({keyboard.Key.f9})
_F9_VK = 0x78

# How long to wait for keys to be released before giving up and copying anyway.
# A backstop for the rare case the OS drops a key-release event, so the app
# never hangs forever.
HOTKEY_RELEASE_TIMEOUT = 5.0


def _is_f9(key) -> bool:
    """True if `key` is F9 in either the named or raw-KeyCode form."""
    if key in _F9_KEYS:
        return True
    # KeyCode instances carry a `vk`; named Keys wrap a KeyCode in `.value`.
    vk = getattr(key, "vk", None)
    if vk is None:
        inner = getattr(key, "value", None)
        vk = getattr(inner, "vk", None)
    return vk == _F9_VK


def hotkey_keys_released(pressed: set) -> bool:
    """True when none of Ctrl, Shift, or F9 are currently held.

    `pressed` is the live set of pynput Key/KeyCode values seen as down.
    """
    if pressed & _CTRL_KEYS or pressed & _SHIFT_KEYS:
        return False
    if any(_is_f9(key) for key in pressed):
        return False
    return True
