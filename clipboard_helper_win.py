"""Clipboard operations and paste simulation for Windows.

Windows counterpart of clipboard_helper.py: instead of osascript keystrokes,
Ctrl+C / Ctrl+V are sent with pynput's keyboard Controller.
"""

import time

import pyperclip
from pynput.keyboard import Controller, Key

from logger import log

# Created lazily so importing this module has no side effects (keeps tests
# runnable on any platform).
_keyboard: Controller | None = None


def _get_keyboard() -> Controller:
    global _keyboard
    if _keyboard is None:
        _keyboard = Controller()
    return _keyboard


def _send_ctrl_key(char: str) -> None:
    """Send Ctrl+<char> to the frontmost window."""
    kb = _get_keyboard()
    with kb.pressed(Key.ctrl):
        kb.press(char)
        kb.release(char)


def read_clipboard() -> str:
    """Return the current clipboard text, or "" if it can't be read.

    Callers snapshot this before get_selected_text() (which overwrites the
    clipboard while probing the selection) so the original can be restored
    after the rephrase paste.
    """
    try:
        return pyperclip.paste()
    except Exception:
        return ""


def _safe_clipboard_restore(original: str) -> None:
    """Safely restore clipboard content, handling any errors."""
    if not original:
        return
    try:
        pyperclip.copy(original)
    except Exception as e:
        log.warning(f"Failed to restore clipboard: {e}")


def get_selected_text() -> str | None:
    """
    Get currently selected text by simulating Ctrl+C.
    Returns the selected text or None if nothing selected.
    """
    # Store current clipboard content
    try:
        original_clipboard = pyperclip.paste()
    except Exception:
        original_clipboard = ""

    # Clear clipboard first to detect if copy worked
    try:
        pyperclip.copy("")
    except Exception as e:
        log.warning(f"Failed to clear clipboard: {e}")
        return None

    log.debug("Attempting copy via Ctrl+C...")
    try:
        _send_ctrl_key("c")
    except Exception as e:
        log.error(f"Ctrl+C simulation failed: {e}")
        _safe_clipboard_restore(original_clipboard)
        return None

    # Wait and check clipboard (some apps, e.g. Office, are slow to publish)
    selected_text = ""
    for attempt in range(5):
        time.sleep(0.15)
        try:
            selected_text = pyperclip.paste()
        except Exception:
            selected_text = ""

        if selected_text:
            log.debug(f"Got text on attempt {attempt + 1}")
            break

    # If clipboard is still empty, nothing was selected
    if not selected_text:
        log.debug("No text in clipboard after copy")
        _safe_clipboard_restore(original_clipboard)
        return None

    # Check for whitespace-only selection
    if not selected_text.strip():
        log.debug("Selection contains only whitespace")
        _safe_clipboard_restore(original_clipboard)
        return None

    log.debug(f"Successfully copied {len(selected_text)} chars")
    return selected_text


def paste_text(text: str, restore_clipboard: str | None = None) -> bool:
    """
    Replace selected text by copying new text to clipboard and simulating Ctrl+V.
    Returns True on success, False on failure.

    If `restore_clipboard` is given, the user's original clipboard content is put
    back after the paste keystroke lands, so the rephrase flow does not clobber
    whatever the user had copied. Restoration is best-effort and never changes
    the return value.
    """
    pyperclip.copy(text)
    try:
        _send_ctrl_key("v")
    except Exception as e:
        log.error(f"Ctrl+V simulation failed: {e}")
        return False

    if restore_clipboard:
        # Give the target app a moment to consume the Ctrl+V before we swap the
        # clipboard back, otherwise it could paste the restored (original)
        # content instead of the rephrased text.
        time.sleep(0.25)
        _safe_clipboard_restore(restore_clipboard)
    return True
