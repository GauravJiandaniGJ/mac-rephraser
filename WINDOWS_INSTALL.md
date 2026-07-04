# Installing Rephrase (Windows)

Rephrase lives in your system tray. Select text in any app, press
**Ctrl + Alt + R**, and the text is replaced with a polished version.

## 1. Install

1. Download `Rephrase-x.y.z.exe` (link shared by your team).
2. Move it somewhere permanent (e.g. `Documents\Rephrase\`) and double-click it.
3. **SmartScreen warning**: Windows will say "Windows protected your PC" because
   the app isn't code-signed. Click **More info → Run anyway**. This is only
   needed the first time.
4. Look for the **R** icon in the system tray (bottom-right, may be hidden
   behind the ^ arrow — drag it out to keep it visible).

## 2. Enter your OpenAI API key

On first launch Rephrase shows a setup dialog asking for your OpenAI API key.
Paste it and press OK — it's stored securely in Windows Credential Manager,
never in a file.

To change it later: right-click the tray icon → **Set API Key…**

## 3. Use it

1. Select some text anywhere (Slack, Outlook, browser…).
2. Press **Ctrl + Alt + R**.
3. Wait a moment — the selection is replaced with the rephrased text.

Tips (type these at the start of your selection):
- `fix:` — grammar fixes only
- `formal:` — professional tone
- `short:` — more concise
- `casual:` — friendly tone
- `[some context] your text` — give the AI context, e.g. `[reply to my manager] can't make it today`

## Optional: start automatically at login

1. Press **Win + R**, type `shell:startup`, press Enter.
2. Right-click drag `Rephrase.exe` into that folder and choose
   **Create shortcuts here**.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Hotkey does nothing in one specific app | If that app runs as Administrator, Windows blocks the hotkey — either run that app normally, or run Rephrase as Administrator too |
| "No text selected" | Make sure text is highlighted before pressing the hotkey; some apps (Office) are slow — try again |
| "API key not set" | Tray icon → Set API Key… |
| No tray icon | Check the hidden-icons arrow (^) in the tray; if truly missing, launch the exe again |
| Still stuck | Tray icon → Open Logs Folder, send the latest log to whoever shared the app |
