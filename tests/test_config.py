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
