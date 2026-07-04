"""Tests for the first-run onboarding flow in rephrase.py."""

from unittest.mock import MagicMock

import rephrase


def test_first_run_skipped_when_key_exists(monkeypatch):
    """Onboarding must not start when an API key is already stored."""
    monkeypatch.setattr(rephrase, "get_api_key", lambda: "sk-test-key")

    started = []

    class FakeThread:
        def __init__(self, *args, **kwargs):
            started.append(kwargs)

        def start(self):
            pass

    monkeypatch.setattr(rephrase.threading, "Thread", FakeThread)

    rephrase.RephraseApp.check_first_run(MagicMock())

    assert started == []


def test_first_run_starts_onboarding_without_key(monkeypatch):
    """Onboarding thread starts when no API key is stored."""
    monkeypatch.setattr(rephrase, "get_api_key", lambda: None)

    started = []

    class FakeThread:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs

        def start(self):
            started.append(self.kwargs)

    monkeypatch.setattr(rephrase.threading, "Thread", FakeThread)

    rephrase.RephraseApp.check_first_run(MagicMock())

    assert len(started) == 1
    assert started[0]["daemon"] is True


def test_onboarding_shows_dialog_then_prompts_for_key(monkeypatch):
    """The onboarding flow shows the welcome dialog, then the API key prompt."""
    monkeypatch.setattr(rephrase, "get_api_key", lambda: None)
    monkeypatch.setattr(rephrase.time, "sleep", lambda s: None)

    osascript_calls = []
    monkeypatch.setattr(
        rephrase.subprocess,
        "run",
        lambda *args, **kwargs: osascript_calls.append(args[0]) or MagicMock(),
    )

    # Run the onboarding body synchronously instead of in a thread
    class InlineThread:
        def __init__(self, target=None, daemon=None):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(rephrase.threading, "Thread", InlineThread)

    app = MagicMock()
    rephrase.RephraseApp.check_first_run(app)

    assert len(osascript_calls) == 1
    assert "Welcome to Rephrase" in osascript_calls[0][2]
    app.prompt_api_key.assert_called_once_with(None)
