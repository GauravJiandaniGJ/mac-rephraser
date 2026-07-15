"""Hotkey-release detection for the Windows app.

Pure logic split out from rephrase_win.py so it is importable and testable on
any platform (rephrase_win.py itself refuses to import off win32 and pulls in
Windows-only deps like pystray/winotify).

The Windows app tracks which keys are currently held and, after the hotkey
fires, waits until those keys are released before sending Ctrl+C. A key still
held down when the copy fires types into (and destroys) the selected text.

The keys to wait for come from the user's configured hotkey, so a custom combo
gets the same protection as the default.
"""

from pynput.keyboard import Key, KeyCode

from hotkey_validation import DEFAULT_HOTKEY, hotkey_parts

# Win32 virtual-key codes for the function keys, so a held key reported as a raw
# KeyCode (see _vks) is still recognized. F1 is 0x70 and they run consecutively.
_WIN_FUNCTION_VKS = {f"f{i}": 0x70 + (i - 1) for i in range(1, 13)}

# Left/right variants of each modifier. pynput may report either the generic key
# or a side-specific one, so any variant of a modifier in the combo counts as
# that modifier being held.
_MODIFIER_VARIANTS = {
    Key.ctrl: frozenset({Key.ctrl, Key.ctrl_l, Key.ctrl_r}),
    Key.alt: frozenset({Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr}),
    Key.shift: frozenset({Key.shift, Key.shift_l, Key.shift_r}),
    Key.cmd: frozenset({Key.cmd, Key.cmd_l, Key.cmd_r}),
}

# Every modifier key, in any variant. Used as the safe fallback when the combo
# cannot be parsed: block on any modifier rather than skipping the wait.
_ALL_MODIFIERS = frozenset().union(*_MODIFIER_VARIANTS.values())

# How long to wait for keys to be released before giving up and copying anyway.
# A backstop for the rare case the OS drops a key-release event, so the app
# never hangs forever.
HOTKEY_RELEASE_TIMEOUT = 5.0


def keys_for_hotkey(hotkey: str = DEFAULT_HOTKEY) -> frozenset:
    """The set of keys that must be released before copying, for `hotkey`.

    Expands modifiers to all their left/right variants. Returns every modifier
    key if `hotkey` cannot be parsed, so a bad value degrades to "wait for any
    modifier" rather than "do not wait at all".

    Named keys are resolved via Key[name] rather than HotKey.parse(), because
    parse() resolves function keys to a *host*-platform virtual-key code
    (macOS F9 is vk 101, Windows F9 is vk 0x78). Key.f9 carries whichever is
    right for the machine pynput is running on.
    """
    parts = hotkey_parts(hotkey)
    if parts is None:
        return _ALL_MODIFIERS

    keys = set()
    for part in parts:
        named = getattr(Key, part, None)
        if named is not None:
            keys.update(_MODIFIER_VARIANTS.get(named, {named}))
        elif len(part) == 1:
            keys.add(KeyCode.from_char(part))
        else:
            # Parseable by our validator but not a Key attribute - be safe.
            return _ALL_MODIFIERS
    return frozenset(keys)


def trigger_vks_for_hotkey(hotkey: str = DEFAULT_HOTKEY) -> frozenset:
    """Win32 virtual-key codes for `hotkey`'s non-modifier keys.

    A backstop for identity matching: depending on layout and driver, pynput can
    surface a held key as a bare KeyCode carrying only a vk. A letter pressed
    while Ctrl is down notably arrives that way rather than as a character.
    """
    parts = hotkey_parts(hotkey)
    if parts is None:
        return frozenset()

    vks = set()
    for part in parts:
        if part in _WIN_FUNCTION_VKS:
            vks.add(_WIN_FUNCTION_VKS[part])
        elif len(part) == 1 and part.isalnum():
            # Letters and digits use their uppercase ASCII code as the Win32 vk.
            vks.add(ord(part.upper()))
    return frozenset(vks)


def _vks_of(key) -> set:
    """The virtual-key codes a pressed pynput key may be carrying."""
    vks = set()
    vk = getattr(key, "vk", None)
    if vk is not None:
        vks.add(vk)
    inner = getattr(key, "value", None)  # named Keys wrap a KeyCode in .value
    inner_vk = getattr(inner, "vk", None)
    if inner_vk is not None:
        vks.add(inner_vk)
    char = getattr(key, "char", None)
    if char and len(char) == 1 and char.isalnum():
        vks.add(ord(char.upper()))
    return vks


def hotkey_keys_released(pressed: set, hotkey: str = DEFAULT_HOTKEY) -> bool:
    """True when none of `hotkey`'s keys are currently held.

    `pressed` is the live set of pynput Key/KeyCode values seen as down.
    """
    if pressed & keys_for_hotkey(hotkey):
        return False

    wanted_vks = trigger_vks_for_hotkey(hotkey)
    if wanted_vks:
        for key in pressed:
            if _vks_of(key) & wanted_vks:
                return False
    return True
