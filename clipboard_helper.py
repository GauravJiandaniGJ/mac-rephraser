"""Clipboard operations and paste simulation for macOS."""

import subprocess
import time

import pyperclip


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
    pyperclip.copy("")
    
    # Simulate Cmd+C using osascript (more reliable than pynput for this)
    script = '''
    tell application "System Events"
        keystroke "c" using command down
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=2)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Restore original clipboard
        if original_clipboard:
            pyperclip.copy(original_clipboard)
        return None
    
    # Small delay for clipboard to update
    time.sleep(0.1)
    
    # Get the copied text
    try:
        selected_text = pyperclip.paste()
    except Exception:
        selected_text = ""
    
    # If clipboard is still empty, nothing was selected
    if not selected_text:
        if original_clipboard:
            pyperclip.copy(original_clipboard)
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
