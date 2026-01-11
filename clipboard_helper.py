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


def _try_copy_keystroke() -> bool:
    """Try to copy using keystroke simulation. Returns True if command executed."""
    script = '''
    tell application "System Events"
        keystroke "c" using command down
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=2)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        log.debug(f"Keystroke copy failed: {e}")
        return False


def _try_copy_menu() -> bool:
    """Try to copy using Edit menu (more reliable for some apps). Returns True if command executed."""
    script = '''
    tell application "System Events"
        tell (first process whose frontmost is true)
            try
                click menu item "Copy" of menu "Edit" of menu bar 1
                return true
            on error
                return false
            end try
        end tell
    end tell
    '''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=2)
        if result and result.stdout:
            return "true" in result.stdout.lower()
        return False
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, AttributeError) as e:
        log.debug(f"Menu copy failed: {e}")
        return False


def get_selected_text() -> str | None:
    """
    Get currently selected text by simulating Cmd+C.
    Returns the selected text or None if nothing selected.
    Uses multiple methods for reliability across different apps.
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

    # Try keystroke method first (faster)
    log.debug("Attempting copy via keystroke...")
    copy_executed = _try_copy_keystroke()

    # Wait and check clipboard
    selected_text = ""
    for attempt in range(3):
        time.sleep(0.15)  # 150ms per attempt
        try:
            selected_text = pyperclip.paste()
        except Exception:
            selected_text = ""

        if selected_text:
            log.debug(f"Got text on attempt {attempt + 1}")
            break

    # If keystroke didn't work, try menu method as fallback
    if not selected_text:
        log.debug("Keystroke copy got nothing, trying menu method...")
        pyperclip.copy("")  # Clear again
        _try_copy_menu()

        # Wait and check clipboard again
        for attempt in range(3):
            time.sleep(0.15)
            try:
                selected_text = pyperclip.paste()
            except Exception:
                selected_text = ""

            if selected_text:
                log.debug(f"Menu method got text on attempt {attempt + 1}")
                break

    # If clipboard is still empty, nothing was selected
    if not selected_text:
        log.debug("No text in clipboard after all copy methods")
        _safe_clipboard_restore(original_clipboard)
        return None

    # Check for whitespace-only selection
    if not selected_text.strip():
        log.debug("Selection contains only whitespace")
        _safe_clipboard_restore(original_clipboard)
        return None

    log.debug(f"Successfully copied {len(selected_text)} chars")
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
