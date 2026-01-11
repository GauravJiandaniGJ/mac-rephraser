"""
Tests for clipboard_helper.py - clipboard operations.
"""

import pytest
from unittest.mock import MagicMock


class TestClipboard:
    """Tests for clipboard_helper.py - clipboard operations"""

    def test_get_selected_text_returns_none_on_failure(self, monkeypatch):
        """Should return None when copy fails"""
        from clipboard_helper import get_selected_text
        import subprocess

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("cmd", 1)

        monkeypatch.setattr("subprocess.run", mock_run)
        monkeypatch.setattr("pyperclip.paste", lambda: "")
        monkeypatch.setattr("pyperclip.copy", lambda x: None)

        result = get_selected_text()
        assert result is None

    def test_paste_text_returns_true_on_success(self, monkeypatch):
        """Should return True when paste succeeds"""
        from clipboard_helper import paste_text

        mock_result = MagicMock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *a, **k: mock_result)
        monkeypatch.setattr("pyperclip.copy", lambda x: None)

        result = paste_text("test text")
        assert result is True

    def test_paste_text_returns_false_on_failure(self, monkeypatch):
        """Should return False when paste fails"""
        from clipboard_helper import paste_text
        import subprocess

        def mock_run(*args, **kwargs):
            raise subprocess.TimeoutExpired("cmd", 1)

        monkeypatch.setattr("subprocess.run", mock_run)
        monkeypatch.setattr("pyperclip.copy", lambda x: None)

        result = paste_text("test text")
        assert result is False


