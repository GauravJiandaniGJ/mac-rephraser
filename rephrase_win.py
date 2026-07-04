#!/usr/bin/env python3
"""
Rephrase - Windows system tray app.

Windows counterpart of rephrase.py (macOS/rumps). Same workflow:
select text anywhere, press Ctrl+Alt+R, the selection is replaced with a
rephrased version.

Run from source:  python rephrase_win.py
Build an exe:     build_windows.bat (see WINDOWS_INSTALL.md for user steps)
"""

import os
import sys
import threading
import time

if sys.platform != "win32":
    raise SystemExit("rephrase_win.py is the Windows entry point - on macOS run rephrase.py")

import pystray
from PIL import Image, ImageDraw, ImageFont
from pynput import keyboard
from winotify import Notification

from api import rephrase_text, RephraseError
from clipboard_helper_win import get_selected_text, paste_text
from config import (
    MODELS,
    TONES,
    SENIORITY_LEVELS,
    get_model,
    get_tone,
    get_seniority,
    set_model,
    set_tone,
    set_seniority,
)
from keychain_helper import get_api_key, set_api_key
from logger import log, LOG_DIR
from usage_stats import get_stats_summary, record_rephrase
from version import __version__

APP_NAME = "Rephrase"


def notify(title: str, message: str = ""):
    """Send a Windows toast notification."""
    log.debug(f"Notification: {title} - {message}")
    try:
        Notification(app_id=APP_NAME, title=title, msg=message or " ").show()
    except Exception as e:
        log.error(f"Notification failed: {e}")


def _topmost_tk_root():
    """Create a hidden, topmost Tk root for dialogs shown from tray callbacks."""
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root


def ask_api_key() -> str | None:
    """Show a masked input dialog for the OpenAI API key."""
    from tkinter import simpledialog

    root = _topmost_tk_root()
    try:
        return simpledialog.askstring(
            f"{APP_NAME} - API Key",
            "Enter your OpenAI API key:",
            show="*",
            parent=root,
        )
    finally:
        root.destroy()


def show_welcome():
    """Show the first-run welcome dialog."""
    from tkinter import messagebox

    root = _topmost_tk_root()
    try:
        messagebox.showinfo(
            f"{APP_NAME} Setup",
            "Welcome to Rephrase!\n\n"
            "One step to finish setup: enter your OpenAI API key in the "
            "next dialog (stored securely in Windows Credential Manager).\n\n"
            "Then select text anywhere and press Ctrl+Alt+R to rephrase it.",
            parent=root,
        )
    finally:
        root.destroy()


