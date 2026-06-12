# AI Translator

A clean, modern desktop translation app powered by AI. Supports **Google Gemini** and **OpenRouter** (Llama, Mistral, Claude, GPT-4o Mini, and more).

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-green)

---

## Features

- **Three AI modes**: Translate, Summarize, and Improve text
- Translate between 55+ languages using AI (no dictionary-based translation)
- Summarize long texts into concise key-point summaries
- Improve text for clarity, grammar, flow, and readability
- Provider choice: **Gemini** or **OpenRouter** (multiple models)
- Auto-detect source language (Translate mode)
- Swap source ↔ target language and text with one click
- Copy output to clipboard
- Persistent settings storing in `~/.ai_translator_settings.json`
- API keys configurable via **Settings panel** or **environment variables**
- Clean dark-mode UI built with PySide6
- Non-blocking operations (run in background thread)
- Keyboard shortcut: **Ctrl+Enter** to process

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> Python 3.10+ recommended.

### 2. Get API keys

**Gemini** (free tier available):
- Go to https://aistudio.google.com/apikey
- Create a key and copy it

**OpenRouter** (many free models):
- Go to https://openrouter.ai/keys
- Create an account and generate a key

### 3. Configure API keys

**Option A – Environment variables (recommended for dev):**

```bash
# macOS / Linux
export GEMINI_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"

# Windows (PowerShell)
$env:GEMINI_API_KEY = "your-key-here"
$env:OPENROUTER_API_KEY = "your-key-here"
```

**Option B – Settings panel:**
- Launch the app, click the ⚙ gear icon in the top-right
- Enter your keys in the relevant tab and click Save

### 4. Run the app

```bash
python main.py
```

---

## Project structure

```
ai_translator/
├── main.py                  # Entry point
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── translator.py        # Gemini + OpenRouter API clients
│   └── settings.py          # Persistent settings (JSON)
└── ui/
    ├── __init__.py
    ├── main_window.py       # Main window, layout, translation flow
    └── settings_dialog.py   # Settings modal
```

---

## Keyboard shortcuts

| Shortcut       | Action            |
|----------------|-------------------|
| Ctrl+Enter     | Translate         |

---

## Possible improvements

- **Streaming output** – show translation token-by-token as it arrives
- **Translation history** – sidebar with past translations, searchable
- **Favorites / glossary** – pin term pairs for consistent translations
- **Detect language label** – show what language was auto-detected
- **System tray** – minimize to tray, translate clipboard contents via hotkey
- **Offline fallback** – bundle a tiny local model (e.g. NLLB via ctranslate2)
- **macOS `.app` bundle / Windows `.exe`** – package with PyInstaller or Nuitka
- **Themes** – light mode toggle
- **Font size controls** – accessibility adjustment for the text areas
