"""
translator.py
Core translation logic for Gemini and OpenRouter API providers.
Framework-agnostic — works with any Python frontend.
"""

import json
import urllib.request
import urllib.error
from typing import Optional


# ── Mode registry ─────────────────────────────────────────────────────────────

MODES = ["Translate", "Summarize", "Improve"]

# ── Language registry ────────────────────────────────────────────────────────

LANGUAGES = {
    "Auto-detect": "auto",
    "Afrikaans": "af",
    "Arabic": "ar",
    "Bengali": "bn",
    "Bulgarian": "bg",
    "Catalan": "ca",
    "Chinese (Simplified)": "zh",
    "Chinese (Traditional)": "zh-TW",
    "Croatian": "hr",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "English": "en",
    "Estonian": "et",
    "Finnish": "fi",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Gujarati": "gu",
    "Hebrew": "he",
    "Hindi": "hi",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Kannada": "kn",
    "Korean": "ko",
    "Latvian": "lv",
    "Lithuanian": "lt",
    "Malay": "ms",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Norwegian": "no",
    "Persian": "fa",
    "Polish": "pl",
    "Portuguese": "pt",
    "Punjabi": "pa",
    "Romanian": "ro",
    "Russian": "ru",
    "Serbian": "sr",
    "Slovak": "sk",
    "Slovenian": "sl",
    "Spanish": "es",
    "Swahili": "sw",
    "Swedish": "sv",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Vietnamese": "vi",
    "Welsh": "cy",
}

LANGUAGE_NAMES = list(LANGUAGES.keys())


# ── Prompt builders ───────────────────────────────────────────────────────────

def build_translate_prompt(text: str, source_lang: str, target_lang: str) -> str:
    if source_lang == "Auto-detect":
        src_clause = "the source language (auto-detect it)"
    else:
        src_clause = source_lang
    return (
        f"Translate the following text from {src_clause} to {target_lang}. "
        "Output ONLY the translated text — no explanations, no quotation marks, "
        "no additional commentary.\n\n"
        f"{text}"
    )


def build_summarize_prompt(text: str, target_lang: str = "") -> str:
    lang_clause = f" Write the summary in {target_lang}." if target_lang and target_lang != "Auto-detect" else ""
    return (
        "Summarize the following text concisely while preserving all key points and facts."
        f"{lang_clause} "
        "Output ONLY the summary — no explanations, no quotation marks, "
        "no additional commentary.\n\n"
        f"{text}"
    )


def build_improve_prompt(text: str, target_lang: str = "") -> str:
    lang_clause = f" Return the improved text in {target_lang}." if target_lang and target_lang != "Auto-detect" else ""
    return (
        "Improve the following text for clarity, grammar, flow, and readability. "
        f"Preserve the original meaning and tone.{lang_clause} "
        "Output ONLY the improved text — no explanations, no quotation marks, "
        "no additional commentary.\n\n"
        f"{text}"
    )


# ── Base / error ──────────────────────────────────────────────────────────────

class TranslationError(Exception):
    """Raised when a translation attempt fails for any reason."""


class BaseTranslator:
    @staticmethod
    def _http_post(url: str, headers: dict, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise TranslationError(f"HTTP {exc.code} – {exc.reason}\n{body}") from exc
        except urllib.error.URLError as exc:
            raise TranslationError(f"Network error: {exc.reason}") from exc


# ── Gemini ────────────────────────────────────────────────────────────────────

GEMINI_MODELS = {
    "gemini-2.0-flash-lite": "Gemini 2.0 Flash-Lite (Fast, Free Tier)",
    "gemini-2.0-flash":      "Gemini 2.0 Flash (Balanced)",
    "gemini-2.5-flash":      "Gemini 2.5 Flash (Latest Fast)",
    "gemini-2.5-pro":        "Gemini 2.5 Pro (Most Capable)",
    "gemini-1.5-flash":      "Gemini 1.5 Flash (Stable)",
}
GEMINI_MODEL_NAMES = list(GEMINI_MODELS.keys())


class GeminiTranslator(BaseTranslator):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-lite"):
        if not api_key:
            raise TranslationError(
                "Gemini API key mancante. Inseriscila nel pannello ⚙ Impostazioni."
            )
        self.api_key = api_key
        self.model = model

    def run(self, prompt: str) -> str:
        url = self.BASE_URL.format(model=self.model) + f"?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
        }
        result = self._http_post(url, {"Content-Type": "application/json"}, payload)
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as exc:
            raise TranslationError(f"Risposta Gemini inattesa:\n{result}") from exc


# ── OpenRouter ────────────────────────────────────────────────────────────────

OPENROUTER_MODELS = {
    "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B Instruct",
    "mistralai/mistral-7b-instruct":     "Mistral 7B Instruct",
    "anthropic/claude-3-haiku":          "Claude 3 Haiku",
    "openai/gpt-4o-mini":                "GPT-4o Mini",
    "google/gemma-3-27b-it:free":        "Gemma 3 27B (Free)",
    "deepseek/deepseek-chat":            "DeepSeek Chat",
}
OPENROUTER_MODEL_NAMES = list(OPENROUTER_MODELS.keys())


class OpenRouterTranslator(BaseTranslator):
    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.3-70b-instruct"):
        if not api_key:
            raise TranslationError(
                "OpenRouter API key mancante. Inseriscila nel pannello ⚙ Impostazioni."
            )
        self.api_key = api_key
        self.model = model

    def run(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://ai-translator-streamlit",
            "X-Title": "AI Translator",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 4096,
        }
        result = self._http_post(self.API_URL, headers, payload)
        try:
            return result["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise TranslationError(f"Risposta OpenRouter inattesa:\n{result}") from exc


# ── Unified entry point ───────────────────────────────────────────────────────

def process(
    text: str,
    mode: str,
    provider: str,
    gemini_key: str,
    openrouter_key: str,
    gemini_model: str,
    openrouter_model: str,
    source_lang: str = "Auto-detect",
    target_lang: str = "English",
    output_lang: str = "",
) -> str:
    """
    Single entry point for all modes and providers.
    Raises TranslationError on failure.
    """
    if provider == "Gemini":
        translator = GeminiTranslator(gemini_key, gemini_model)
    else:
        translator = OpenRouterTranslator(openrouter_key, openrouter_model)

    if mode == "Translate":
        prompt = build_translate_prompt(text, source_lang, target_lang)
    elif mode == "Summarize":
        prompt = build_summarize_prompt(text, output_lang)
    elif mode == "Improve":
        prompt = build_improve_prompt(text, output_lang)
    else:
        raise TranslationError(f"Modalità sconosciuta: {mode}")

    return translator.run(prompt)
