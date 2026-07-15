"""Tests for the Windows global-hotkey conflict probe."""

from hotkey_conflict import (
    MOD_ALT,
    MOD_CONTROL,
    MOD_SHIFT,
    MOD_WIN,
    is_taken_by_another_app,
    to_win32,
)


class TestToWin32:
    def test_default_combo(self):
        flags, vk = to_win32("<ctrl>+<shift>+<f9>")
        assert flags == MOD_CONTROL | MOD_SHIFT
        assert vk == 0x78  # VK_F9

    def test_alt_function_key(self):
        flags, vk = to_win32("<ctrl>+<alt>+<f10>")
        assert flags == MOD_CONTROL | MOD_ALT
        assert vk == 0x79  # VK_F10

    def test_letter_key(self):
        flags, vk = to_win32("<ctrl>+<alt>+r")
        assert flags == MOD_CONTROL | MOD_ALT
        assert vk == ord("R")

    def test_win_key(self):
        flags, _ = to_win32("<cmd>+<shift>+<f9>")
        assert flags == MOD_WIN | MOD_SHIFT

    def test_named_key(self):
        _, vk = to_win32("<ctrl>+<alt>+<space>")
        assert vk == 0x20  # VK_SPACE

    def test_unparseable_returns_none(self):
        assert to_win32("garbage") is None

    def test_no_modifier_returns_none(self):
        # RegisterHotKey needs at least one modifier; validate_hotkey blocks
        # these anyway, but the probe must not construct a bogus registration.
        assert to_win32("<f9>") is None

    def test_modifiers_only_returns_none(self):
        assert to_win32("<ctrl>+<shift>") is None


class TestProbe:
    def test_probe_is_safe_off_windows(self, monkeypatch):
        # On macOS/Linux there is no RegisterHotKey; the probe must report "not
        # taken" rather than raise or block the user from saving.
        monkeypatch.setattr("hotkey_conflict.sys.platform", "darwin")
        assert is_taken_by_another_app("<ctrl>+<shift>+<f9>") is False

    def test_unprobeable_combo_is_not_reported_taken(self):
        assert is_taken_by_another_app("garbage") is False
