"""Hotkey parsing, validation, and formatting.

Pure logic, importable on any platform (no pystray/winotify), so it can be
tested off Windows.

Three vocabularies are in play:

  friendly    what the user types             "ctrl+shift+f9"
  canonical   what pynput/GlobalHotKeys want  "<ctrl>+<shift>+<f9>"
  display     what the menu shows             "Ctrl+Shift+F9"

Everything is stored canonical; normalize_hotkey() converts in, format_hotkey()
converts out.
"""

from pynput.keyboard import HotKey

DEFAULT_HOTKEY = "<ctrl>+<shift>+<f9>"

# Offered in the Set Hotkey dialog. Modifier + function key is the safe corner of
# the keyboard on Windows: almost nothing binds these, unlike Ctrl+Shift+<letter>
# which browsers and IDEs have thoroughly colonized.
SUGGESTED_HOTKEYS = [
    "<ctrl>+<shift>+<f9>",
    "<ctrl>+<alt>+<f10>",
    "<ctrl>+<shift>+<f8>",
    "<ctrl>+<alt>+<f11>",
]

# Friendly spellings the user might type for the same key.
_ALIASES = {
    "control": "ctrl",
    "ctl": "ctrl",
    "option": "alt",
    "opt": "alt",
    "win": "cmd",
    "windows": "cmd",
    "super": "cmd",
    "meta": "cmd",
    "return": "enter",
    "escape": "esc",
    "del": "delete",
    "ins": "insert",
    "pgup": "page_up",
    "pgdn": "page_down",
}

_MODIFIERS = frozenset({"ctrl", "alt", "shift", "cmd"})


class HotkeyError(ValueError):
    """A hotkey string is unparseable or not allowed."""


def _split(text: str) -> list[str]:
    """Split a hotkey string into lowercase, unbracketed, alias-resolved parts."""
    parts = []
    for raw in text.split("+"):
        part = raw.strip().lower()
        if part.startswith("<") and part.endswith(">") and len(part) > 2:
            part = part[1:-1].strip()
        if not part:
            raise HotkeyError(f"Invalid hotkey: '{text}'")
        parts.append(_ALIASES.get(part, part))
    if not parts:
        raise HotkeyError(f"Invalid hotkey: '{text}'")
    return parts


def _canonical(parts: list[str]) -> str:
    """Rebuild pynput's canonical form: named keys bracketed, characters bare."""
    return "+".join(p if len(p) == 1 else f"<{p}>" for p in parts)


def normalize_hotkey(text: str) -> str:
    """Convert user input to pynput's canonical form.

    Raises HotkeyError if the combo is not something pynput can parse.
    """
    if not text or not text.strip():
        raise HotkeyError("Enter a key combination, e.g. Ctrl+Shift+F9")

    canonical = _canonical(_split(text))

    # Let pynput itself be the source of truth on what parses - it is what has to
    # register the combo at runtime.
    try:
        HotKey.parse(canonical)
    except ValueError as e:
        raise HotkeyError(f"'{text.strip()}' is not a valid key combination ({e})")

    return canonical


def hotkey_parts(text: str) -> list[str] | None:
    """The lowercase, alias-resolved parts of a hotkey, or None if unparseable.

    For callers (menu labels, warnings, release detection) that must degrade
    rather than raise on a bad config value.
    """
    try:
        parts = _split(text)
        HotKey.parse(_canonical(parts))
    except (HotkeyError, ValueError):
        return None
    return parts


def format_hotkey(canonical: str) -> str:
    """Human-readable form for menus and messages. Never raises."""
    parts = hotkey_parts(canonical)
    if parts is None:
        return canonical
    return "+".join(p.upper() if len(p) == 1 else p.replace("_", " ").title() for p in parts)


