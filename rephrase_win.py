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
from clipboard_helper_win import get_selected_text, paste_text, read_clipboard
from hotkey_release import HOTKEY_RELEASE_TIMEOUT, hotkey_keys_released
from config import (
    MODELS,
    TONES,
    SENIORITY_LEVELS,
    get_hotkey,
    get_model,
    get_tone,
    get_seniority,
    reset_hotkey,
    set_hotkey,
    set_model,
    set_tone,
    set_seniority,
)
from hotkey_conflict import is_taken_by_another_app
from hotkey_validation import (
    SUGGESTED_HOTKEYS,
    HotkeyError,
    format_hotkey,
    validate_hotkey,
    warning_for_hotkey,
)
from keychain_helper import CredentialStoreError, get_api_key, set_api_key
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


def show_welcome(hotkey: str):
    """Show the first-run welcome dialog."""
    from tkinter import messagebox

    root = _topmost_tk_root()
    try:
        messagebox.showinfo(
            f"{APP_NAME} Setup",
            "Welcome to Rephrase!\n\n"
            "One step to finish setup: enter your OpenAI API key in the "
            "next dialog (stored securely in Windows Credential Manager).\n\n"
            f"Then select text anywhere and press {format_hotkey(hotkey)} to "
            "rephrase it.\n\n"
            "You can change that shortcut anytime from the tray icon menu "
            "(Set Hotkey...).",
            parent=root,
        )
    finally:
        root.destroy()


def ask_hotkey(current: str) -> str | None:
    """Prompt for a new hotkey. Returns the raw string, or None if cancelled."""
    from tkinter import simpledialog

    suggestions = ", ".join(format_hotkey(h) for h in SUGGESTED_HOTKEYS)
    root = _topmost_tk_root()
    try:
        return simpledialog.askstring(
            f"{APP_NAME} - Set Hotkey",
            f"Current hotkey: {format_hotkey(current)}\n\n"
            "Type a new combination, e.g. Ctrl+Alt+F10\n"
            "(one or more of Ctrl, Alt, Shift, plus one other key)\n\n"
            f"Suggested: {suggestions}\n"
            "Function-key combos are least likely to clash with other apps.",
            initialvalue=format_hotkey(current),
            parent=root,
        )
    finally:
        root.destroy()


def show_error(message: str):
    from tkinter import messagebox

    root = _topmost_tk_root()
    try:
        messagebox.showerror(f"{APP_NAME} - Set Hotkey", message, parent=root)
    finally:
        root.destroy()


def confirm(message: str) -> bool:
    from tkinter import messagebox

    root = _topmost_tk_root()
    try:
        return bool(
            messagebox.askokcancel(f"{APP_NAME} - Set Hotkey", message, parent=root)
        )
    finally:
        root.destroy()


