"""Tests for the persisted hotkey setting in config.py.

The hotkey lives in the per-machine config file, so each system can have its
own combo with no sync.
"""

import json

import pytest


class TestHotkeySetting:
    def test_default_is_ctrl_shift_f9(self):
        from config import DEFAULT_CONFIG

        assert DEFAULT_CONFIG["hotkey"] == "<ctrl>+<shift>+<f9>"

    def test_get_hotkey_returns_default_when_unset(self, temp_config):
        from config import get_hotkey

        assert get_hotkey() == "<ctrl>+<shift>+<f9>"

    def test_set_and_get_hotkey(self, temp_config):
        from config import get_hotkey, set_hotkey

        set_hotkey("<ctrl>+<alt>+<f10>")
        assert get_hotkey() == "<ctrl>+<alt>+<f10>"

    def test_set_hotkey_normalizes_friendly_input(self, temp_config):
        from config import get_hotkey, set_hotkey

        set_hotkey("Ctrl + Alt + F10")
        assert get_hotkey() == "<ctrl>+<alt>+<f10>"

    def test_set_hotkey_rejects_blocked_combo(self, temp_config):
        from config import get_hotkey, set_hotkey
        from hotkey_validation import HotkeyError

        with pytest.raises(HotkeyError):
            set_hotkey("ctrl+c")
        # And must not have persisted anything.
        assert get_hotkey() == "<ctrl>+<shift>+<f9>"

    def test_reset_hotkey_restores_default(self, temp_config):
        from config import get_hotkey, reset_hotkey, set_hotkey

        set_hotkey("<ctrl>+<alt>+<f10>")
        reset_hotkey()
        assert get_hotkey() == "<ctrl>+<shift>+<f9>"

    def test_corrupt_hotkey_in_file_falls_back_to_default(self, temp_config):
        """A hand-edited, unparseable hotkey must not brick the app at startup."""
        from config import get_hotkey

        temp_config.mkdir(parents=True, exist_ok=True)
        (temp_config / "config.json").write_text(
            json.dumps({"model": "gpt-4o-mini", "hotkey": "ctrl+shft+f9"})
        )
        assert get_hotkey() == "<ctrl>+<shift>+<f9>"

    def test_blocked_hotkey_in_file_falls_back_to_default(self, temp_config):
        """Hand-editing Ctrl+C into the file must not self-trigger the app."""
        from config import get_hotkey

        temp_config.mkdir(parents=True, exist_ok=True)
        (temp_config / "config.json").write_text(json.dumps({"hotkey": "<ctrl>+c"}))
        assert get_hotkey() == "<ctrl>+<shift>+<f9>"

    def test_hotkey_survives_other_setting_changes(self, temp_config):
        from config import get_hotkey, set_hotkey, set_model, set_tone

        set_hotkey("<ctrl>+<alt>+<f10>")
        set_model("gpt-4o")
        set_tone("concise")
        assert get_hotkey() == "<ctrl>+<alt>+<f10>"
