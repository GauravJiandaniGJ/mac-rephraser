"""Clipboard operations and paste simulation for macOS."""

import subprocess
import time

import pyperclip

from logger import log


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
    Get currently selected text by simulating Cmd+C.
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

    # Simulate Cmd+C using osascript (more reliable than pynput for this)
    script = '''
    tell application "System Events"
        keystroke "c" using command down
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=2)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log.warning(f"Cmd+C simulation failed: {e}")
        _safe_clipboard_restore(original_clipboard)
        return None

    # Wait for clipboard to update - use retry logic for reliability
    selected_text = ""
    for attempt in range(3):
        time.sleep(0.1)  # 100ms per attempt, up to 300ms total
        try:
            selected_text = pyperclip.paste()
        except Exception:
            selected_text = ""

        # If we got something, break early
        if selected_text:
            break

    # If clipboard is still empty, nothing was selected
    if not selected_text:
        log.debug("No text in clipboard after Cmd+C")
        _safe_clipboard_restore(original_clipboard)
        return None

    # Check for whitespace-only selection
    if not selected_text.strip():
        log.debug("Selection contains only whitespace")
        _safe_clipboard_restore(original_clipboard)
        return None

    return selected_text


def paste_text(text: str) -> bool:
    """
    Replace selected text by copying new text to clipboard and simulating Cmd+V.
    Returns True on success, False on failure.
    """
    # Copy new text to clipboard
    pyperclip.copy(text)
    
    # Simulate Cmd+V using osascript
    script = '''
    tell application "System Events"
        keystroke "v" using command down
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=2)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False