def make_icon_image() -> Image.Image:
    """Draw the tray icon: an 'R' on a dark rounded square."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((2, 2, 62, 62), radius=14, fill=(45, 45, 48, 255))
    try:
        font = ImageFont.truetype("arialbd.ttf", 44)
    except OSError:
        font = ImageFont.load_default()
    draw.text((32, 30), "R", fill=(255, 255, 255, 255), font=font, anchor="mm")
    return img


class RephraseWinApp:
    def __init__(self):
        log.info("Starting Rephrase app (Windows)...")
        self.is_processing = False
        self.status = "Ready"
        self.hotkeys = None
        self.icon = pystray.Icon(
            APP_NAME, make_icon_image(), APP_NAME, menu=self._build_menu()
        )

    # --- Menu ---------------------------------------------------------------

    def _build_menu(self) -> pystray.Menu:
        Item = pystray.MenuItem

        def radio_items(options: dict, getter, setter, name_of):
            return pystray.Menu(
                *[
                    Item(
                        name_of(key, value),
                        lambda icon, item, k=key: self._select(setter, k),
                        checked=lambda item, k=key: getter() == k,
                        radio=True,
                    )
                    for key, value in options.items()
                ]
            )

        return pystray.Menu(
            Item(lambda item: f"Status: {self.status}", None, enabled=False),
            Item(lambda item: self._get_usage_text(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            Item("Model", radio_items(MODELS, get_model, set_model, lambda k, v: v)),
            Item(
                "Default Tone",
                radio_items(TONES, get_tone, set_tone, lambda k, v: v["name"]),
            ),
            Item(
                "Seniority",
                radio_items(
                    SENIORITY_LEVELS, get_seniority, set_seniority, lambda k, v: v["name"]
                ),
            ),
            pystray.Menu.SEPARATOR,
            Item(
                lambda item: "API Key: ✓ Set" if get_api_key() else "API Key: ✗ Not set",
                None,
                enabled=False,
            ),
            Item("Set API Key...", self.prompt_api_key),
            pystray.Menu.SEPARATOR,
            Item("Test Rephrase", self.test_rephrase),
            Item("Open Logs Folder", self.open_logs),
            Item("Hotkey: Ctrl+Alt+R", None, enabled=False),
            Item(f"Rephrase v{__version__}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            Item("Quit", self.quit_app),
        )

    def _get_usage_text(self) -> str:
        stats = get_stats_summary()
        return f"Today: {stats['today']} | 30 days: {stats['total_30_days']}"

    def _select(self, setter, key: str):
        log.info(f"Setting changed via menu: {setter.__name__}({key})")
        setter(key)
        self.icon.update_menu()

    def _set_status(self, status: str):
        self.status = status
        self.icon.update_menu()

    # --- Menu actions ---------------------------------------------------------

    def prompt_api_key(self, icon=None, item=None):
        log.debug("Prompting for API key...")
        api_key = ask_api_key()
        if api_key and api_key.strip():
            set_api_key(api_key.strip())
            log.info("API key saved successfully")
            notify(APP_NAME, "API key saved securely")
            self.icon.update_menu()
        else:
            log.debug("API key prompt cancelled")

    def test_rephrase(self, icon=None, item=None):
        test_text = "i want to check if this is working properly or not"
        log.info(f"Running test rephrase with: {test_text}")
        notify(APP_NAME, "Testing with sample text...")

        def run_test():
            try:
                result = rephrase_text(test_text)
                log.info(f"Test result: {result}")
                notify("Test Success ✓", result[:100])
            except RephraseError as e:
                log.error(f"Test failed: {e}")
                notify("Test Failed ✗", str(e))

        threading.Thread(target=run_test, daemon=True).start()

    def open_logs(self, icon=None, item=None):
        os.startfile(str(LOG_DIR))

    def quit_app(self, icon=None, item=None):
        log.info("Quitting app...")
        if self.hotkeys:
            self.hotkeys.stop()
        self.icon.stop()

    # --- Hotkey + workflow ------------------------------------------------------

    def start_hotkey_listener(self):
        """Register the global Ctrl+Alt+R hotkey."""
        DEBOUNCE_SECONDS = 1.0
        last_triggered = [0.0]

        def on_hotkey():
            current_time = time.time()
            if current_time - last_triggered[0] < DEBOUNCE_SECONDS:
                log.debug("Hotkey debounced")
                return
            last_triggered[0] = current_time
            log.info("Hotkey Ctrl+Alt+R detected!")

            if self.is_processing:
                log.debug("Already processing, ignoring hotkey")
                return

            def run():
                # Let the user release the hotkey before we send Ctrl+C
                time.sleep(0.3)
                self.do_rephrase()

            threading.Thread(target=run, daemon=True).start()

        # GlobalHotKeys handles the Ctrl-held char translation quirks on
        # Windows (Ctrl+R arrives as '\x12', not 'r') that a raw Listener
        # like the Mac version uses would misread.
        self.hotkeys = keyboard.GlobalHotKeys({"<ctrl>+<alt>+r": on_hotkey})
        self.hotkeys.start()
        log.debug("Hotkey listener started")

    def check_first_run(self):
        """On first launch (no API key stored yet), walk the user through setup."""
        if get_api_key():
            return

        def run_onboarding():
            # Let the tray icon appear before showing dialogs
            time.sleep(1.0)
            log.info("First run: no API key set, showing onboarding")
            try:
                show_welcome()
            except Exception as e:
                log.warning(f"Onboarding welcome dialog failed: {e}")
            self.prompt_api_key()

        threading.Thread(target=run_onboarding, daemon=True).start()

    def do_rephrase(self):
        """Main rephrase workflow."""
        if self.is_processing:
            return

        self.is_processing = True
        self._set_status("Working...")
        log.info("Starting rephrase workflow...")

        try:
            log.debug("Getting selected text...")
            selected_text = get_selected_text()

            if not selected_text:
                log.warning("No text selected")
                notify(APP_NAME, "No text selected")
                return

            log.info(f"Selected text ({len(selected_text)} chars): {selected_text[:50]}...")

            log.debug("Calling OpenAI API...")
            notify(APP_NAME, "Rephrasing...")
            rephrased = rephrase_text(selected_text)
            log.info(f"Rephrased ({len(rephrased)} chars): {rephrased[:50]}...")

            log.debug("Pasting result...")
            if paste_text(rephrased):
                log.info("Text replaced successfully")
                record_rephrase()
                notify("Rephrase ✓", "Text replaced!")
            else:
                log.warning("Paste failed, text is in clipboard")
                notify(APP_NAME, "Couldn't paste. Text copied to clipboard.")

        except RephraseError as e:
            log.error(f"Rephrase error: {e}")
            notify("Rephrase ✗", str(e))

        except Exception as e:
            log.exception(f"Unexpected error: {e}")
            notify("Rephrase ✗", f"Error: {str(e)[:50]}")

        finally:
            self.is_processing = False
            self._set_status("Ready")
            log.debug("Rephrase workflow completed")

    # --- Entry point ------------------------------------------------------------

    def run(self):
        self.start_hotkey_listener()
        self.check_first_run()
        log.info("App initialized. Hotkey: Ctrl+Alt+R")
        self.icon.run()


if __name__ == "__main__":
    app = RephraseWinApp()
    app.run()