def show_hotkey_test_prompt(hotkey: str, seconds: int, done) -> bool:
    """Ask the user to press `hotkey` to confirm it works.

    Shows a modal that closes as soon as `done` (a threading.Event set by the
    hotkey handler) fires, or when the countdown runs out. Returns True if the
    hotkey was detected.
    """
    import tkinter as tk

    root = tk.Tk()
    root.title(f"{APP_NAME} - Confirm Hotkey")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.geometry("380x150")

    tk.Label(
        root,
        text=f"Press {format_hotkey(hotkey)} now to confirm it works.",
        font=("Segoe UI", 10, "bold"),
        pady=10,
    ).pack()
    status = tk.Label(
        root,
        text=f"Waiting... {seconds}s\n\nIf nothing happens, the combination is "
        "blocked by\nanother app - your previous hotkey will be kept.",
        justify="center",
    )
    status.pack()

    remaining = [seconds]

    def tick():
        if done.is_set():
            root.destroy()
            return
        remaining[0] -= 1
        if remaining[0] <= 0:
            root.destroy()
            return
        status.config(
            text=f"Waiting... {remaining[0]}s\n\nIf nothing happens, the "
            "combination is blocked by\nanother app - your previous hotkey "
            "will be kept."
        )
        root.after(1000, tick)

    # Cancelling the window counts as "did not work" - the caller reverts.
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.after(1000, tick)
    root.mainloop()
    return done.is_set()


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
        self.key_listener = None
        self.hotkey = get_hotkey()
        # Set while the Set Hotkey dialog waits for the user to press their new
        # combo; a press signals this event instead of running a rephrase.
        self._awaiting_hotkey_test = None
        # Live set of keys currently held down, kept up to date by key_listener.
        # Used to wait for hotkey release before copying the selection.
        self._pressed_keys = set()
        self.icon = pystray.Icon(
            APP_NAME, make_icon_image(), APP_NAME, menu=self._build_menu()
        )

    # --- Menu ---------------------------------------------------------------

    def _build_menu(self) -> pystray.Menu:
        Item = pystray.MenuItem

        def radio_items(options: dict, getter, setter, name_of):
            def make_action(k):
                return lambda icon, item: self._select(setter, k)

            def make_checked(k):
                return lambda item: getter() == k

            return pystray.Menu(
                *[
                    Item(
                        name_of(key, value),
                        make_action(key),
                        checked=make_checked(key),
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
                lambda item: self._api_key_status_text(),
                None,
                enabled=False,
            ),
            Item("Set API Key...", self.prompt_api_key),
            pystray.Menu.SEPARATOR,
            Item(
                lambda item: f"Hotkey: {format_hotkey(self.hotkey)}",
                None,
                enabled=False,
            ),
            Item("Set Hotkey...", self.prompt_hotkey),
            Item("Reset Hotkey to Default", self.reset_hotkey_to_default),
            pystray.Menu.SEPARATOR,
            Item("Test Rephrase", self.test_rephrase),
            Item("Open Logs Folder", self.open_logs),
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

    def _api_key_status_text(self) -> str:
        try:
            return "API Key: ✓ Set" if get_api_key() else "API Key: ✗ Not set"
        except CredentialStoreError as e:
            log.warning(f"Credential store unavailable: {e}")
            return "API Key: ⚠ Store unavailable"

    # --- Menu actions ---------------------------------------------------------

    def prompt_api_key(self, icon=None, item=None):
        log.debug("Prompting for API key...")
        api_key = ask_api_key()
        if api_key and api_key.strip():
            try:
                set_api_key(api_key.strip())
            except CredentialStoreError as e:
                log.error(f"Failed to save API key: {e}")
                notify("Rephrase ✗", str(e))
                return
            log.info("API key saved successfully")
            notify(APP_NAME, "API key saved securely")
            self.icon.update_menu()
        else:
            log.debug("API key prompt cancelled")

    # Seconds the user gets to press their new hotkey to confirm it works.
    HOTKEY_TEST_SECONDS = 10

    def prompt_hotkey(self, icon=None, item=None):
        """Set Hotkey: validate, warn, probe for conflicts, then live-test it.

        Runs off the tray thread - tkinter dialogs would otherwise block the
        menu, and the live test needs the hotkey listener to keep running.
        """
        threading.Thread(target=self._prompt_hotkey_flow, daemon=True).start()

    def _prompt_hotkey_flow(self):
        previous = self.hotkey
        raw = ask_hotkey(previous)
        if not raw or not raw.strip():
            log.debug("Set Hotkey cancelled")
            return

        # 1. Parse + blocklist. Ctrl+C and friends are refused outright: the app
        #    simulates them internally, so they would make it trigger itself.
        try:
            candidate = validate_hotkey(raw)
        except HotkeyError as e:
            log.info(f"Rejected hotkey {raw!r}: {e}")
            show_error(str(e))
            return

        if candidate == previous:
            notify(APP_NAME, f"Hotkey unchanged ({format_hotkey(candidate)})")
            return

        # 2. Warn about combos that clash with common app shortcuts. Allowed -
        #    the user can override, since we cannot know what they actually use.
        warning = warning_for_hotkey(candidate)
        if warning and not confirm(
            f"{warning}\n\nRephrase does not block the other app's shortcut, so "
            f"both would fire.\n\nUse {format_hotkey(candidate)} anyway?"
        ):
            log.debug("User declined warned hotkey")
            return

        # 3. Probe combos another app has globally reserved (PowerToys, capture
        #    tools). These would never reach us at all.
        if is_taken_by_another_app(candidate):
            log.info(f"Hotkey {candidate} already registered by another app")
            show_error(
                f"{format_hotkey(candidate)} is already registered by another "
                "application.\n\nPick a different combination."
            )
            return

        # 4. Live test: switch to the new hotkey, ask the user to press it, and
        #    revert if it never arrives. Guarantees they are never left stranded
        #    with a hotkey that does not fire.
        log.info(f"Trying hotkey {candidate} (previous: {previous})")
        try:
            set_hotkey(candidate)
        except HotkeyError as e:
            show_error(str(e))
            return

        self.restart_hotkey_listener()
        self.icon.update_menu()

        detected = threading.Event()
        self._awaiting_hotkey_test = detected
        try:
            worked = show_hotkey_test_prompt(
                candidate, self.HOTKEY_TEST_SECONDS, detected
            )
        finally:
            self._awaiting_hotkey_test = None

        if worked:
            log.info(f"Hotkey confirmed: {candidate}")
            notify("Rephrase ✓", f"Hotkey set to {format_hotkey(candidate)}")
            return

        log.warning(f"Hotkey {candidate} not detected, reverting to {previous}")
        try:
            set_hotkey(previous)
        except HotkeyError:
            reset_hotkey()
        self.restart_hotkey_listener()
        self.icon.update_menu()
        show_error(
            f"{format_hotkey(candidate)} was not detected.\n\nSomething else is "
            "likely intercepting it. Kept your previous hotkey "
            f"({format_hotkey(self.hotkey)})."
        )

    def reset_hotkey_to_default(self, icon=None, item=None):
        def run():
            default = reset_hotkey()
            log.info(f"Hotkey reset to default: {default}")
            self.restart_hotkey_listener()
            self.icon.update_menu()
            notify(APP_NAME, f"Hotkey reset to {format_hotkey(default)}")

        threading.Thread(target=run, daemon=True).start()

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
        self.stop_hotkey_listener()
        self.icon.stop()

    # --- Hotkey + workflow ------------------------------------------------------

    def start_hotkey_listener(self):
        """Register the user's configured global hotkey."""
        DEBOUNCE_SECONDS = 1.0
        last_triggered = [0.0]

        hotkey = get_hotkey()
        self.hotkey = hotkey

        def on_hotkey():
            current_time = time.time()
            if current_time - last_triggered[0] < DEBOUNCE_SECONDS:
                log.debug("Hotkey debounced")
                return
            last_triggered[0] = current_time
            log.info(f"Hotkey {format_hotkey(hotkey)} detected!")

            # While the Set Hotkey dialog is waiting for confirmation, a press
            # proves the combo works - it must not also rephrase whatever
            # happens to be selected.
            if self._awaiting_hotkey_test is not None:
                self._awaiting_hotkey_test.set()
                return

            if self.is_processing:
                log.debug("Already processing, ignoring hotkey")
                return

            def run():
                # Wait until every key in the hotkey is released before sending
                # Ctrl+C. Otherwise a still-held key types into and overwrites
                # the selected text. This waits however long the keys are held
                # (0.5s or 5s) and fires the instant they're released, with a
                # timeout backstop in case a key-release event is ever missed.
                deadline = time.time() + HOTKEY_RELEASE_TIMEOUT
                while not hotkey_keys_released(self._pressed_keys, hotkey):
                    if time.time() >= deadline:
                        log.warning("Timed out waiting for hotkey release")
                        break
                    time.sleep(0.02)
                log.debug("Hotkey released, copying selection")
                self.do_rephrase()

            threading.Thread(target=run, daemon=True).start()

        def on_press(key):
            self._pressed_keys.add(key)

        def on_release(key):
            self._pressed_keys.discard(key)

        # GlobalHotKeys parses the combo string and handles the modifier-state
        # quirks that a raw Listener (like the Mac version) would misread. A
        # separate lightweight Listener tracks which keys are currently held so
        # we can wait for the hotkey to be released before copying.
        self.hotkeys = keyboard.GlobalHotKeys({hotkey: on_hotkey})
        self.hotkeys.start()
        self.key_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.key_listener.start()
        log.debug(f"Hotkey listener started ({format_hotkey(hotkey)})")

    def stop_hotkey_listener(self):
        """Tear down the listeners so a new hotkey can be registered."""
        if self.hotkeys:
            self.hotkeys.stop()
            self.hotkeys = None
        if self.key_listener:
            self.key_listener.stop()
            self.key_listener = None
        self._pressed_keys.clear()

    def restart_hotkey_listener(self):
        """Re-register listeners against the current configured hotkey."""
        self.stop_hotkey_listener()
        self.start_hotkey_listener()

    def check_first_run(self):
        """On first launch (no API key stored yet), walk the user through setup."""
        try:
            if get_api_key():
                return
        except CredentialStoreError as e:
            log.error(f"Credential store unavailable at startup: {e}")
            notify("Rephrase ✗", str(e))
            return

        def run_onboarding():
            # Let the tray icon appear before showing dialogs
            time.sleep(1.0)
            log.info("First run: no API key set, showing onboarding")
            try:
                show_welcome(self.hotkey)
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
            # Snapshot the user's clipboard before get_selected_text() probes
            # the selection (which overwrites the clipboard), so we can restore
            # it after pasting the rephrased text.
            original_clipboard = read_clipboard()

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
            if paste_text(rephrased, restore_clipboard=original_clipboard):
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
        log.info(f"App initialized. Hotkey: {format_hotkey(self.hotkey)}")
        self.icon.run()


if __name__ == "__main__":
    app = RephraseWinApp()
    app.run()
