"""
Tests for mac-rephraser

Run with: pytest test_rephraser.py -v
Run specific test: pytest test_rephraser.py::test_config_load -v
Run with coverage: pytest test_rephraser.py --cov=. --cov-report=html
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ============================================================================
# CONFIG TESTS
# ============================================================================

class TestConfig:
    """Tests for config.py - settings management"""

    def test_default_config_values(self):
        """Default config should have expected values"""
        from config import DEFAULT_CONFIG

        assert DEFAULT_CONFIG["model"] == "gpt-4o-mini"
        assert DEFAULT_CONFIG["tone"] == "rephrase"

    def test_models_available(self):
        """Should have at least 2 models available"""
        from config import MODELS

        assert "gpt-4o-mini" in MODELS
        assert "gpt-4o" in MODELS
        assert len(MODELS) >= 2

    def test_tones_available(self):
        """Should have all expected tones"""
        from config import TONES

        expected_tones = ["rephrase", "grammar", "professional", "concise", "friendly"]
        for tone in expected_tones:
            assert tone in TONES, f"Missing tone: {tone}"
            assert "name" in TONES[tone], f"Tone {tone} missing 'name'"
            assert "prompt" in TONES[tone], f"Tone {tone} missing 'prompt'"

    def test_tone_prompts_not_empty(self):
        """Each tone should have a non-empty prompt"""
        from config import TONES

        for tone_key, tone_config in TONES.items():
            assert len(tone_config["prompt"]) > 20, f"Tone {tone_key} prompt too short"

    def test_inline_prefixes_map_to_valid_tones(self):
        """All inline prefixes should map to existing tones"""
        from config import INLINE_PREFIXES, TONES

        for prefix, tone_key in INLINE_PREFIXES.items():
            assert tone_key in TONES, f"Prefix '{prefix}' maps to invalid tone '{tone_key}'"

    def test_parse_inline_tone_with_prefix(self):
        """Should detect inline tone prefixes"""
        from config import parse_inline_tone

        # Test various prefixes
        tone, text = parse_inline_tone("formal: hello world")
        assert tone == "professional"
        assert text == "hello world"

        tone, text = parse_inline_tone("concise: this is a long message")
        assert tone == "concise"
        assert text == "this is a long message"

        tone, text = parse_inline_tone("grammar: fix this plz")
        assert tone == "grammar"
        assert text == "fix this plz"

    def test_parse_inline_tone_without_prefix(self):
        """Should return None tone when no prefix"""
        from config import parse_inline_tone

        tone, text = parse_inline_tone("just regular text")
        assert tone is None
        assert text == "just regular text"

    def test_parse_inline_tone_case_insensitive(self):
        """Prefix detection should be case insensitive"""
        from config import parse_inline_tone

        tone, text = parse_inline_tone("FORMAL: hello")
        assert tone == "professional"

        tone, text = parse_inline_tone("Concise: hello")
        assert tone == "concise"

    def test_load_config_creates_default(self, tmp_path, monkeypatch):
        """load_config should return defaults if no config file"""
        from config import load_config, CONFIG_DIR

        # Point to temp directory
        fake_config_dir = tmp_path / ".config" / "rephrase"
        monkeypatch.setattr("config.CONFIG_DIR", fake_config_dir)
        monkeypatch.setattr("config.CONFIG_FILE", fake_config_dir / "config.json")

        config = load_config()
        assert config["model"] == "gpt-4o-mini"
        assert config["tone"] == "rephrase"

    def test_save_and_load_config(self, tmp_path, monkeypatch):
        """Should save and load config correctly"""
        from config import load_config, save_config

        # Point to temp directory
        fake_config_dir = tmp_path / ".config" / "rephrase"
        monkeypatch.setattr("config.CONFIG_DIR", fake_config_dir)
        monkeypatch.setattr("config.CONFIG_FILE", fake_config_dir / "config.json")

        # Save custom config
        save_config({"model": "gpt-4o", "tone": "professional"})

        # Load and verify
        config = load_config()
        assert config["model"] == "gpt-4o"
        assert config["tone"] == "professional"

    def test_set_and_get_model(self, tmp_path, monkeypatch):
        """set_model and get_model should work correctly"""
        from config import get_model, set_model

        fake_config_dir = tmp_path / ".config" / "rephrase"
        monkeypatch.setattr("config.CONFIG_DIR", fake_config_dir)
        monkeypatch.setattr("config.CONFIG_FILE", fake_config_dir / "config.json")

        set_model("gpt-4o")
        assert get_model() == "gpt-4o"

        set_model("gpt-4o-mini")
        assert get_model() == "gpt-4o-mini"

    def test_set_and_get_tone(self, tmp_path, monkeypatch):
        """set_tone and get_tone should work correctly"""
        from config import get_tone, set_tone

        fake_config_dir = tmp_path / ".config" / "rephrase"
        monkeypatch.setattr("config.CONFIG_DIR", fake_config_dir)
        monkeypatch.setattr("config.CONFIG_FILE", fake_config_dir / "config.json")

        set_tone("professional")
        assert get_tone() == "professional"

        set_tone("concise")
        assert get_tone() == "concise"


# ============================================================================
# API TESTS
# ============================================================================

class TestAPI:
    """Tests for api.py - OpenAI integration"""

    @pytest.fixture(autouse=True)
    def reset_api_client(self):
        """Reset the cached OpenAI client before each test"""
        from api import reset_client
        reset_client()
        yield
        reset_client()

    def test_rephrase_error_class_exists(self):
        """RephraseError should be importable"""
        from api import RephraseError

        error = RephraseError("test error")
        assert str(error) == "test error"

    def test_rephrase_text_without_api_key(self, monkeypatch):
        """Should raise error when API key not set"""
        from api import rephrase_text, RephraseError

        # Mock keychain to return None
        monkeypatch.setattr("api.get_api_key", lambda: None)

        with pytest.raises(RephraseError) as exc_info:
            rephrase_text("test text")

        assert "API key not set" in str(exc_info.value)

    def test_rephrase_text_empty_input(self, monkeypatch):
        """Should raise error for empty text"""
        from api import rephrase_text, RephraseError

        # Mock keychain to return a key
        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")

        with pytest.raises(RephraseError) as exc_info:
            rephrase_text("   ")

        assert "No text to rephrase" in str(exc_info.value)

    def test_rephrase_text_with_inline_prefix(self, monkeypatch):
        """Should strip inline prefix before sending to API"""
        from api import rephrase_text

        # Mock keychain
        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")

        # Mock OpenAI client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Rephrased text"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            result = rephrase_text("formal: hello world")

        # Check that the API was called with clean text (no prefix)
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        user_message = messages[1]["content"]

        assert user_message == "hello world"
        assert "formal:" not in user_message

    def test_rephrase_text_success(self, monkeypatch):
        """Should return rephrased text on success"""
        from api import rephrase_text

        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is the rephrased text."

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            result = rephrase_text("test input")

        assert result == "This is the rephrased text."

    def test_rephrase_text_uses_correct_model(self, monkeypatch, tmp_path):
        """Should use the model from config"""
        from api import rephrase_text
        from config import set_model

        # Setup temp config
        fake_config_dir = tmp_path / ".config" / "rephrase"
        monkeypatch.setattr("config.CONFIG_DIR", fake_config_dir)
        monkeypatch.setattr("config.CONFIG_FILE", fake_config_dir / "config.json")

        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")
        set_model("gpt-4o")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Result"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            rephrase_text("test")

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o"


# ============================================================================
# KEYCHAIN TESTS
# ============================================================================

class TestKeychain:
    """Tests for keychain_helper.py - API key storage"""

    def test_service_name_defined(self):
        """Service name should be defined"""
        from keychain_helper import SERVICE_NAME, ACCOUNT_NAME

        assert SERVICE_NAME == "rephrase-app"
        assert ACCOUNT_NAME == "openai-api-key"

    def test_set_and_get_api_key(self, monkeypatch):
        """Should set and get API key via keyring"""
        from keychain_helper import get_api_key, set_api_key

        stored_key = {}

        def mock_set(service, account, password):
            stored_key["value"] = password

        def mock_get(service, account):
            return stored_key.get("value")

        monkeypatch.setattr("keyring.set_password", mock_set)
        monkeypatch.setattr("keyring.get_password", mock_get)

        set_api_key("sk-test-12345")
        assert get_api_key() == "sk-test-12345"

    def test_get_api_key_returns_none_when_not_set(self, monkeypatch):
        """Should return None when no key is set"""
        from keychain_helper import get_api_key

        monkeypatch.setattr("keyring.get_password", lambda s, a: None)

        assert get_api_key() is None

    def test_delete_api_key_no_error_when_missing(self, monkeypatch):
        """delete_api_key should not raise when key doesn't exist"""
        from keychain_helper import delete_api_key
        import keyring

        def mock_delete(service, account):
            raise keyring.errors.PasswordDeleteError("Not found")

        monkeypatch.setattr("keyring.delete_password", mock_delete)

        # Should not raise
        delete_api_key()


