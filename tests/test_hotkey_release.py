"""Tests for hotkey-release detection.

The Windows app copies the selection only after Ctrl, Alt, and 'r' are all
released. Copying while 'r' is still held would overwrite the selected text
with the letter 'r' (the bug this logic fixes).
"""

from pynput import keyboard
from pynput.keyboard import Key, KeyCode

from hotkey_release import hotkey_keys_released, HOTKEY_RELEASE_TIMEOUT


def test_all_released_returns_true():
    assert hotkey_keys_released(set()) is True


def test_ctrl_still_held_returns_false():
    assert hotkey_keys_released({Key.ctrl}) is False
    assert hotkey_keys_released({Key.ctrl_l}) is False
    assert hotkey_keys_released({Key.ctrl_r}) is False


def test_alt_still_held_returns_false():
    assert hotkey_keys_released({Key.alt}) is False
    assert hotkey_keys_released({Key.alt_l}) is False
    assert hotkey_keys_released({Key.alt_gr}) is False


def test_r_still_held_returns_false():
    # The exact scenario the user asked about: Ctrl and Alt released, but 'r'
    # is still down. Must NOT copy yet.
    assert hotkey_keys_released({KeyCode.from_char("r")}) is False


def test_uppercase_r_still_held_returns_false():
    assert hotkey_keys_released({KeyCode.from_char("R")}) is False


def test_ctrl_translated_r_control_char_returns_false():
    # While Ctrl is held, Windows reports Ctrl+R as the control char '\x12'.
    assert hotkey_keys_released({KeyCode.from_char("\x12")}) is False


def test_full_combo_held_returns_false():
    assert hotkey_keys_released({Key.ctrl, Key.alt, KeyCode.from_char("r")}) is False


def test_unrelated_key_held_returns_true():
    # A stray unrelated key (e.g. 'a') does not block copying.
    assert hotkey_keys_released({KeyCode.from_char("a")}) is True


def test_timeout_is_reasonable_backstop():
    # Must be long enough not to fire mid-hold, short enough not to hang.
    assert 1.0 <= HOTKEY_RELEASE_TIMEOUT <= 10.0
