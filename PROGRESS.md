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

## TODO: Future Tasks

### Refactor Test Structure
**Priority:** Medium
**Status:** Pending

Move tests into a dedicated directory and split into separate files for better organization and maintainability.

**Current structure:**
```
rephraser/
├── test_rephraser.py    # All 37 tests in one file
```

**Target structure:**
```
rephraser/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   ├── test_config.py        # TestConfig class
│   ├── test_api.py           # TestAPI class
│   ├── test_keychain.py      # TestKeychain class
│   ├── test_clipboard.py     # TestClipboard + TestClipboardBugs classes
│   ├── test_logger.py        # TestLogger class
│   └── test_integration.py   # TestIntegration class
```

**Steps:**
1. Create `tests/` directory
2. Create `conftest.py` with shared fixtures (mock_subprocess, reset_api_client)
3. Move each test class to its own file
4. Update imports in each test file
5. Remove old `test_rephraser.py`
6. Update pytest command in CLAUDE.md if needed
7. Run tests to verify everything works

---

*Last updated: 2026-01-11*
