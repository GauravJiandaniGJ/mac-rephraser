"""OpenAI API integration for text rephrasing."""

from openai import OpenAI

from config import (
    TONES,
    SENIORITY_LEVELS,
    get_model,
    get_tone,
    get_seniority,
    parse_inline_tone,
    parse_context,
)
from keychain_helper import get_api_key
from logger import log


class RephraseError(Exception):
    """Custom exception for rephrase errors."""
    pass


# Cached OpenAI client
_client: OpenAI | None = None
_client_api_key: str | None = None


def get_client() -> OpenAI:
    """Get or create the OpenAI client. Creates new client if API key changed."""
    global _client, _client_api_key

    api_key = get_api_key()
    if not api_key:
        raise RephraseError("API key not set. Click menubar icon → Set API Key")

    # Recreate client if key changed or client doesn't exist
    if _client is None or _client_api_key != api_key:
        log.info("Creating new OpenAI client")
        _client = OpenAI(api_key=api_key)
        _client_api_key = api_key

    return _client


def recreate_client() -> bool:
    """Force recreation of the OpenAI client. Returns True if successful."""
    global _client, _client_api_key

    api_key = get_api_key()
    if not api_key:
        log.warning("Cannot recreate client: no API key set")
        return False

    log.info("Forcing OpenAI client recreation")
    _client = OpenAI(api_key=api_key)
    _client_api_key = api_key
    return True


def reset_client() -> None:
    """Reset the cached client. Used for testing."""
    global _client, _client_api_key
    _client = None
    _client_api_key = None


def build_system_prompt(tone_key: str, seniority_key: str, context: str | None) -> str:
    """
    Build the system prompt by combining tone, seniority modifier, and context.

    Order: Seniority modifier → Tone prompt → Context
    """
    tone_config = TONES.get(tone_key, TONES["rephrase"])
    seniority_config = SENIORITY_LEVELS.get(seniority_key, SENIORITY_LEVELS["none"])

    # Start with tone prompt
    prompt = tone_config["prompt"]

    # Prepend seniority modifier if set
    seniority_modifier = seniority_config.get("modifier", "")
    if seniority_modifier:
        prompt = f"{seniority_modifier}\n\n{prompt}"

    # Append context if provided
    if context:
        prompt = f"{prompt}\n\nContext: {context}"

    return prompt


def rephrase_text(text: str) -> str:
    """
    Rephrase the given text using OpenAI API.

    Processing order:
    1. Parse context from [brackets]
    2. Parse inline tone prefix
    3. Get seniority setting
    4. Build combined system prompt
    5. Call API

    Returns the rephrased text.
    Raises RephraseError on failure.
    """
    # Step 1: Parse context from [brackets]
    context, text_after_context = parse_context(text)

    # Step 2: Check for inline tone override
    inline_tone, clean_text = parse_inline_tone(text_after_context)
    tone_key = inline_tone if inline_tone else get_tone()

    if not clean_text.strip():
        raise RephraseError("No text to rephrase")

    # Step 3: Get seniority setting
    seniority_key = get_seniority()

    # Step 4: Build combined system prompt
    system_prompt = build_system_prompt(tone_key, seniority_key, context)
    model = get_model()

    log.debug(f"Rephrasing with tone={tone_key}, seniority={seniority_key}, context={context}")

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
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
