"""Configuration management for Rephrase app."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "rephrase"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Available models
MODELS = {
    "gpt-4o-mini": "gpt-4o-mini (Fast, cheaper)",
    "gpt-4o": "gpt-4o (Smarter, slower)",
}

# Available tones with their system prompts
TONES = {
    "rephrase": {
        "name": "Rephrase (fix grammar + clarity)",
        "prompt": "Rephrase the following text to fix grammar and improve clarity. Keep the same meaning and tone. Only output the rephrased text, nothing else.",
    },
    "grammar": {
        "name": "Fix grammar only",
        "prompt": "Fix only the grammar errors in the following text. Make minimal changes. Only output the corrected text, nothing else.",
    },
    "professional": {
        "name": "Professional",
        "prompt": "Rewrite the following text in a professional, formal business tone. Fix any grammar issues. Only output the rewritten text, nothing else.",
    },
    "concise": {
        "name": "Concise",
        "prompt": "Rewrite the following text to be more concise and to the point. Fix any grammar issues. Only output the rewritten text, nothing else.",
    },
    "friendly": {
        "name": "Friendly",
        "prompt": "Rewrite the following text in a warm, friendly, casual tone. Fix any grammar issues. Only output the rewritten text, nothing else.",
    },
}

# Inline prefixes that override default tone
INLINE_PREFIXES = {
    "grammar:": "grammar",
    "fix:": "grammar",
    "professional:": "professional",
    "formal:": "professional",
    "concise:": "concise",
    "short:": "concise",
    "friendly:": "friendly",
    "casual:": "friendly",
}

DEFAULT_CONFIG = {
    "model": "gpt-4o-mini",
    "tone": "rephrase",
}


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file."""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                return {**DEFAULT_CONFIG, **config}
        except (json.JSONDecodeError, IOError):
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """Save configuration to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_model() -> str:
    """Get current model setting."""
    return load_config()["model"]


def set_model(model: str) -> None:
    """Set model preference."""
    config = load_config()
    config["model"] = model
    save_config(config)


def get_tone() -> str:
    """Get current tone setting."""
    return load_config()["tone"]


def set_tone(tone: str) -> None:
    """Set tone preference."""
    config = load_config()
    config["tone"] = tone
    save_config(config)


def reload_config() -> dict:
    """Force reload configuration from file. Returns the reloaded config."""
    return load_config()


def parse_inline_tone(text: str) -> tuple[str, str]:
    """
    Check if text starts with an inline tone prefix.
    Returns (tone_key, remaining_text) or (None, original_text).
    """
    text_lower = text.lower().lstrip()
    for prefix, tone_key in INLINE_PREFIXES.items():
        if text_lower.startswith(prefix):
            # Find the prefix in original text (case-insensitive position)
            prefix_end = len(prefix)
            # Skip whitespace after prefix
            remaining = text.lstrip()[prefix_end:].lstrip()
            return tone_key, remaining
    return None, text
