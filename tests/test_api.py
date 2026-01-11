"""
Tests for api.py - OpenAI integration.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAPI:
    """Tests for api.py - OpenAI integration"""

    @pytest.fixture(autouse=True)
    def reset_client(self, reset_api_client):
        """Reset the cached OpenAI client before each test"""
        pass

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

    def test_rephrase_text_uses_correct_model(self, monkeypatch, temp_config):
        """Should use the model from config"""
        from api import rephrase_text
        from config import set_model

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
