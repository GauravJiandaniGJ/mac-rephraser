"""Detect hotkeys already claimed by another Windows application.

Windows lets an app reserve a global hotkey with RegisterHotKey(). If another
process (PowerToys, a clipboard manager, a screenshot tool) owns a combo, that
call fails with ERROR_HOTKEY_ALREADY_REGISTERED. Probing is simply: try to
register, note the result, unregister immediately.

This only sees combos reserved through RegisterHotKey. It cannot see shortcuts
that live *inside* an application (Ctrl+Shift+R reloading a browser page), since
those are handled by the app's own key handling and are not registered with
Windows. Those are covered by the warning list in hotkey_validation instead.

No-ops off Windows so the app and tests import cleanly on macOS.
"""

import sys

from hotkey_validation import hotkey_parts

# Modifier flags for RegisterHotKey (winuser.h).
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
# Do not fire repeatedly while the key is held; irrelevant for a probe, but it
# is what we would want if we ever registered for real.
MOD_NOREPEAT = 0x4000

_MOD_FLAGS = {
    "ctrl": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "cmd": MOD_WIN,
}

# Win32 virtual-key codes for the non-modifier keys a hotkey can use.
_VK_FUNCTION = {f"f{i}": 0x70 + (i - 1) for i in range(1, 13)}
_VK_NAMED = {
    "space": 0x20,
    "enter": 0x0D,
    "tab": 0x09,
    "esc": 0x1B,
    "backspace": 0x08,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "page_up": 0x21,
    "page_down": 0x22,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
}

ERROR_HOTKEY_ALREADY_REGISTERED = 1409

# Arbitrary id for the probe registration; unregistered immediately after.
_PROBE_ID = 0xBEEF


def to_win32(hotkey: str) -> tuple[int, int] | None:
    """Convert a canonical hotkey to (modifier_flags, virtual_key_code).

    Returns None if the combo cannot be expressed for RegisterHotKey.
    """
    parts = hotkey_parts(hotkey)
    if not parts:
        return None

    flags = 0
    vk = None
    for part in parts:
        if part in _MOD_FLAGS:
            flags |= _MOD_FLAGS[part]
        elif part in _VK_FUNCTION:
            vk = _VK_FUNCTION[part]
        elif part in _VK_NAMED:
            vk = _VK_NAMED[part]
        elif len(part) == 1 and part.isalnum():
            vk = ord(part.upper())
        else:
            return None

    if vk is None or flags == 0:
        return None
    return flags, vk


def is_taken_by_another_app(hotkey: str) -> bool:
    """True if another application has globally registered `hotkey`.

    False if the combo is free, if it cannot be probed, or off Windows - a probe
    that cannot run must never block the user from saving.
    """
    if sys.platform != "win32":
        return False

    converted = to_win32(hotkey)
    if converted is None:
        return False
    flags, vk = converted

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.UnregisterHotKey.restype = wintypes.BOOL

    # hwnd=None registers against the calling thread; the probe must therefore
    # run on the thread that will also unregister it, which it does here.
    if user32.RegisterHotKey(None, _PROBE_ID, flags | MOD_NOREPEAT, vk):
        user32.UnregisterHotKey(None, _PROBE_ID)
        return False

    return ctypes.get_last_error() == ERROR_HOTKEY_ALREADY_REGISTERED
