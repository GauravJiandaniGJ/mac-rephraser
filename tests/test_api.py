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


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function"""

    def test_basic_prompt_without_seniority_or_context(self):
        """Should return tone prompt when no seniority or context"""
        from api import build_system_prompt
        from config import TONES

        prompt = build_system_prompt("rephrase", "none", None)
        assert prompt == TONES["rephrase"]["prompt"]

    def test_prompt_with_seniority(self):
        """Should prepend seniority modifier to prompt"""
        from api import build_system_prompt
        from config import TONES, SENIORITY_LEVELS

        prompt = build_system_prompt("professional", "senior", None)

        # Should contain both seniority modifier and tone prompt
        assert SENIORITY_LEVELS["senior"]["modifier"] in prompt
        assert TONES["professional"]["prompt"] in prompt

        # Seniority should come first
        seniority_pos = prompt.find(SENIORITY_LEVELS["senior"]["modifier"])
        tone_pos = prompt.find(TONES["professional"]["prompt"])
        assert seniority_pos < tone_pos

    def test_prompt_with_context(self):
        """Should append context to prompt"""
        from api import build_system_prompt
        from config import TONES

        prompt = build_system_prompt("concise", "none", "Q4 planning meeting")

        assert TONES["concise"]["prompt"] in prompt
        assert "Context: Q4 planning meeting" in prompt

        # Context should come after tone prompt
        tone_pos = prompt.find(TONES["concise"]["prompt"])
        context_pos = prompt.find("Context:")
        assert context_pos > tone_pos

    def test_prompt_with_seniority_and_context(self):
        """Should combine seniority, tone, and context correctly"""
        from api import build_system_prompt
        from config import TONES, SENIORITY_LEVELS

        prompt = build_system_prompt("friendly", "senior", "team standup")

        # All three should be present
        assert SENIORITY_LEVELS["senior"]["modifier"] in prompt
        assert TONES["friendly"]["prompt"] in prompt
        assert "Context: team standup" in prompt

        # Order should be: seniority -> tone -> context
        seniority_pos = prompt.find(SENIORITY_LEVELS["senior"]["modifier"])
        tone_pos = prompt.find(TONES["friendly"]["prompt"])
        context_pos = prompt.find("Context:")
        assert seniority_pos < tone_pos < context_pos


class TestRephraseSeniorityAndContext:
    """Tests for rephrase_text with seniority and context features"""

    @pytest.fixture(autouse=True)
    def reset_client(self, reset_api_client):
        """Reset the cached OpenAI client before each test"""
        pass

    def test_rephrase_with_context(self, monkeypatch, temp_config):
        """Should parse context from brackets and include in prompt"""
        from api import rephrase_text

        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Result"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            rephrase_text("[client meeting] fix this issue")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # System prompt should include context
        system_prompt = messages[0]["content"]
        assert "Context: client meeting" in system_prompt

        # User message should not include brackets
        user_message = messages[1]["content"]
        assert user_message == "fix this issue"
        assert "[" not in user_message

    def test_rephrase_with_seniority(self, monkeypatch, temp_config):
        """Should include seniority modifier in prompt when set"""
        from api import rephrase_text
        from config import set_seniority, SENIORITY_LEVELS

        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")
        set_seniority("senior")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Result"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            rephrase_text("hello world")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_prompt = messages[0]["content"]

        assert SENIORITY_LEVELS["senior"]["modifier"] in system_prompt

    def test_rephrase_with_context_and_tone_prefix(self, monkeypatch, temp_config):
        """Should handle both context and inline tone prefix"""
        from api import rephrase_text
        from config import TONES

        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Result"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            rephrase_text("[urgent] formal: please fix this")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # System prompt should include context and professional tone
        system_prompt = messages[0]["content"]
        assert "Context: urgent" in system_prompt
        assert TONES["professional"]["prompt"] in system_prompt

        # User message should be clean
        user_message = messages[1]["content"]
        assert user_message == "please fix this"

    def test_rephrase_full_combination(self, monkeypatch, temp_config):
        """Should combine seniority + context + tone correctly"""
        from api import rephrase_text
        from config import set_seniority, TONES, SENIORITY_LEVELS

        monkeypatch.setattr("api.get_api_key", lambda: "fake-key")
        set_seniority("senior")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Professional result"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("api.OpenAI", return_value=mock_client):
            result = rephrase_text("[Q4 roadmap] concise: defer this to next sprint")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        system_prompt = messages[0]["content"]

        # All components should be present
        assert SENIORITY_LEVELS["senior"]["modifier"] in system_prompt
        assert TONES["concise"]["prompt"] in system_prompt
        assert "Context: Q4 roadmap" in system_prompt

        # User message should be clean
        user_message = messages[1]["content"]
        assert user_message == "defer this to next sprint"

        assert result == "Professional result"
