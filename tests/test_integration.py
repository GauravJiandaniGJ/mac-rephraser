"""
Integration tests - multiple components working together.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestIntegration:
    """Integration tests - multiple components working together"""

    @pytest.fixture(autouse=True)
    def reset_client(self, reset_api_client):
        """Reset the cached OpenAI client before each test"""
        pass

    def test_full_rephrase_flow_mocked(self, monkeypatch, temp_config):
        """Test complete flow from config to API call"""
        from api import rephrase_text
        from config import set_model, set_tone

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

    def test_inline_override_takes_precedence(self, monkeypatch, temp_config):
        """Inline prefix should override default tone"""
        from api import rephrase_text
        from config import set_tone, TONES

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
