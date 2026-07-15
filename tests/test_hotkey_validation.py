"""Tests for hotkey parsing, validation, and formatting.

Guards the rules that keep a user from saving a hotkey that would break the app:
Ctrl+C/Ctrl+V are used internally by the copy/paste workflow, and a bare key
with no modifier would fire on ordinary typing.
"""

import pytest

from hotkey_validation import (
    DEFAULT_HOTKEY,
    SUGGESTED_HOTKEYS,
    HotkeyError,
    format_hotkey,
    normalize_hotkey,
    validate_hotkey,
    warning_for_hotkey,
)


class TestNormalize:
    def test_friendly_input_becomes_pynput_form(self):
        assert normalize_hotkey("ctrl+shift+f9") == "<ctrl>+<shift>+<f9>"

    def test_spaces_and_case_are_tolerated(self):
        assert normalize_hotkey("  Ctrl + Shift + F9 ") == "<ctrl>+<shift>+<f9>"

    def test_already_canonical_input_is_unchanged(self):
        assert normalize_hotkey("<ctrl>+<alt>+<f10>") == "<ctrl>+<alt>+<f10>"

    def test_letters_stay_bare(self):
        # pynput wants literal characters unbracketed: <ctrl>+<alt>+r
        assert normalize_hotkey("ctrl+alt+R") == "<ctrl>+<alt>+r"

    def test_aliases(self):
        assert normalize_hotkey("control+shift+f9") == "<ctrl>+<shift>+<f9>"
        assert normalize_hotkey("ctrl+win+f9") == "<ctrl>+<cmd>+<f9>"

    def test_unknown_key_name_rejected(self):
        with pytest.raises(HotkeyError):
            normalize_hotkey("ctrl+shft+f9")

    def test_empty_rejected(self):
        with pytest.raises(HotkeyError):
            normalize_hotkey("")

    def test_dangling_separator_rejected(self):
        with pytest.raises(HotkeyError):
            normalize_hotkey("ctrl+")


class TestFormat:
    def test_canonical_becomes_human_readable(self):
        assert format_hotkey("<ctrl>+<shift>+<f9>") == "Ctrl+Shift+F9"

    def test_letter_is_uppercased_for_display(self):
        assert format_hotkey("<ctrl>+<alt>+r") == "Ctrl+Alt+R"

    def test_invalid_value_degrades_to_raw_string(self):
        # Used in menu labels; must never raise and blank out the menu.
        assert format_hotkey("garbage") == "garbage"


class TestValidateBlocklist:
    """Combos the app must refuse outright - no 'continue anyway'."""

    def test_ctrl_c_blocked(self):
        # Ctrl+C is simulated internally to grab the selection: allowing it as
        # the hotkey means every copy triggers a rephrase, and the app retriggers
        # itself.
        with pytest.raises(HotkeyError):
            validate_hotkey("ctrl+c")

    def test_ctrl_v_blocked(self):
        with pytest.raises(HotkeyError):
            validate_hotkey("ctrl+v")

    def test_ctrl_x_blocked(self):
        with pytest.raises(HotkeyError):
            validate_hotkey("ctrl+x")

    def test_bare_key_without_modifier_blocked(self):
        # Would fire on ordinary typing.
        with pytest.raises(HotkeyError):
            validate_hotkey("r")

    def test_bare_function_key_without_modifier_blocked(self):
        with pytest.raises(HotkeyError):
            validate_hotkey("f9")

    def test_modifiers_only_blocked(self):
        # No trigger key at all.
        with pytest.raises(HotkeyError):
            validate_hotkey("ctrl+shift")

    def test_ctrl_alt_delete_blocked(self):
        # Reserved by Windows; the app can never receive it.
        with pytest.raises(HotkeyError):
            validate_hotkey("ctrl+alt+delete")

    def test_blocklist_message_explains_why(self):
        with pytest.raises(HotkeyError) as exc:
            validate_hotkey("ctrl+c")
        assert "copy" in str(exc.value).lower()


class TestValidateAccepts:
    def test_default_is_valid(self):
        assert validate_hotkey(DEFAULT_HOTKEY) == DEFAULT_HOTKEY

    def test_returns_normalized_form(self):
        assert validate_hotkey("Ctrl + Alt + F10") == "<ctrl>+<alt>+<f10>"

    def test_all_suggestions_are_valid_and_unwarned(self):
        # What we recommend must itself pass every check.
        for combo in SUGGESTED_HOTKEYS:
            assert validate_hotkey(combo) == normalize_hotkey(combo)
            assert warning_for_hotkey(combo) is None

    def test_ctrl_shift_letter_is_allowed(self):
        # Allowed, but warned about (see TestWarnings) - not blocked.
        assert validate_hotkey("ctrl+shift+r") == "<ctrl>+<shift>+r"


class TestWarnings:
    def test_ctrl_shift_r_warns_about_browser_reload(self):
        warning = warning_for_hotkey("ctrl+shift+r")
        assert warning is not None
        assert "reload" in warning.lower()

    def test_ctrl_z_warns(self):
        assert warning_for_hotkey("ctrl+z") is not None

    def test_f5_with_modifier_warns(self):
        assert warning_for_hotkey("ctrl+f5") is not None

    def test_win_key_warns(self):
        assert warning_for_hotkey("cmd+shift+f9") is not None

    def test_clean_combo_has_no_warning(self):
        assert warning_for_hotkey(DEFAULT_HOTKEY) is None
        assert warning_for_hotkey("ctrl+alt+f10") is None

    def test_warning_never_raises_on_blocked_input(self):
        # warning_for_hotkey is called on already-validated input, but must not
        # explode if handed something unparseable.
        assert warning_for_hotkey("garbage") is None