# Combos the app refuses to save, mapped to why. These are not merely
# inconvenient - each one breaks the app or the user's system:
#
#   Ctrl+C / Ctrl+X   the app simulates Ctrl+C to grab the selection, so this
#                     both fires on every ordinary copy and lets the app
#                     retrigger itself
#   Ctrl+V            the app simulates Ctrl+V to paste the result - same loop,
#                     at the end of the workflow where the guards are unwinding
#   Ctrl+Alt+Delete   reserved by Windows; the app would never receive it
_BLOCKED = {
    ("ctrl", "c"): "Ctrl+C is the system copy shortcut, and Rephrase uses it "
    "internally to read your selection. Choose another combination.",
    ("ctrl", "x"): "Ctrl+X is the system cut shortcut, and Rephrase uses copy "
    "internally to read your selection. Choose another combination.",
    ("ctrl", "v"): "Ctrl+V is the system paste shortcut, and Rephrase uses it "
    "internally to replace your text. Choose another combination.",
    ("ctrl", "alt", "delete"): "Ctrl+Alt+Delete is reserved by Windows and can "
    "never reach Rephrase. Choose another combination.",
}

# Allowed, but likely to collide with something the user relies on. pynput's hook
# does not swallow the keystroke, so the other app's action fires too.
_WARNINGS = {
    ("ctrl", "shift", "r"): "Ctrl+Shift+R reloads the page in most browsers, "
    "which can discard what you were editing.",
    ("ctrl", "r"): "Ctrl+R reloads the page in most browsers, which can discard "
    "what you were editing.",
    ("ctrl", "z"): "Ctrl+Z is Undo in almost every app.",
    ("ctrl", "y"): "Ctrl+Y is Redo in many apps.",
    ("ctrl", "a"): "Ctrl+A is Select All in almost every app.",
    ("ctrl", "s"): "Ctrl+S is Save in almost every app.",
    ("ctrl", "shift", "n"): "Ctrl+Shift+N opens a new private window in browsers.",
    ("ctrl", "shift", "t"): "Ctrl+Shift+T reopens the last closed tab in browsers.",
    ("ctrl", "shift", "esc"): "Ctrl+Shift+Esc opens Task Manager.",
}

# Trigger keys that are heavily used on their own, whatever modifiers accompany
# them.
_WARN_TRIGGERS = {
    "f5": "F5 refreshes the page in most browsers and file explorers.",
    "f12": "F12 opens developer tools in most browsers.",
    "f1": "F1 opens Help in most apps.",
    "f4": "F4 combinations are used by Windows to close windows.",
}


def warning_for_hotkey(text: str) -> str | None:
    """A caution for an allowed-but-risky combo, or None if it looks clean."""
    parts = hotkey_parts(text)
    if parts is None:
        return None

    key = tuple(sorted(parts[:-1])) + (parts[-1],)
    for combo, message in _WARNINGS.items():
        if tuple(sorted(combo[:-1])) + (combo[-1],) == key:
            return message

    trigger = parts[-1]
    if trigger in _WARN_TRIGGERS:
        return _WARN_TRIGGERS[trigger]

    if "cmd" in parts:
        return (
            "The Windows key is reserved for system shortcuts; combinations "
            "using it may be intercepted by Windows."
        )

    return None


def validate_hotkey(text: str) -> str:
    """Normalize and check a hotkey. Returns the canonical form.

    Raises HotkeyError if unparseable or on the blocklist. Risky-but-allowed
    combos pass - call warning_for_hotkey() to surface those to the user.
    """
    canonical = normalize_hotkey(text)
    parts = _split(canonical)

    modifiers = [p for p in parts if p in _MODIFIERS]
    triggers = [p for p in parts if p not in _MODIFIERS]

    if not triggers:
        raise HotkeyError(
            "A hotkey needs a key besides modifiers, e.g. Ctrl+Shift+F9."
        )
    if len(triggers) > 1:
        raise HotkeyError(
            f"A hotkey can only have one non-modifier key "
            f"(got {', '.join(t.upper() for t in triggers)})."
        )
    if not modifiers:
        raise HotkeyError(
            f"'{format_hotkey(canonical)}' has no modifier key. It would fire "
            f"while you type. Add Ctrl, Alt, or Shift."
        )

    key = tuple(sorted(modifiers)) + (triggers[0],)
    for combo, message in _BLOCKED.items():
        if tuple(sorted(combo[:-1])) + (combo[-1],) == key:
            raise HotkeyError(message)

    return canonical
