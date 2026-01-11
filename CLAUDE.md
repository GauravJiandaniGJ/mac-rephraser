# CLAUDE.md - Claude Code Instructions for mac-rephraser

## MANDATORY RULES

**These rules MUST be followed for every code change:**

1. **ALWAYS run tests before committing:**
   ```bash
   source venv/bin/activate && pytest tests/ -v
   ```
   - All tests must pass before any `git commit`
   - If tests fail, fix the issues first
   - Never skip this step, even for "small" changes

2. **Test-Driven Development (TDD) for bug fixes:**
   - Write a failing test that reproduces the bug first
   - Then fix the bug
   - Verify the test passes

3. **Update tests when changing functionality:**
   - If you modify existing behavior, update relevant tests
   - If you add new features, add new tests

---

## Project Overview

**mac-rephraser** is a macOS menubar application that rephrases selected text using OpenAI's API. Users select text anywhere on their Mac, press `Ctrl+Option+R`, and the text gets replaced with a polished version.

### Tech Stack
- **Language:** Python 3.11+
- **UI:** rumps (macOS menubar)
- **Hotkey:** pynput (global keyboard listener)
- **AI:** OpenAI API (gpt-4o-mini default)
- **Security:** macOS Keychain via keyring
- **Clipboard:** pyperclip + osascript

### File Structure
```
mac-rephraser/
├── rephrase.py          # Main app - menubar + hotkey listener
├── config.py            # Settings management (model, tone)
├── api.py               # OpenAI API integration
├── clipboard_helper.py  # Copy/paste simulation via osascript
├── keychain_helper.py   # Secure API key storage
├── logger.py            # Debug logging to ~/.config/rephrase/logs/
├── requirements.txt     # Dependencies
├── README.md            # User documentation
├── LICENSE              # MIT License
├── tests/               # Test suite
│   ├── conftest.py      # Shared fixtures
│   ├── test_api.py      # API tests
│   ├── test_clipboard.py # Clipboard tests
│   ├── test_config.py   # Config tests
│   ├── test_integration.py # Integration tests
│   ├── test_keychain.py # Keychain tests
│   └── test_logger.py   # Logger tests
└── assets/
    └── demo.gif         # Demo for README
```

---

## Agents and Their Best Uses

### 1. **Code Agent** (Default)
Best for: Writing new features, fixing bugs, refactoring

```
Use for:
- Adding new tone options
- Implementing new hotkey combinations
- Fixing clipboard issues
- Adding new AI providers (Claude, Gemini, etc.)
```

### 2. **Review Agent**
Best for: Code review, security audit, best practices

```
Prompt examples:
- "Review api.py for security issues with API key handling"
- "Review clipboard_helper.py for edge cases"
- "Check if there are any memory leaks in the hotkey listener"
```

### 3. **Debug Agent**
Best for: Troubleshooting issues, analyzing logs

```
Prompt examples:
- "Why might the hotkey not trigger on some apps?"
- "Debug why notifications stopped appearing"
- "Analyze this log output and find the issue: [paste logs]"
```

### 4. **Docs Agent**
Best for: Documentation, comments, README updates

```
Prompt examples:
- "Add docstrings to all functions in rephrase.py"
- "Update README with new feature X"
- "Create CONTRIBUTING.md for open source contributors"
```

### 5. **Test Agent**
Best for: Writing tests, test coverage

```
Prompt examples:
- "Write unit tests for config.py"
- "Create integration tests for the API module"
- "Add pytest fixtures for testing"
```

---

## Common Tasks & Prompts

### Adding a New Tone

```
Add a new tone called "technical" that rephrases text for developer documentation.
Update config.py with the new tone and its system prompt.
```

### Adding a New AI Provider

```
Add support for Anthropic's Claude API as an alternative to OpenAI.
- Add provider selection in config.py
- Create claude_api.py similar to api.py
- Update menubar to allow switching providers
- Store Claude API key separately in keychain
```

### Fixing Hotkey Issues

```
The hotkey Ctrl+Option+R is not being detected in [specific app].
Debug the pynput listener and suggest fixes.
Check if it's a permission issue or key detection issue.
```

### Adding New Features

```
Add a feature to show the last 5 rephrased texts in the menubar menu,
so users can quickly copy a previous result if needed.
```

