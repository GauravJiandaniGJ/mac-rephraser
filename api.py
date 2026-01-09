"""OpenAI API integration for text rephrasing."""

from openai import OpenAI

from config import TONES, get_model, get_tone, parse_inline_tone
from keychain_helper import get_api_key


class RephraseError(Exception):
    """Custom exception for rephrase errors."""
    pass


def rephrase_text(text: str) -> str:
    """
    Rephrase the given text using OpenAI API.
    
    Checks for inline tone prefixes first, falls back to configured tone.
    Returns the rephrased text.
    Raises RephraseError on failure.
    """
    api_key = get_api_key()
    if not api_key:
        raise RephraseError("API key not set. Click menubar icon → Set API Key")
    
    # Check for inline tone override
    inline_tone, clean_text = parse_inline_tone(text)
    tone_key = inline_tone if inline_tone else get_tone()
    
    if not clean_text.strip():
        raise RephraseError("No text to rephrase")
    
    tone_config = TONES.get(tone_key, TONES["rephrase"])
    model = get_model()
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": tone_config["prompt"]},
                {"role": "user", "content": clean_text},
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=2048,
        )
        
        result = response.choices[0].message.content
        if not result:
            raise RephraseError("Empty response from API")
        
        return result.strip()
    
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            raise RephraseError("Invalid API key")
        elif "rate_limit" in error_msg.lower():
            raise RephraseError("Rate limited. Try again in a moment")
        elif "timeout" in error_msg.lower():
            raise RephraseError("Request timed out")
        else:
            raise RephraseError(f"API error: {error_msg[:50]}")
