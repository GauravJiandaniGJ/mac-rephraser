# PROGRESS.md - Development Session Summary

**Date:** 2026-01-11
**Session Focus:** Bug fixes, testing infrastructure, and stability improvements

---

## Completed Work

### 1. OpenAI Client Caching with Recreation
**Commit:** `a8ea9f1`

**Problem:** OpenAI client was created fresh on every API call (wasteful).

**Solution:**
- Added client caching in `api.py` with `_client` and `_client_api_key` globals
- `get_client()` returns cached client, auto-recreates if API key changes
- `recreate_client()` for manual recreation
- `reset_client()` for test isolation
- Added "Recreate OpenAI Client" menu item

**Files changed:** `api.py`, `rephrase.py`

---

### 2. Config File Re-reading
**Commit:** `9f2e633`

**Problem:** No way to reload config without restarting app.

**Solution:**
- Added `reload_config()` function in `config.py`
- Added "Reload Config" menu item that updates UI checkmarks
- Re-reads `~/.config/rephrase/config.json` from disk

**Files changed:** `config.py`, `rephrase.py`

---

### 3. Keychain Re-access
**Commit:** `99c3d47`

**Problem:** No way to refresh API key status from keychain.

**Solution:**
- Added "Refresh API Key Status" menu item
- Re-checks macOS Keychain and updates status display

**Files changed:** `rephrase.py`

---

### 4. Test Suite Implementation
**Commit:** `07c1a67`

**Problem:** No automated tests existed.

**Solution:**
- Created `test_rephraser.py` with 37 comprehensive tests
- Test coverage for: Config, API, Keychain, Clipboard, Logger, Integration
- Added `reset_client()` to `api.py` for test isolation

**Test classes:**
- `TestConfig` - 12 tests for configuration management
- `TestAPI` - 6 tests for OpenAI API integration
- `TestKeychain` - 4 tests for API key storage
- `TestClipboard` - 3 tests for clipboard operations
- `TestClipboardBugs` - 8 tests for clipboard edge cases
- `TestLogger` - 2 tests for logging
- `TestIntegration` - 2 tests for end-to-end flow

---

### 5. Clipboard Bug Fixes (TDD Approach)
**Commit:** `b3cdd77`

**Problems identified:**
1. Clipboard restoration could fail silently (crash)
2. 0.1s delay not enough for clipboard update
3. Whitespace-only selections treated as valid

**Solutions:**
- Added `_safe_clipboard_restore()` with exception handling
- Added retry logic (3 attempts × 100ms = up to 300ms)
- Whitespace-only selections now return `None`
- Added logging throughout clipboard operations

**Files changed:** `clipboard_helper.py`, `test_rephraser.py`

---

### 6. URGENT: Hotkey Firing Repeatedly
**Commit:** `506125b`

**Problem:** Hotkey triggered multiple times without user pressing, firing continuously.

**Root cause:**
- No debounce mechanism
- `pressed_keys` not cleared after firing
- Could re-trigger immediately

**Solution:**
- Added 1 second debounce (`DEBOUNCE_SECONDS = 1.0`)
- Clear `pressed_keys` after firing to prevent re-trigger
- Increased key release delay from 0.2s to 0.3s

**Files changed:** `rephrase.py`

---

### 7. URGENT: Cmd+C Not Working in Some Apps
**Commit:** `506125b`

**Problem:** "No text selected" even with text visibly selected (especially in Claude.ai web interface).

**Root cause:**
- `keystroke "c" using command down` doesn't work in all apps
- Electron apps and some web browsers ignore simulated keystrokes

**Solution:**
- Added fallback using Edit menu: `_try_copy_menu()`
- Flow: Try keystroke first → if fails, try menu "Edit > Copy"
- Increased retry delay from 100ms to 150ms per attempt
- Better null handling in subprocess results

**Files changed:** `clipboard_helper.py`

---

### 8. Mandatory Testing Rule
**Commit:** `f5705cd`

