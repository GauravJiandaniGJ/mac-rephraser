"""
Tests for config.py - settings management.
"""

import pytest


class TestConfig:
    """Tests for config.py - settings management"""

    def test_default_config_values(self):
        """Default config should have expected values"""
        from config import DEFAULT_CONFIG

        assert DEFAULT_CONFIG["model"] == "gpt-4o-mini"
        assert DEFAULT_CONFIG["tone"] == "rephrase"
        assert DEFAULT_CONFIG["seniority"] == "none"

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

    def test_load_config_creates_default(self, temp_config):
        """load_config should return defaults if no config file"""
        from config import load_config

        config = load_config()
        assert config["model"] == "gpt-4o-mini"
        assert config["tone"] == "rephrase"

    def test_save_and_load_config(self, temp_config):
        """Should save and load config correctly"""
        from config import load_config, save_config

        # Save custom config
        save_config({"model": "gpt-4o", "tone": "professional"})

        # Load and verify
        config = load_config()
        assert config["model"] == "gpt-4o"
        assert config["tone"] == "professional"

    def test_set_and_get_model(self, temp_config):
        """set_model and get_model should work correctly"""
        from config import get_model, set_model

        set_model("gpt-4o")
        assert get_model() == "gpt-4o"

        set_model("gpt-4o-mini")
        assert get_model() == "gpt-4o-mini"

    def test_set_and_get_tone(self, temp_config):
        """set_tone and get_tone should work correctly"""
        from config import get_tone, set_tone

        set_tone("professional")
        assert get_tone() == "professional"

        set_tone("concise")
        assert get_tone() == "concise"


class TestSeniority:
    """Tests for seniority configuration"""

    def test_seniority_levels_available(self):
        """Should have all expected seniority levels"""
        from config import SENIORITY_LEVELS

        expected_levels = ["senior", "mid", "none"]
        for level in expected_levels:
            assert level in SENIORITY_LEVELS, f"Missing level: {level}"
            assert "name" in SENIORITY_LEVELS[level], f"Level {level} missing 'name'"
            assert "modifier" in SENIORITY_LEVELS[level], f"Level {level} missing 'modifier'"

    def test_senior_modifier_not_empty(self):
        """Senior level should have a non-empty modifier"""
        from config import SENIORITY_LEVELS

        assert len(SENIORITY_LEVELS["senior"]["modifier"]) > 20

    def test_none_modifier_is_empty(self):
        """None level should have empty modifier"""
        from config import SENIORITY_LEVELS

        assert SENIORITY_LEVELS["none"]["modifier"] == ""

    def test_set_and_get_seniority(self, temp_config):
        """set_seniority and get_seniority should work correctly"""
        from config import get_seniority, set_seniority

        # Default should be "none"
        assert get_seniority() == "none"

        set_seniority("senior")
        assert get_seniority() == "senior"

        set_seniority("mid")
        assert get_seniority() == "mid"

        set_seniority("none")
        assert get_seniority() == "none"


class TestParseContext:
    """Tests for parse_context function"""

    def test_basic_context(self):
        """Should extract context from brackets"""
        from config import parse_context

        context, text = parse_context("[meeting notes] hello world")
        assert context == "meeting notes"
        assert text == "hello world"

    def test_no_context(self):
        """Should return None when no brackets"""
        from config import parse_context

        context, text = parse_context("just regular text")
        assert context is None
        assert text == "just regular text"

    def test_context_with_tone_prefix(self):
        """Context should work with inline tone prefix"""
        from config import parse_context

        context, text = parse_context("[urgent] formal: fix this now")
        assert context == "urgent"
        assert text == "formal: fix this now"

    def test_empty_brackets(self):
        """Empty brackets should return None context"""
        from config import parse_context

        context, text = parse_context("[] some text")
        assert context is None
        assert text == "[] some text"

    def test_nested_brackets(self):
        """Should handle nested brackets"""
        from config import parse_context

        context, text = parse_context("[foo [bar] baz] text")
        assert context == "foo [bar] baz"
        assert text == "text"

    def test_whitespace_handling(self):
        """Should strip whitespace from context and text"""
        from config import parse_context

        context, text = parse_context("  [  client call  ]   hello  ")
        assert context == "client call"
        assert text == "hello"

    def test_no_closing_bracket(self):
        """Unclosed bracket should return None context"""
        from config import parse_context

        context, text = parse_context("[unclosed text")
        assert context is None
        assert text == "[unclosed text"

    def test_bracket_not_at_start(self):
        """Brackets not at start should return None context"""
        from config import parse_context

        context, text = parse_context("hello [world]")
        assert context is None
        assert text == "hello [world]"

    def test_multiline_text_after_context(self):
        """Should handle multiline text after context"""
        from config import parse_context

        context, text = parse_context("[context] line1\nline2")
        assert context == "context"
        assert text == "line1\nline2"