class TestClipboardBugs:
    """Tests to reproduce and verify clipboard-related bugs"""

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_subprocess):
        """Use shared mock_subprocess fixture"""
        self.mock_run_result = mock_subprocess["result"]
        self.subprocess_calls = mock_subprocess["calls"]

    def test_original_clipboard_restored_when_nothing_selected(self, monkeypatch):
        """
        When nothing is selected, original clipboard should be restored.
        User had 'important text' in clipboard, triggered hotkey with nothing
        selected - clipboard should still have 'important text'.
        """
        from clipboard_helper import get_selected_text

        clipboard_state = {"value": "important text in clipboard"}
        copy_calls = []

        def mock_paste():
            return clipboard_state["value"]

        def mock_copy(text):
            copy_calls.append(text)
            clipboard_state["value"] = text

        monkeypatch.setattr("pyperclip.paste", mock_paste)
        monkeypatch.setattr("pyperclip.copy", mock_copy)

        result = get_selected_text()

        assert result is None, "Should return None when nothing selected"
        assert clipboard_state["value"] == "important text in clipboard", \
            "Original clipboard content should be restored"

    def test_original_clipboard_preserved_after_successful_copy(self, monkeypatch):
        """
        When text IS selected and copied, the selected text replaces clipboard.
        This is expected behavior - just documenting it.
        """
        from clipboard_helper import get_selected_text

        clipboard_state = {"value": "original content"}
        paste_call_count = [0]

        def mock_paste():
            paste_call_count[0] += 1
            if paste_call_count[0] == 1:
                return "original content"  # First call: save original
            else:
                return "selected text"  # After Cmd+C: return selected text

        def mock_copy(text):
            clipboard_state["value"] = text

        monkeypatch.setattr("pyperclip.paste", mock_paste)
        monkeypatch.setattr("pyperclip.copy", mock_copy)

        result = get_selected_text()

        assert result == "selected text"

    def test_clipboard_not_cleared_if_cmd_c_fails_silently(self, monkeypatch):
        """
        If Cmd+C runs but doesn't actually copy anything (silent failure),
        the clipboard ends up empty because we cleared it first.
        Original clipboard should be restored in this case.
        """
        from clipboard_helper import get_selected_text

        clipboard_state = {"value": "user's important data"}

        def mock_paste():
            return clipboard_state["value"]

        def mock_copy(text):
            clipboard_state["value"] = text

        monkeypatch.setattr("pyperclip.paste", mock_paste)
        monkeypatch.setattr("pyperclip.copy", mock_copy)

        result = get_selected_text()

        assert result is None
        assert clipboard_state["value"] == "user's important data", \
            "Original clipboard should be restored when copy yields nothing"

    def test_handles_clipboard_exception_gracefully(self, monkeypatch):
        """
        Edge case: pyperclip.paste() raises exception.
        Should handle gracefully and not crash.
        """
        from clipboard_helper import get_selected_text

        paste_call_count = [0]

        def mock_paste():
            paste_call_count[0] += 1
            if paste_call_count[0] == 1:
                raise Exception("Clipboard access denied")
            return "selected"

        def mock_copy(text):
            pass

        monkeypatch.setattr("pyperclip.paste", mock_paste)
        monkeypatch.setattr("pyperclip.copy", mock_copy)

        # Should not raise
        result = get_selected_text()
        assert result == "selected"

    def test_get_selected_text_with_empty_string_selected(self, monkeypatch):
        """
        Edge case: User selects empty text or whitespace only.
        Should return None and restore original clipboard.
        """
        from clipboard_helper import get_selected_text

        clipboard_state = {"value": "original"}

        def mock_paste():
            return clipboard_state["value"]

        def mock_copy(text):
            clipboard_state["value"] = text

        monkeypatch.setattr("pyperclip.paste", mock_paste)
        monkeypatch.setattr("pyperclip.copy", mock_copy)

        result = get_selected_text()

        assert result is None
        assert clipboard_state["value"] == "original", \
            "Original clipboard should be restored"

    def test_clipboard_timing_race_condition(self, monkeypatch):
        """
        The delay after Cmd+C might not be enough.
        If clipboard hasn't updated yet, we get empty string and
        return None even though text WAS selected.

        This simulates: Cmd+C is sent, clipboard will update, but
        when we check (after delay), it hasn't updated yet.
        """
        from clipboard_helper import get_selected_text

        clipboard_state = {"value": "original", "update_pending": True}
        paste_call_count = [0]

        def mock_paste():
            paste_call_count[0] += 1
            if paste_call_count[0] == 1:
                return clipboard_state["value"]  # Original: "original"
            # After clear + Cmd+C, but clipboard hasn't updated yet
            # In real life, this happens when delay isn't enough
            if clipboard_state["update_pending"]:
                return ""  # Clipboard shows empty (hasn't updated)
            return "selected text"

        def mock_copy(text):
            clipboard_state["value"] = text

        monkeypatch.setattr("pyperclip.paste", mock_paste)
        monkeypatch.setattr("pyperclip.copy", mock_copy)

        result = get_selected_text()

        # Returns None because clipboard appears empty after retries
        assert result is None
        # At minimum, original clipboard should be restored
        assert clipboard_state["value"] == "original", \
            "Original clipboard should be restored on failure"

    def test_restoration_fails_silently(self, monkeypatch):
        """
        If pyperclip.copy() fails during restoration,
        it should be handled gracefully (not crash).
        """
        from clipboard_helper import get_selected_text

        clipboard_state = {"value": "important data"}
        restore_attempted = [False]

        def mock_paste():
            return clipboard_state["value"]

        def mock_copy(text):
            if text == "important data":
                restore_attempted[0] = True
                raise Exception("Clipboard write failed")
            clipboard_state["value"] = text

        monkeypatch.setattr("pyperclip.paste", mock_paste)
        monkeypatch.setattr("pyperclip.copy", mock_copy)

        # Should not raise - restoration failure is handled gracefully
        result = get_selected_text()

        assert result is None
        assert restore_attempted[0], "Should have attempted to restore"

    def test_whitespace_only_selection_handled(self, monkeypatch):
        """
        Edge case: User selects only whitespace (spaces, newlines).
        Should be treated as "no selection" and return None.
        Original clipboard should be restored.
        """
        from clipboard_helper import get_selected_text

        clipboard_state = {"value": "original"}
        paste_call_count = [0]

        def mock_paste():
            paste_call_count[0] += 1
            if paste_call_count[0] == 1:
                return "original"
            return "   \n\t  "  # Whitespace only

        def mock_copy(text):
            clipboard_state["value"] = text

        monkeypatch.setattr("pyperclip.paste", mock_paste)
        monkeypatch.setattr("pyperclip.copy", mock_copy)

        result = get_selected_text()

        # Whitespace-only should be treated as no selection
        assert result is None, "Whitespace-only should return None"
        assert clipboard_state["value"] == "original", \
            "Original clipboard should be restored"
