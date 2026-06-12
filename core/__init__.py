"""AI Translator – core package."""
from .translator import (
    process,
    TranslationError,
    MODES,
    LANGUAGES,
    LANGUAGE_NAMES,
    GEMINI_MODELS,
    GEMINI_MODEL_NAMES,
    OPENROUTER_MODELS,
    OPENROUTER_MODEL_NAMES,
)

__all__ = [
    "process",
    "TranslationError",
    "MODES",
    "LANGUAGES",
    "LANGUAGE_NAMES",
    "GEMINI_MODELS",
    "GEMINI_MODEL_NAMES",
    "OPENROUTER_MODELS",
    "OPENROUTER_MODEL_NAMES",
]