```
Add a "Preview" mode where instead of replacing text directly,
it shows the rephrased text in a popup for user to confirm.
```

```
Add usage tracking - count how many times the tool has been used
and show it in the menubar menu.
```

### Performance Improvements

```
Optimize the hotkey listener to use less CPU when idle.
Currently it's checking every keypress - can we make it more efficient?
```

### Cross-Platform Exploration

```
What would need to change to make this work on Windows?
Create a detailed technical plan without implementing yet.
```

---

## Agent Combinations for Complex Tasks

### New Feature (Full Cycle)
```
1. Code Agent: Implement the feature
2. Review Agent: Review for bugs and security
3. Test Agent: Write tests
4. Docs Agent: Update README
```

### Bug Fix (Full Cycle)
```
1. Debug Agent: Identify root cause
2. Code Agent: Implement fix
3. Test Agent: Add regression test
4. Review Agent: Verify fix doesn't break anything
```

### Refactoring
```
1. Review Agent: Identify code smells
2. Code Agent: Refactor
3. Test Agent: Ensure tests still pass
4. Review Agent: Final review
```

---

## Project-Specific Context

### macOS Permissions Required
- **Accessibility:** For simulating Cmd+C and Cmd+V
- **Input Monitoring:** For global hotkey detection

### Key Technical Decisions
1. **Why osascript for clipboard?** More reliable than pure Python on macOS
2. **Why pynput over pyobjc?** Simpler API, cross-platform potential
3. **Why keyring for API key?** Secure, uses native macOS Keychain
4. **Why rumps for menubar?** Lightweight, Pythonic, easy to use

### Known Limitations
- Only works on macOS (pynput + rumps + osascript)
- Requires Python 3.9+ (PyObjC dependency)
- Hotkey `Ctrl+Option+R` chosen because `Cmd+Option+R` produces `®`
- Needs 0.2s delay after hotkey to let user release keys before Cmd+C

### Configuration Locations
- **Config file:** `~/.config/rephrase/config.json`
- **Logs:** `~/.config/rephrase/logs/`
- **API Key:** macOS Keychain (service: `rephrase-app`)

---

## Running the Project

### First Time Setup
```bash
# Clone
git clone https://github.com/gauravjiandani/mac-rephraser.git
cd mac-rephraser

# Setup Python (if needed)
pyenv install 3.11.9
pyenv local 3.11.9

# Create venv
python -m venv venv
source venv/bin/activate

# Install deps
pip install --upgrade pip
pip install -r requirements.txt

# Run
python rephrase.py
```

### Daily Development
```bash
cd mac-rephraser
source venv/bin/activate
python rephrase.py
```

### View Logs
```bash
cat ~/.config/rephrase/logs/rephrase_$(date +%Y-%m-%d).log
```

### Reset Configuration
```bash
rm -rf ~/.config/rephrase
python -c "import keyring; keyring.delete_password('rephrase-app', 'openai-api-key')"
```

---

## Code Style Guidelines

- **Formatting:** Follow PEP 8
- **Imports:** Standard library → Third party → Local (separated by blank lines)
- **Logging:** Use `log.debug()`, `log.info()`, `log.warning()`, `log.error()`
- **Error handling:** Catch specific exceptions, log them, show user-friendly notifications
- **Type hints:** Use them for function signatures

---

## Quick Reference

| Task | Command/Location |
|------|------------------|
| Run app | `python rephrase.py` |
| View logs | `~/.config/rephrase/logs/` |
| Edit config | `~/.config/rephrase/config.json` |
| API key | macOS Keychain → "rephrase-app" |
| Main logic | `rephrase.py` → `do_rephrase()` |
| Hotkey setup | `rephrase.py` → `start_hotkey_listener()` |
| API call | `api.py` → `rephrase_text()` |
| Tones | `config.py` → `TONES` dict |

---

## Future Ideas (Backlog)

- [ ] Add Claude API support
- [ ] Add local LLM support (Ollama)
- [ ] Preview mode before replacing
- [ ] History of last N rephrases
- [ ] Custom hotkey configuration
- [ ] Usage statistics
- [ ] Auto-update mechanism
- [ ] Package as .app with py2app
- [ ] Windows support
- [ ] Sync settings across devices
