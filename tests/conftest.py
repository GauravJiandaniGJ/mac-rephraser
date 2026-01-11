"""
Shared pytest fixtures for mac-rephraser tests.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def reset_api_client():
    """Reset the cached OpenAI client before and after test."""
    from api import reset_client
    reset_client()
    yield
    reset_client()


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess.run for clipboard tests."""
    mock_result = MagicMock()
    mock_result.stdout = ""
    mock_result.returncode = 0
    subprocess_calls = []

    def mock_run(*args, **kwargs):
        subprocess_calls.append(args)
        return mock_result

    monkeypatch.setattr("subprocess.run", mock_run)
    monkeypatch.setattr("clipboard_helper.time.sleep", lambda x: None)

    return {"result": mock_result, "calls": subprocess_calls}


@pytest.fixture
def temp_config(tmp_path, monkeypatch):
    """Set up temporary config directory for tests."""
    fake_config_dir = tmp_path / ".config" / "rephrase"
    monkeypatch.setattr("config.CONFIG_DIR", fake_config_dir)
    monkeypatch.setattr("config.CONFIG_FILE", fake_config_dir / "config.json")
    return fake_config_dir


@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mocked response text."
    return mock_response


@pytest.fixture
def mock_keychain(monkeypatch):
    """Mock keychain operations."""
    stored_key = {}

    def mock_set(service, account, password):
        stored_key["value"] = password

    def mock_get(service, account):
        return stored_key.get("value")

    monkeypatch.setattr("keyring.set_password", mock_set)
    monkeypatch.setattr("keyring.get_password", mock_get)

    return stored_key
