"""Tests for hotkey-release detection.

The Windows app copies the selection only after Ctrl, Shift, and F9 are all
released. Copying while a modifier is still held can interfere with the copy.
"""

from pynput.keyboard import Key, KeyCode

from hotkey_release import hotkey_keys_released, HOTKEY_RELEASE_TIMEOUT


def test_all_released_returns_true():
    assert hotkey_keys_released(set()) is True


def test_ctrl_still_held_returns_false():
    assert hotkey_keys_released({Key.ctrl}) is False
    assert hotkey_keys_released({Key.ctrl_l}) is False
    assert hotkey_keys_released({Key.ctrl_r}) is False


def test_shift_still_held_returns_false():
    assert hotkey_keys_released({Key.shift}) is False
    assert hotkey_keys_released({Key.shift_l}) is False
    assert hotkey_keys_released({Key.shift_r}) is False


def test_f9_still_held_returns_false():
    # Ctrl and Shift released, but F9 still down. Must NOT copy yet.
    assert hotkey_keys_released({Key.f9}) is False


def test_f9_raw_keycode_by_vk_returns_false():
    # On some layouts/drivers pynput reports F9 as a raw KeyCode carrying the
    # Win32 virtual-key code (0x78) instead of the named Key.f9. It must still
    # be recognized as held.
    assert hotkey_keys_released({KeyCode(vk=0x78)}) is False


def test_other_function_key_vk_does_not_block():
    # A different function key (F8, vk 0x77) held must NOT be treated as F9.
    assert hotkey_keys_released({KeyCode(vk=0x77)}) is True


def test_full_combo_held_returns_false():
    assert hotkey_keys_released({Key.ctrl, Key.shift, Key.f9}) is False


def test_unrelated_key_held_returns_true():
    # A stray unrelated key (e.g. 'a') does not block copying.
    assert hotkey_keys_released({KeyCode.from_char("a")}) is True


def test_timeout_is_reasonable_backstop():
    # Must be long enough not to fire mid-hold, short enough not to hang.
    assert 1.0 <= HOTKEY_RELEASE_TIMEOUT <= 10.0
