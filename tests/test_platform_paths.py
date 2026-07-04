"""Tests for platform-specific config directory resolution."""

import sys
from pathlib import Path

from config import get_config_dir


def test_config_dir_macos(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert get_config_dir() == Path.home() / ".config" / "rephrase"


def test_config_dir_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert get_config_dir() == Path.home() / ".config" / "rephrase"


def test_config_dir_windows_uses_appdata(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(Path("C:/Users/test/AppData/Roaming")))
    assert get_config_dir() == Path("C:/Users/test/AppData/Roaming") / "Rephrase"


def test_config_dir_windows_without_appdata(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    assert get_config_dir() == Path.home() / "AppData" / "Roaming" / "Rephrase"


def test_usage_stats_uses_shared_config_dir():
    import usage_stats

    assert usage_stats.STATS_FILE.name == "usage_stats.json"
    assert usage_stats.STATS_DIR == get_config_dir()