**Decision:** Always run tests before committing.

**Added to CLAUDE.md:**
```markdown
## MANDATORY RULES
1. ALWAYS run tests before committing
2. TDD approach for bug fixes
3. Update tests when changing functionality
```

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| 1s debounce for hotkey | Prevents accidental multiple triggers while still being responsive |
| Menu fallback for copy | More reliable across different app types (Electron, web, native) |
| Retry logic for clipboard | macOS clipboard updates are asynchronous, timing varies |
| Whitespace = no selection | Prevents API calls with empty/useless content |
| Client caching | Reduces overhead, but auto-recreates when API key changes |

---

## Commits This Session

```
f5705cd Add mandatory rule: always run tests before committing
506125b URGENT: Fix hotkey firing repeatedly and Cmd+C failures
b3cdd77 Fix clipboard bugs with TDD approach
07c1a67 Add test suite with 29 tests for all modules
99c3d47 Add keychain re-access with menu item
9f2e633 Add config file re-reading with menu item
a8ea9f1 Add OpenAI client caching with recreation capability
```

---

## Test Results

```
37 passed in ~1.3s
```

All tests passing as of last commit.

---

## Completed: Test Refactoring

### 9. Refactor Test Structure
**Commit:** `(pending)`
**Status:** Completed

Moved tests into a dedicated directory and split into separate files for better organization.

**New structure:**
```
rephraser/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures (reset_api_client, mock_subprocess, temp_config, etc.)
│   ├── test_config.py        # 12 tests - configuration management
│   ├── test_api.py           # 6 tests - OpenAI API integration
│   ├── test_keychain.py      # 4 tests - API key storage
│   ├── test_clipboard.py     # 11 tests - clipboard operations + bug tests
│   ├── test_logger.py        # 2 tests - logging configuration
│   └── test_integration.py   # 2 tests - end-to-end flow
```

**Changes made:**
1. Created `tests/` directory with `__init__.py`
2. Created `conftest.py` with shared fixtures:
   - `reset_api_client` - resets OpenAI client cache
   - `mock_subprocess` - mocks subprocess for clipboard tests
   - `temp_config` - temporary config directory
   - `mock_openai_response` - mock API response
   - `mock_keychain` - mock keychain operations
3. Split tests into 6 separate files by module
4. Removed old `test_rephraser.py`
5. Updated CLAUDE.md with new pytest command: `pytest tests/ -v`

**Test results:** 37 passed in ~1.3s

---

### 10. Seniority Modifier + Context Feature
**Commit:** `(pending)`
**Status:** Completed
**Spec:** [FEATURE_SENIORITY_CONTEXT.md](FEATURE_SENIORITY_CONTEXT.md)

**Summary:**
1. **Seniority Modifier** - Global setting (senior/mid/none) that makes ALL tones sound like selected level
2. **Context Feature** - Inline syntax `[context] text` for situational awareness

**Example:**
```
[client escalation] formal: fix this now
→ Senior voice + Professional tone + Context-aware response
```

**Implementation:**
- [x] Add SENIORITY_LEVELS to config.py
- [x] Add get_seniority() / set_seniority() functions
- [x] Add parse_context() function with nested bracket support
- [x] Modify api.py with build_system_prompt() for combined prompts
- [x] Add Seniority submenu to UI
- [x] Write tests (21 new tests added)
- [x] All 58 tests passing

**Files changed:**
- `config.py` - Added SENIORITY_LEVELS, parse_context(), get/set_seniority()
- `api.py` - Added build_system_prompt(), updated rephrase_text() flow
- `rephrase.py` - Added Seniority submenu, updated reload_config_file()
- `tests/test_config.py` - Added TestSeniority (4 tests), TestParseContext (9 tests)
- `tests/test_api.py` - Added TestBuildSystemPrompt (4 tests), TestRephraseSeniorityAndContext (4 tests)

**Test results:** 58 passed in ~1.2s

---

*Last updated: 2026-01-12*
