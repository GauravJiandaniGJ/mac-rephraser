#!/usr/bin/env python3
"""
Rephrase - Mac-wide text rephrasing with OpenAI.

Select text anywhere, press Cmd+Option+R, get it rephrased.
"""

import subprocess
import threading
from pathlib import Path

import rumps
from pynput import keyboard

from api import rephrase_text, RephraseError, recreate_client
from clipboard_helper import get_selected_text, paste_text
from config import MODELS, TONES, get_model, get_tone, set_model, set_tone, reload_config
from keychain_helper import get_api_key, set_api_key
from logger import log
from usage_stats import get_stats_summary, record_rephrase


def notify(title: str, message: str = "", sound: bool = False):
    """Send macOS notification."""
    log.debug(f"Notification: {title} - {message}")
    
    # Escape quotes in message
    message = message.replace('"', '\\"').replace("'", "\\'")
    title = title.replace('"', '\\"').replace("'", "\\'")
    
    script = f'display notification "{message}" with title "{title}"'
    if sound:
        script += ' sound name "default"'
    
    result = subprocess.run(
        ["osascript", "-e", script], 
        capture_output=True, 
        text=True
    )
    
    if result.returncode != 0:
        log.error(f"Notification failed: {result.stderr}")


class RephraseApp(rumps.App):
    def __init__(self):
        log.info("Starting Rephrase app...")
        super().__init__(
            "R✎",
            title="R✎",
            quit_button=None,  # We'll add our own
        )
        
        self.is_processing = False
        self.setup_menu()
        self.start_hotkey_listener()
        log.info("App initialized. Hotkey: Ctrl+Option+R")
    
    def setup_menu(self):
        """Build the menubar menu."""
        # Status item
        self.status_item = rumps.MenuItem("Status: Ready")
        self.status_item.set_callback(None)  # Not clickable
        
        # Model submenu
        self.model_menu = rumps.MenuItem("Model")
        current_model = get_model()
        for model_key, model_name in MODELS.items():
            item = rumps.MenuItem(
                model_name,
                callback=lambda sender, m=model_key: self.select_model(m, sender),
            )
            if model_key == current_model:
                item.state = 1  # Checkmark
            self.model_menu.add(item)
        
        # Tone submenu
        self.tone_menu = rumps.MenuItem("Default Tone")
        current_tone = get_tone()
        for tone_key, tone_config in TONES.items():
            item = rumps.MenuItem(
                tone_config["name"],
                callback=lambda sender, t=tone_key: self.select_tone(t, sender),
            )
            if tone_key == current_tone:
                item.state = 1  # Checkmark
            self.tone_menu.add(item)
        
        # API Key status
        api_key = get_api_key()
        api_status = "API Key: ✓ Set" if api_key else "API Key: ✗ Not set"
        self.api_status_item = rumps.MenuItem(api_status)
        self.api_status_item.set_callback(None)

        # Usage stats
        self.usage_item = rumps.MenuItem(self._get_usage_text())
        self.usage_item.set_callback(None)

        # Build menu
        self.menu = [
            self.status_item,
            self.usage_item,
            None,  # Separator
            self.model_menu,
            self.tone_menu,
            None,  # Separator
            self.api_status_item,
            rumps.MenuItem("Set API Key...", callback=self.prompt_api_key),
            rumps.MenuItem("Recreate OpenAI Client", callback=self.recreate_openai_client),
            rumps.MenuItem("Reload Config", callback=self.reload_config_file),
            rumps.MenuItem("Refresh API Key Status", callback=self.refresh_api_key_status),
            None,  # Separator
            rumps.MenuItem("Test Rephrase", callback=self.test_rephrase),
            rumps.MenuItem("View Logs", callback=self.open_logs),
            rumps.MenuItem("Hotkey: ⌃⌥R", callback=None),
            None,  # Separator
            rumps.MenuItem("Quit", callback=self.quit_app),
        ]
    
    def _get_usage_text(self) -> str:
        """Get formatted usage statistics text for menu."""
        stats = get_stats_summary()
        return f"Today: {stats['today']} | 30 days: {stats['total_30_days']}"

    def _update_usage_display(self):
        """Update the usage stats menu item."""
        self.usage_item.title = self._get_usage_text()

    def select_model(self, model_key: str, sender: rumps.MenuItem):
        """Handle model selection."""
        log.info(f"Model changed to: {model_key}")
        set_model(model_key)
        # Update checkmarks
        for item in self.model_menu.values():
            item.state = 0
        sender.state = 1
    
    def select_tone(self, tone_key: str, sender: rumps.MenuItem):
        """Handle tone selection."""
        log.info(f"Tone changed to: {tone_key}")
        set_tone(tone_key)
        # Update checkmarks
        for item in self.tone_menu.values():
            item.state = 0
        sender.state = 1
    
    def prompt_api_key(self, _):
        """Show dialog to enter API key."""
        log.debug("Prompting for API key...")
        # Use osascript for a simple input dialog
        script = '''
        tell application "System Events"
            display dialog "Enter your OpenAI API Key:" default answer "" with hidden answer with title "Rephrase - API Key"
            return text returned of result
        end tell
        '''
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                api_key = result.stdout.strip()
                set_api_key(api_key)
                self.api_status_item.title = "API Key: ✓ Set"
                log.info("API key saved successfully")
                notify("Rephrase", "API key saved securely")
            else:
                log.debug("API key prompt cancelled")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            log.error(f"API key prompt failed: {e}")
    
    def recreate_openai_client(self, _):
        """Force recreation of the OpenAI client."""
        log.info("User requested OpenAI client recreation")
        if recreate_client():
            notify("Rephrase", "OpenAI client recreated")
        else:
            notify("Rephrase", "Failed - API key not set")

    def reload_config_file(self, _):
        """Reload configuration from file and update UI."""
        log.info("User requested config reload")
        config = reload_config()

        # Update model checkmarks
        current_model = config.get("model", "gpt-4o-mini")
        for model_key, item in self.model_menu.items():
            item.state = 1 if model_key == current_model else 0

        # Update tone checkmarks
        current_tone = config.get("tone", "rephrase")
        for tone_key, item in self.tone_menu.items():
            item.state = 1 if tone_key == current_tone else 0

        notify("Rephrase", "Config reloaded")

    def refresh_api_key_status(self, _):
        """Re-check keychain for API key and update status display."""
        log.info("User requested API key status refresh")
        api_key = get_api_key()
        if api_key:
            self.api_status_item.title = "API Key: ✓ Set"
            notify("Rephrase", "API key found in keychain")
        else:
            self.api_status_item.title = "API Key: ✗ Not set"
            notify("Rephrase", "No API key in keychain")

    def test_rephrase(self, _):
        """Test the rephrase function with sample text."""
        test_text = "i want to check if this is working properly or not"
        log.info(f"Running test rephrase with: {test_text}")
        notify("Rephrase", "Testing with sample text...")
        
        def run_test():
            try:
                result = rephrase_text(test_text)
                log.info(f"Test result: {result}")
                notify("Test Success ✓", result[:100])
            except RephraseError as e:
                log.error(f"Test failed: {e}")
                notify("Test Failed ✗", str(e))
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def open_logs(self, _):
        """Open logs folder in Finder."""
        log_dir = str(Path.home() / ".config" / "rephrase" / "logs")
        subprocess.run(["open", log_dir])
    
    def quit_app(self, _):
        """Quit the application."""
        log.info("Quitting app...")
        rumps.quit_application()
    
    def start_hotkey_listener(self):
        """Start global hotkey listener in background thread."""
        def on_hotkey():
            log.debug("Hotkey triggered!")
            if not self.is_processing:
                # Small delay to let user release keys before we simulate Cmd+C
                import time
                time.sleep(0.2)
                # Run in thread to not block the listener
                threading.Thread(target=self.do_rephrase, daemon=True).start()
            else:
                log.debug("Already processing, ignoring hotkey")
        
        # Track pressed keys manually for debugging
        self.pressed_keys = set()
        
        def on_press(key):
            try:
                key_name = key.char if hasattr(key, 'char') and key.char else str(key)
            except:
                key_name = str(key)

            self.pressed_keys.add(key_name)

            # Check for our combo: Ctrl + Option + R
            held = self.pressed_keys
            if ('Key.ctrl' in held or 'Key.ctrl_r' in held) and \
               ('Key.alt' in held or 'Key.alt_r' in held) and \
               ('r' in held or '®' in held):
                log.info("Hotkey Ctrl+Option+R detected!")
                on_hotkey()
        
        def on_release(key):
            try:
                key_name = key.char if hasattr(key, 'char') and key.char else str(key)
            except:
                key_name = str(key)
            
            self.pressed_keys.discard(key_name)
        
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()
        log.debug("Hotkey listener started")
    
    def do_rephrase(self):
        """Main rephrase workflow."""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.status_item.title = "Status: Working..."
        self.title = "R⏳"
        log.info("Starting rephrase workflow...")
        
        try:
            # Step 1: Get selected text
            log.debug("Getting selected text...")
            selected_text = get_selected_text()
            
            if not selected_text:
                log.warning("No text selected")
                notify("Rephrase", "No text selected")
                return
            
            log.info(f"Selected text ({len(selected_text)} chars): {selected_text[:50]}...")
            
            # Step 2: Call API
            log.debug("Calling OpenAI API...")
            notify("Rephrase", "Rephrasing...")
            rephrased = rephrase_text(selected_text)
            log.info(f"Rephrased ({len(rephrased)} chars): {rephrased[:50]}...")
            
            # Step 3: Paste result
            log.debug("Pasting result...")
            if paste_text(rephrased):
                log.info("Text replaced successfully")
                record_rephrase()
                self._update_usage_display()
                notify("Rephrase ✓", "Text replaced!")
            else:
                log.warning("Paste failed, text is in clipboard")
                notify("Rephrase", "Couldn't paste. Text copied to clipboard.")
        
        except RephraseError as e:
            log.error(f"Rephrase error: {e}")
            notify("Rephrase ✗", str(e))
        
        except Exception as e:
            log.exception(f"Unexpected error: {e}")
            notify("Rephrase ✗", f"Error: {str(e)[:50]}")
        
        finally:
            self.is_processing = False
            self.status_item.title = "Status: Ready"
            self.title = "R✎"
            log.debug("Rephrase workflow completed")


if __name__ == "__main__":
    app = RephraseApp()
    app.run()
