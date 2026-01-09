# Rephrase ✨

A Mac-wide text rephrasing tool powered by OpenAI. Select text anywhere, press **Ctrl+Option+R**, get it rephrased with proper grammar.

## Features

- 🌍 **Works everywhere** - Slack, email, browser, any app
- ⚡ **Fast** - Uses GPT-4o-mini by default for quick responses
- 🎨 **Multiple tones** - Professional, concise, friendly, or just fix grammar
- 🔐 **Secure** - API key stored in macOS Keychain
- 📝 **Inline overrides** - Prefix text with `formal:` or `concise:` for quick tone changes

---

## Prerequisites

- macOS (tested on Monterey and later)
- Python 3.9+ (we use pyenv to manage this)
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Homebrew ([Install here](https://brew.sh))

---

## Installation

### Step 1: Install pyenv (Python version manager)

We use pyenv to install Python 3.11 without affecting your system Python.

```bash
# Install pyenv via Homebrew
brew install pyenv

# Add pyenv to your shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Reload your shell
source ~/.zshrc
```

### Step 2: Install Python 3.11

```bash
# Install Python 3.11 (isolated, won't touch system Python)
pyenv install 3.11.9

# Verify installation
pyenv versions
```

### Step 3: Setup the project

```bash
# Create project directory
mkdir -p ~/Projects/rephrase
cd ~/Projects/rephrase

# Copy all project files here (or clone from repo)
# You should have: rephrase.py, config.py, api.py, clipboard_helper.py, 
#                  keychain_helper.py, logger.py, requirements.txt

# Set Python 3.11 for THIS project only
pyenv local 3.11.9

# Verify correct Python version
python --version  # Should show: Python 3.11.9

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Run the app

```bash
cd ~/Projects/rephrase
source venv/bin/activate
python rephrase.py
```

You should see:
```
INFO    | Starting Rephrase app...
DEBUG   | Hotkey listener started
INFO    | App initialized. Hotkey: Ctrl+Option+R
```

### Step 5: Set your OpenAI API key

1. Click the **✨** icon in your menubar
2. Click **"Set API Key..."**
3. Paste your OpenAI API key
4. Click OK

### Step 6: Grant macOS permissions

When you first run the app, macOS will ask for permissions. You need to grant:

#### Accessibility Permission (Required)
1. Go to **System Settings → Privacy & Security → Accessibility**
2. Find **Terminal** (or iTerm) in the list
3. Toggle it **ON**
4. If not listed, click **+** and add Terminal from Applications → Utilities

#### Input Monitoring Permission (Required)
1. Go to **System Settings → Privacy & Security → Input Monitoring**
2. Find **Terminal** (or iTerm) in the list
3. Toggle it **ON**

> ⚠️ **Important:** After granting permissions, restart the app for changes to take effect.

---

## Usage

### Basic Usage

1. **Select text** anywhere on your Mac (Slack, email, browser, Notes, etc.)
2. Press **Ctrl+Option+R**
3. Wait for the notification
4. Text is replaced with the rephrased version

### Inline Tone Overrides

Prefix your selected text to override the default tone:

| Prefix | Effect | Example |
|--------|--------|---------|
| `professional:` or `formal:` | Formal business tone | `formal: hey can u check this` |
| `concise:` or `short:` | Shorter, to the point | `concise: I wanted to follow up regarding the matter we discussed` |
| `friendly:` or `casual:` | Warm, casual tone | `friendly: Please review the document` |
| `grammar:` or `fix:` | Only fix grammar, minimal changes | `fix: i dont think this are correct` |

### Menubar Options

Click the **✨** icon to access:

| Option | Description |
|--------|-------------|
| **Status** | Shows Ready/Working |
| **Model** | Switch between gpt-4o-mini (fast) and gpt-4o (smarter) |
| **Default Tone** | Set your preferred rephrasing style |
| **Set API Key...** | Update your OpenAI API key |
| **Test Rephrase** | Test with sample text to verify setup |
| **View Logs** | Open logs folder for debugging |
| **Quit** | Stop the app |

---

## Configuration

Settings are stored in `~/.config/rephrase/config.json`:

```json
{
  "model": "gpt-4o-mini",
  "tone": "rephrase"
}
```

### Available Models

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `gpt-4o-mini` | ~0.5s | Cheaper | Daily use, quick fixes |
| `gpt-4o` | ~2s | Higher | Complex rewrites |

### Available Tones

| Tone | Description |
|------|-------------|
| `rephrase` | Fix grammar + improve clarity (default) |
| `grammar` | Only fix grammar, minimal changes |
| `professional` | Formal business tone |
| `concise` | Shorter, to the point |
| `friendly` | Warm, casual tone |

---

## Running on Startup (Optional)

### Option A: Simple Shell Script

Create `~/Projects/rephrase/start.sh`:

```bash
#!/bin/bash
cd ~/Projects/rephrase
source venv/bin/activate
python rephrase.py
```

Make it executable:
```bash
chmod +x ~/Projects/rephrase/start.sh
```

Add to **System Settings → General → Login Items** using Automator or manually run after login.

### Option B: Launch Agent (Recommended)

Create `~/Library/LaunchAgents/com.rephrase.app.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.rephrase.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ~/Projects/rephrase && source venv/bin/activate && python rephrase.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/rephrase.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/rephrase.error.log</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.rephrase.app.plist
```

Unload if needed:
```bash
launchctl unload ~/Library/LaunchAgents/com.rephrase.app.plist
```

---

## Troubleshooting

### "No text selected"

- Make sure you **select text first**, then press the hotkey
- Check Accessibility permissions are granted
- Try restarting the app after granting permissions

### Hotkey doesn't work

- Check **System Settings → Privacy & Security → Input Monitoring**
- Make sure Terminal is listed and enabled
- Restart Terminal and the app

### "API key not set"

- Click menubar **✨ → Set API Key...**
- Paste your OpenAI API key

### "This process is not trusted!"

This appears in the terminal when permissions aren't granted:
1. Grant Accessibility permission to Terminal
2. Grant Input Monitoring permission to Terminal
3. Restart the app

### Permissions dialog doesn't appear

Reset and try again:
```bash
tccutil reset Accessibility
tccutil reset InputMonitoring
```
Then restart the app and grant permissions when prompted.

### Check logs for errors

1. Click menubar **✨ → View Logs**
2. Open the latest log file
3. Look for ERROR or WARNING lines

Logs are stored in: `~/.config/rephrase/logs/`

### pyenv not working after terminal restart

Make sure these lines are in your `~/.zshrc`:
```bash
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

Then run:
```bash
source ~/.zshrc
```

---

## Project Structure

```
rephrase/
├── rephrase.py          # Main app - menubar + hotkey listener
├── config.py            # Model/tone configuration management
├── api.py               # OpenAI API calls
├── clipboard_helper.py  # Clipboard read/write + paste simulation
├── keychain_helper.py   # Secure API key storage in macOS Keychain
├── logger.py            # Logging configuration
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## Uninstall

1. Quit the app from menubar (**✨ → Quit**)

2. Remove the project folder:
```bash
rm -rf ~/Projects/rephrase
```

3. Remove API key from Keychain:
```bash
cd ~/Projects/rephrase
source venv/bin/activate
python -c "import keyring; keyring.delete_password('rephrase-app', 'openai-api-key')"
```

4. Remove config files:
```bash
rm -rf ~/.config/rephrase
```

5. Remove Launch Agent (if created):
```bash
launchctl unload ~/Library/LaunchAgents/com.rephrase.app.plist
rm ~/Library/LaunchAgents/com.rephrase.app.plist
```

---

## FAQ

**Q: Does this work with other AI providers?**  
A: Currently only OpenAI. Adding Claude/other providers is possible with code changes.

**Q: Is my text sent to OpenAI?**  
A: Yes, selected text is sent to OpenAI's API for processing. Don't use with sensitive/confidential data if that's a concern.

**Q: Can I change the hotkey?**  
A: Yes, edit `rephrase.py` and modify the key detection in `start_hotkey_listener()`.

**Q: Why Ctrl+Option+R instead of Cmd+Option+R?**  
A: Cmd+Option+R produces the `®` character on Mac, which causes detection issues.

---

## Credits

Built with:
- [rumps](https://github.com/jaredks/rumps) - macOS menubar apps in Python
- [pynput](https://github.com/moses-palmer/pynput) - Global hotkey detection
- [OpenAI API](https://platform.openai.com/) - Text processing
- [keyring](https://github.com/jaraco/keyring) - Secure credential storage
