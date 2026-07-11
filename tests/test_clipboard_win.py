"""Tests for the Windows clipboard helper.

The module is importable on any platform (the keyboard Controller is created
lazily), so the copy/paste logic is tested here with mocks.
"""

import clipboard_helper_win as cw


def _no_sleep(monkeypatch):
    monkeypatch.setattr(cw.time, "sleep", lambda s: None)


def test_paste_text_success(monkeypatch):
    copied = []
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: copied.append(t))
    monkeypatch.setattr(cw, "_send_ctrl_key", lambda c: None)

    assert cw.paste_text("hello") is True
    assert copied == ["hello"]


def test_paste_text_failure_returns_false(monkeypatch):
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: None)

    def boom(c):
        raise RuntimeError("no keyboard")

    monkeypatch.setattr(cw, "_send_ctrl_key", boom)

    assert cw.paste_text("hello") is False


def test_paste_text_restores_original_clipboard(monkeypatch):
    _no_sleep(monkeypatch)
    clipboard = {"value": None}
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: clipboard.update(value=t))
    monkeypatch.setattr(cw, "_send_ctrl_key", lambda c: None)

    assert cw.paste_text("rephrased", restore_clipboard="user's original") is True
    # After pasting, the user's original clipboard content must be restored.
    assert clipboard["value"] == "user's original"


def test_paste_text_no_restore_when_none(monkeypatch):
    _no_sleep(monkeypatch)
    clipboard = {"value": None}
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: clipboard.update(value=t))
    monkeypatch.setattr(cw, "_send_ctrl_key", lambda c: None)

    assert cw.paste_text("rephrased") is True
    # With no restore requested, the pasted text stays on the clipboard.
    assert clipboard["value"] == "rephrased"


def test_paste_text_does_not_restore_on_keystroke_failure(monkeypatch):
    _no_sleep(monkeypatch)
    clipboard = {"value": None}
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: clipboard.update(value=t))

    def boom(c):
        raise RuntimeError("no keyboard")

    monkeypatch.setattr(cw, "_send_ctrl_key", boom)

    assert cw.paste_text("rephrased", restore_clipboard="user's original") is False


def test_read_clipboard_returns_content(monkeypatch):
    monkeypatch.setattr(cw.pyperclip, "paste", lambda: "current content")
    assert cw.read_clipboard() == "current content"


def test_read_clipboard_returns_empty_on_error(monkeypatch):
    def boom():
        raise RuntimeError("no clipboard")

    monkeypatch.setattr(cw.pyperclip, "paste", boom)
    assert cw.read_clipboard() == ""


def test_get_selected_text_returns_selection(monkeypatch):
    _no_sleep(monkeypatch)
    clipboard = {"value": "original content"}
    monkeypatch.setattr(cw.pyperclip, "paste", lambda: clipboard["value"])
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: clipboard.update(value=t))

    def fake_ctrl(char):
        if char == "c":
            clipboard["value"] = "selected text"

    monkeypatch.setattr(cw, "_send_ctrl_key", fake_ctrl)

    assert cw.get_selected_text() == "selected text"


def test_get_selected_text_none_when_nothing_selected(monkeypatch):
    _no_sleep(monkeypatch)
    clipboard = {"value": "original content"}
    monkeypatch.setattr(cw.pyperclip, "paste", lambda: clipboard["value"])
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: clipboard.update(value=t))
    monkeypatch.setattr(cw, "_send_ctrl_key", lambda c: None)  # copy has no effect

    assert cw.get_selected_text() is None
    # Original clipboard content must be restored
    assert clipboard["value"] == "original content"


def test_get_selected_text_none_for_whitespace_only(monkeypatch):
    _no_sleep(monkeypatch)
    clipboard = {"value": "original content"}
    monkeypatch.setattr(cw.pyperclip, "paste", lambda: clipboard["value"])
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: clipboard.update(value=t))

    def fake_ctrl(char):
        if char == "c":
            clipboard["value"] = "   \n  "

    monkeypatch.setattr(cw, "_send_ctrl_key", fake_ctrl)

    assert cw.get_selected_text() is None
    assert clipboard["value"] == "original content"


def test_get_selected_text_none_when_keystroke_fails(monkeypatch):
    _no_sleep(monkeypatch)
    clipboard = {"value": "original content"}
    monkeypatch.setattr(cw.pyperclip, "paste", lambda: clipboard["value"])
    monkeypatch.setattr(cw.pyperclip, "copy", lambda t: clipboard.update(value=t))

    def boom(c):
        raise RuntimeError("no keyboard")

    monkeypatch.setattr(cw, "_send_ctrl_key", boom)

    assert cw.get_selected_text() is None
    assert clipboard["value"] == "original content"
