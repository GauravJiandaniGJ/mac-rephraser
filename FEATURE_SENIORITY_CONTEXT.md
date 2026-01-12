# Feature: Seniority Modifier + Context

**Status:** Planned
**Created:** 2026-01-12
**Author:** User + Claude

---

## Problem Statement

As a senior engineer/tech lead, rephrased messages should reflect seniority level - confident, authoritative, direct but respectful. Additionally, context about the situation (e.g., "client escalation", "code review") would help produce more appropriate rephrases.

**Time saved calculation:**
- ~20 seconds per message to rephrase
- 100 messages/day = 33 minutes/day
- 33 × 30 days = 16.5 hours/month
- **2 entire working days per month** spent on rephrasing

---

## Solution

### 1. Seniority Modifier

A global setting that modifies ALL tones to sound like the selected seniority level.

**Options:**
| Level | Description |
|-------|-------------|
| `senior` | Senior/Lead - Confident, authoritative, direct but respectful |
| `mid` | Mid-Level - Professional and collaborative |
| `none` | No modification (current behavior) |

**How it works:**
- Stored in config.json alongside model/tone
- Menubar submenu to select (like Model/Tone menus)
- Injected as a prefix to ALL tone prompts

**Senior Modifier Prompt:**
```
You are writing as a senior engineer or tech lead. Use confident,
authoritative language. Be direct but respectful. Show technical
depth without being condescending.
```

### 2. Context Feature

Inline syntax to provide situational context for better rephrasing.

**Syntax:** `[context here] text to rephrase`

**Examples:**
```
[replying to angry client] fix this asap
→ "I understand your frustration. We're prioritizing this fix and will have it resolved shortly."

[Q4 planning meeting] let's defer this to next sprint
→ "Given our Q4 priorities, I recommend we schedule this for the next sprint."

[code review feedback] this approach won't scale
→ "This implementation may face scalability challenges as load increases. Consider..."

[standup update] blocked on API team
→ "Currently blocked pending API team's response. Following up today."
```

**How it works:**
- Parsed before inline tone prefix
- Extracted and sent as additional context in system prompt
- Works with any tone

### 3. Combined Usage

All features can be combined:

```
[client escalation] formal: fix this now
```

**Processing order:**
1. Parse context: `[client escalation]` → context
2. Parse tone prefix: `formal:` → professional tone
3. Get seniority: `senior` (from config)
4. Build prompt: Senior modifier + Professional tone + Context
5. Rephrase: "fix this now"

**Result:** A senior-sounding, professional response aware of client escalation context.

---

## Technical Design

### Config Changes (`config.py`)

```python
SENIORITY_LEVELS = {
    "senior": {
        "name": "Senior/Lead",
        "modifier": "You are writing as a senior engineer or tech lead..."
    },
    "mid": {
        "name": "Mid-Level",
        "modifier": "You are writing as a mid-level engineer..."
    },
    "none": {
        "name": "None",
        "modifier": ""
    }
}

DEFAULT_CONFIG = {
    "model": "gpt-4o-mini",
    "tone": "rephrase",
    "seniority": "none"  # NEW
}

def get_seniority() -> str: ...
def set_seniority(seniority: str) -> None: ...
def parse_context(text: str) -> tuple[str | None, str]: ...
```

### API Changes (`api.py`)

```python
def rephrase_text(text: str) -> str:
    # 1. Parse context from text
    context, text = parse_context(text)

    # 2. Parse inline tone
    inline_tone, clean_text = parse_inline_tone(text)
    tone_key = inline_tone or get_tone()

    # 3. Build system prompt
    tone_prompt = TONES[tone_key]["prompt"]
    seniority_modifier = SENIORITY_LEVELS[get_seniority()]["modifier"]

    system_prompt = tone_prompt
    if seniority_modifier:
        system_prompt = f"{seniority_modifier}\n\n{system_prompt}"
    if context:
        system_prompt += f"\n\nContext: {context}"

    # 4. Call API with combined prompt
    ...
```

### UI Changes (`rephrase.py`)

```python
# Add Seniority submenu (like Model/Tone menus)
self.seniority_menu = rumps.MenuItem("Seniority")
current_seniority = get_seniority()
for level_key, level_config in SENIORITY_LEVELS.items():
    item = rumps.MenuItem(
        level_config["name"],
        callback=lambda sender, s=level_key: self.select_seniority(s, sender)
    )
    if level_key == current_seniority:
        item.state = 1
    self.seniority_menu.add(item)
```

---

## Implementation Checklist

- [ ] Add SENIORITY_LEVELS to config.py
- [ ] Add get_seniority() / set_seniority() functions
- [ ] Add parse_context() function
- [ ] Update DEFAULT_CONFIG with seniority field
- [ ] Modify api.py to build combined prompts
- [ ] Add Seniority submenu to rephrase.py
- [ ] Add reload support for seniority in reload_config_file()
- [ ] Write tests for parse_context()
- [ ] Write tests for seniority config functions
- [ ] Write tests for combined prompt building
- [ ] Write integration tests
- [ ] Manual testing
- [ ] Update PROGRESS.md

---

## Test Cases

### parse_context()
```python
# Basic context
parse_context("[meeting notes] hello") → ("meeting notes", "hello")

# No context
parse_context("just text") → (None, "just text")

# Context with tone prefix
parse_context("[urgent] formal: fix this") → ("urgent", "formal: fix this")

# Empty brackets (edge case)
parse_context("[] text") → (None, "[] text")  # or ("", "text")?

# Nested brackets (edge case)
parse_context("[foo [bar]] text") → ("foo [bar]", "text")
```

### Seniority Config
```python
# Default
get_seniority() → "none"

# Set and get
set_seniority("senior")
get_seniority() → "senior"
```

### Prompt Building
```python
# Senior + Professional + Context
# Should produce combined prompt with all three elements
```

---

## Future Enhancements

- [ ] Custom seniority prompts (user-defined)
- [ ] Context history (remember recent contexts)
- [ ] Context suggestions based on app/window
- [ ] Seniority presets per app (Slack vs Email)
