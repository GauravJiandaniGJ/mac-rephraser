# Mac Rephraser ✎

A Mac-wide text rephrasing tool built by a senior engineer who got tired of wasting 16+ hours a month on copy-paste gymnastics.

Select text anywhere → Press **Ctrl+Option+R** → Done.

![Demo](assets/demo.gif)

---

## The Problem I Solved

After 10+ years of building software for clients, I noticed something embarrassing: I was spending more time *formatting* messages than *writing* them.

Every Slack message, every email, every client update followed the same ritual:

```
Write → Copy → Open ChatGPT → Paste → "Rephrase this professionally" →
Wait → Copy → Switch back → Paste → Tweak → Send
```

**6 context switches. For a single message.**

I timed it: **~20 seconds per message.**

### The Math That Made Me Build This

| Metric | Value |
|--------|-------|
| Messages per day | ~100 (across Slack, email, PRs) |
| Time per message | 20 seconds |
| Days per month | 30 |
| **Total time wasted** | **16.5 hours/month** |

That's **two full workdays** every month spent on copy-paste-wait-copy-paste.

As an engineer, I knew I could fix this in a day. So I did.

---

## The Solution: One Hotkey

Now my workflow is:

```
Write → Select → Ctrl+Option+R → Send
```

**2 seconds instead of 20.** No tab switching. No waiting. No breaking flow.

---

## Features

- 🌍 **Works everywhere** - Slack, email, browser, any Mac app
- ⚡ **Fast** - Uses GPT-4o-mini by default (~0.5s response)
- 🎨 **Multiple tones** - Professional, concise, friendly, or just fix grammar
- 🔐 **Secure** - API key stored in macOS Keychain (not in files)
- 📝 **Inline overrides** - Prefix with `formal:` or `concise:` for quick tone changes

---

## Quick Start

### Prerequisites

- macOS (Monterey or later)
- Python 3.9+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

```bash
# Clone the repo
git clone https://github.com/gauravjiandani/mac-rephraser.git
cd mac-rephraser

# If you have Python 3.9+, skip to next section
# Otherwise, install via pyenv:
brew install pyenv
pyenv install 3.11.9
pyenv local 3.11.9

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run
python rephrase.py
```

### Setup

1. Click the **R✎** icon in your menubar
2. Click **"Set API Key..."** → paste your OpenAI key
3. Grant **Accessibility** and **Input Monitoring** permissions when prompted
4. Restart the app after granting permissions

---

## Usage

1. **Select text** anywhere (Slack, email, browser, Notes...)
2. Press **Ctrl+Option+R**
3. Wait for notification (~1 second)
4. Text is replaced with the rephrased version ✨

### Inline Tone Overrides

Prefix your text to change the tone on-the-fly:

| Prefix | Effect |
|--------|--------|
| `formal:` | Professional business tone |
| `concise:` | Shorter, to the point |
| `friendly:` | Warm, casual tone |
| `grammar:` | Only fix grammar, minimal changes |

**Example:** Select `formal: hey can u review this` → becomes professional.

### Menu Options

Click **R✎** in menubar:

- **Model** - Switch between `gpt-4o-mini` (fast) and `gpt-4o` (smarter)
- **Default Tone** - Set your preferred style
- **Test Rephrase** - Verify setup works
- **View Logs** - Debug issues

---

## macOS Permissions

The app needs these permissions to work (it reads keypresses and simulates copy/paste):

| Permission | Where to Grant |
|------------|----------------|
| **Accessibility** | System Settings → Privacy & Security → Accessibility → Enable Terminal |
| **Input Monitoring** | System Settings → Privacy & Security → Input Monitoring → Enable Terminal |

> ⚠️ Restart the app after granting permissions

---

## Configuration

Settings stored in `~/.config/rephrase/config.json`:

```json
{
  "model": "gpt-4o-mini",
  "tone": "rephrase"
}
```

API key stored securely in **macOS Keychain** (not in any file).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Hotkey doesn't work | Grant Input Monitoring permission, restart app |
| "No text selected" | Grant Accessibility permission, restart app |
| "API key not set" | Click menubar → Set API Key |
| "This process is not trusted!" | Grant both permissions above |

**View logs:** Click menubar → View Logs (or check `~/.config/rephrase/logs/`)

---

## Project Structure

```
mac-rephraser/
├── rephrase.py          # Main app (menubar + hotkey)
├── config.py            # Settings management
├── api.py               # OpenAI integration
├── clipboard_helper.py  # Copy/paste simulation
├── keychain_helper.py   # Secure API key storage
├── logger.py            # Debug logging
├── requirements.txt     # Dependencies
└── README.md
```

---

## Run on Startup (Optional)

Create `~/Library/LaunchAgents/com.macrephraser.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.macrephraser</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd ~/Projects/mac-rephraser && source venv/bin/activate && python rephrase.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Load: `launchctl load ~/Library/LaunchAgents/com.macrephraser.plist`

---

## Contributing

Found a bug? Have an idea? [Open an issue](https://github.com/gauravjiandani/mac-rephraser/issues)!

Want Windows/Linux support? Let me know by opening an issue - if there's enough demand, I'll consider it.

---

## License

MIT © [Gaurav Jiandani](https://gauravjiandani.com)

---

## Author

**Gaurav Jiandani**
- Website: [gauravjiandani.com](https://gauravjiandani.com)
- GitHub: [@gauravjiandani](https://github.com/gauravjiandani)

Built with ☕ and frustration at copy-pasting to ChatGPT.


<!-- Security scan triggered at 2026-09-02 06:50:24 -->