# ============================================================================
# CLIPBOARD TESTS
# ============================================================================

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
        import subprocess

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


# ============================================================================
# LOGGER TESTS
# ============================================================================

class TestLogger:
    """Tests for logger.py - logging configuration"""

    def test_logger_is_configured(self):
        """Logger should be properly configured"""
        from logger import log

        assert log is not None
        assert log.name == "rephrase"

    def test_log_directory_constant(self):
        """LOG_DIR should point to correct location"""
        from logger import LOG_DIR
        from pathlib import Path

        expected = Path.home() / ".config" / "rephrase" / "logs"
        assert LOG_DIR == expected


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration tests - multiple components working together"""

    @pytest.fixture(autouse=True)
    def reset_api_client(self):
        """Reset the cached OpenAI client before each test"""
        from api import reset_client
        reset_client()
        yield
        reset_client()

    def test_full_rephrase_flow_mocked(self, monkeypatch, tmp_path):
        """Test complete flow from config to API call"""
        from api import rephrase_text
        from config import set_model, set_tone

        # Setup temp config
        fake_config_dir = tmp_path / ".config" / "rephrase"
        monkeypatch.setattr("config.CONFIG_DIR", fake_config_dir)
        monkeypatch.setattr("config.CONFIG_FILE", fake_config_dir / "config.json")

        # Set config
        set_model("gpt-4o-mini")
        set_tone("professional")

        # Mock API key
        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")

        # Mock OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Professional response."

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            result = rephrase_text("hey can u check this")

        assert result == "Professional response."

        # Verify correct model was used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"

    def test_inline_override_takes_precedence(self, monkeypatch, tmp_path):
        """Inline prefix should override default tone"""
        from api import rephrase_text
        from config import set_tone, TONES

        # Setup temp config
        fake_config_dir = tmp_path / ".config" / "rephrase"
        monkeypatch.setattr("config.CONFIG_DIR", fake_config_dir)
        monkeypatch.setattr("config.CONFIG_FILE", fake_config_dir / "config.json")

        # Set default tone to professional
        set_tone("professional")

        # Mock API key
        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")

        # Mock OpenAI
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Concise result."

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            # Use concise: prefix which should override professional default
            result = rephrase_text("concise: this is a very long message")

        # Verify the concise tone prompt was used
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_prompt = messages[0]["content"]

        assert system_prompt == TONES["concise"]["prompt"]


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def reset_modules():
    """Reset module state between tests"""
    yield
    # Cleanup if needed


# ============================================================================
# RUN INSTRUCTIONS
# ============================================================================
"""
To run these tests:

1. Install pytest:
   pip install pytest pytest-cov

2. Run all tests:
   pytest test_rephraser.py -v

3. Run specific test class:
   pytest test_rephraser.py::TestConfig -v

4. Run specific test:
   pytest test_rephraser.py::TestConfig::test_default_config_values -v

5. Run with coverage:
   pytest test_rephraser.py --cov=. --cov-report=html
   open htmlcov/index.html

6. Run only fast tests (skip integration):
   pytest test_rephraser.py -v -k "not Integration"
"""
