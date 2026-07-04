# Installing Rephrase

Rephrase lives in your menubar. Select text in any app, press **Ctrl + Option + R**, and the text is replaced with a polished version.

No Terminal, no Python, no git — just follow the steps below once.

## 1. Install the app

1. Download `Rephrase-x.y.z.dmg` (link shared by your team).
2. Double-click the `.dmg` and drag **Rephrase** into your **Applications** folder.
3. Eject the disk image.

## 2. First launch (one-time security step)

The app isn't notarized by Apple yet, so macOS blocks the first launch:

1. Double-click **Rephrase** in Applications. macOS will say it can't verify the app — click **Done** (don't move it to Trash).
2. Open **System Settings → Privacy & Security**, scroll down to the message about Rephrase, and click **"Open Anyway"**.
3. Confirm in the dialog that appears. This is only needed once.

## 3. Grant permissions

Rephrase needs two permissions to copy your selection and paste the result. macOS will prompt you; if a prompt doesn't appear, add Rephrase manually:

- **System Settings → Privacy & Security → Accessibility** → enable **Rephrase**
- **System Settings → Privacy & Security → Input Monitoring** → enable **Rephrase**

Also click **OK** on the one-time *"Rephrase wants to control System Events"* prompt.

> If you granted a permission while the app was running, quit Rephrase (menubar icon → Quit) and open it again.

## 4. Enter your OpenAI API key

On first launch Rephrase shows a setup dialog asking for your OpenAI API key. Paste it and press OK — it's stored securely in your macOS Keychain, never in a file.

To change it later: click the **R✎** menubar icon → **Set API Key…**

## 5. Use it

1. Select some text anywhere (Slack, Mail, browser…).
2. Press **Ctrl + Option + R**.
3. Wait a moment — the selection is replaced with the rephrased text.

Tips (type these at the start of your selection):
- `fix:` — grammar fixes only
- `formal:` — professional tone
- `short:` — more concise
- `casual:` — friendly tone
- `[some context] your text` — give the AI context, e.g. `[reply to my manager] can't make it today`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Hotkey does nothing | Check Accessibility **and** Input Monitoring are enabled for Rephrase, then quit and reopen the app |
| "No text selected" | Make sure text is highlighted before pressing the hotkey |
| "API key not set" | Menubar icon → Set API Key… |
| Nothing in the menubar | Look for **R✎** on the right side of the menubar; if missing, reopen the app from Applications |
| Still stuck | Menubar icon → View Logs, and send the latest log file to whoever shared the app |
