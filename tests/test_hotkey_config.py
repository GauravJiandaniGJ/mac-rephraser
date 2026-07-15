"""Release-detection must follow the user's configured hotkey.

The app waits for the hotkey keys to be released before sending Ctrl+C - a key
still held down types into (and destroys) the selected text. When the user picks
a custom combo, the wait has to track *their* keys, not the hard-coded ones.
"""

from pynput.keyboard import Key, KeyCode

from hotkey_release import keys_for_hotkey, hotkey_keys_released


class TestKeysForHotkey:
    def test_default_combo(self):
        keys = keys_for_hotkey("<ctrl>+<shift>+<f9>")
        assert Key.ctrl in keys
        assert Key.shift in keys
        assert Key.f9 in keys

    def test_letter_combo(self):
        keys = keys_for_hotkey("<ctrl>+<alt>+r")
        assert Key.ctrl in keys
        assert Key.alt in keys
        assert KeyCode.from_char("r") in keys


class TestReleasedWithCustomHotkey:
    def test_alt_f10_combo_blocks_on_its_own_keys(self):
        combo = "<ctrl>+<alt>+<f10>"
        assert hotkey_keys_released({Key.ctrl}, combo) is False
        assert hotkey_keys_released({Key.alt}, combo) is False
        assert hotkey_keys_released({Key.f10}, combo) is False
        assert hotkey_keys_released(set(), combo) is True

    def test_shift_not_part_of_combo_does_not_block(self):
        # Shift is not in Ctrl+Alt+F10, so holding it must not stall the copy.
        assert hotkey_keys_released({Key.shift}, "<ctrl>+<alt>+<f10>") is True

    def test_f9_does_not_block_an_f10_hotkey(self):
        assert hotkey_keys_released({Key.f9}, "<ctrl>+<alt>+<f10>") is True

    def test_left_right_modifier_variants_block(self):
        # pynput reports ctrl_l/ctrl_r/alt_r etc.; all variants of a modifier in
        # the combo must count as held.
        combo = "<ctrl>+<alt>+<f10>"
        assert hotkey_keys_released({Key.ctrl_l}, combo) is False
        assert hotkey_keys_released({Key.ctrl_r}, combo) is False
        assert hotkey_keys_released({Key.alt_r}, combo) is False

    def test_letter_key_blocks_until_released(self):
        # The original bug: a still-held 'r' overwrites the selection.
        combo = "<ctrl>+<alt>+r"
        assert hotkey_keys_released({KeyCode.from_char("r")}, combo) is False
        assert hotkey_keys_released(set(), combo) is True

    def test_letter_key_by_vk_blocks(self):
        # Under a held Ctrl, pynput can surface the letter as a raw KeyCode with
        # only the Win32 virtual-key code set ('R' -> 0x52).
        combo = "<ctrl>+<alt>+r"
        assert hotkey_keys_released({KeyCode(vk=0x52)}, combo) is False

    def test_function_key_by_vk_blocks(self):
        # F10's Win32 virtual-key code is 0x79.
        assert hotkey_keys_released({KeyCode(vk=0x79)}, "<ctrl>+<alt>+<f10>") is False

    def test_unrelated_vk_does_not_block(self):
        assert hotkey_keys_released({KeyCode(vk=0x41)}, "<ctrl>+<alt>+<f10>") is True

    def test_invalid_combo_falls_back_to_blocking_on_any_modifier(self):
        # A corrupt config value must never make the app copy while keys are
        # held - degrade safely rather than skipping the wait entirely.
        assert hotkey_keys_released({Key.ctrl}, "garbage") is False
        assert hotkey_keys_released(set(), "garbage") is True


class TestBackwardCompatibleDefault:
    """Existing call sites pass no combo and must keep working (Ctrl+Shift+F9)."""

    def test_default_arg_uses_configured_default(self):
        assert hotkey_keys_released(set()) is True
        assert hotkey_keys_released({Key.ctrl}) is False
        assert hotkey_keys_released({Key.shift}) is False
        assert hotkey_keys_released({Key.f9}) is False
