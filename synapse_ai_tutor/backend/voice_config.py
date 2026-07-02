"""
voice_config.py ΓÇö Centralized voice layer configuration for Synapse AI Tutor
=============================================================================
Single source of truth for ALL voice settings.

Usage
-----
Import from any voice backend module::

    from backend.voice_config import cfg

    if cfg.use_groq_stt:
        ...

VOICE_MODE presets
------------------
"hackathon"  (DEFAULT)
    STT  : faster-whisper local only
    TTS  : gTTS only
    APIs : zero external dependencies ΓÇö runs fully offline

"standard"
    STT  : faster-whisper local
    TTS  : gTTS primary, ElevenLabs allowed as fallback if key present

"premium"
    STT  : Groq Whisper (cloud) ΓåÆ faster-whisper fallback
    TTS  : gTTS primary, ElevenLabs allowed as fallback
"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)


# ΓöÇΓöÇ Helper ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
def _bool_env(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")


def _str_env(key: str, default: str) -> str:
    return os.getenv(key, default)


# =============================================================================
class VoiceConfig:
    """
    Immutable-at-runtime voice configuration.
    All values can be overridden by environment variables before startup.
    """

    # ── Mode ──────────────────────────────────────────────────────────────────
    VOICE_MODE: str = _str_env("VOICE_MODE", "premium")   # Groq STT enabled

    # ── STT — faster-whisper (local fallback) ─────────────────────────────────
    WHISPER_MODEL_SIZE: str   = _str_env("WHISPER_MODEL_SIZE", "base")
    WHISPER_DEVICE: str       = _str_env("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = _str_env("WHISPER_COMPUTE_TYPE", "int8")

    # ── STT — Groq Whisper API (PRIMARY — fast cloud STT, no local model needed)
    USE_GROQ_STT: bool  = True                              # enabled in premium mode
    GROQ_STT_MODEL: str = _str_env("GROQ_STT_MODEL", "whisper-large-v3")


    # ── TTS — gTTS (primary, always) ──────────────────────────────────────────
    TTS_LANG: str = _str_env("TTS_LANG", "en")

    # ── TTS — ElevenLabs (optional premium fallback) ──────────────────────────
    USE_ELEVENLABS: bool = _bool_env("ELEVENLABS_ENABLED", False)

    # ΓöÇΓöÇ Apply mode-specific overrides ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    @classmethod
    def _apply_mode(cls) -> None:
        if cls.VOICE_MODE == "hackathon":
            # Enforce zero external dependencies
            cls.USE_GROQ_STT   = False
            cls.USE_ELEVENLABS = False
            logger.info("[VoiceConfig] Mode: HACKATHON ΓÇö local-only, no cloud APIs")

        elif cls.VOICE_MODE == "standard":
            cls.USE_GROQ_STT = False
            # ElevenLabs allowed if key is present (env-controlled)
            logger.info("[VoiceConfig] Mode: STANDARD ΓÇö local STT, gTTS primary")

        elif cls.VOICE_MODE == "premium":
            # Groq + ElevenLabs allowed ΓÇö controlled by env vars
            logger.info("[VoiceConfig] Mode: PREMIUM ΓÇö Groq STT, ElevenLabs optional")

        else:
            logger.warning(
                f"[VoiceConfig] Unknown VOICE_MODE='{cls.VOICE_MODE}'. "
                "Defaulting to hackathon settings."
            )
            cls.USE_GROQ_STT   = False
            cls.USE_ELEVENLABS = False

    def summary(self) -> dict:
        """Return a human-readable config summary dict."""
        return {
            "voice_mode":          self.VOICE_MODE,
            "whisper_model":       self.WHISPER_MODEL_SIZE,
            "whisper_device":      self.WHISPER_DEVICE,
            "whisper_compute":     self.WHISPER_COMPUTE_TYPE,
            "use_groq_stt":        self.USE_GROQ_STT,
            "groq_stt_model":      self.GROQ_STT_MODEL,
            "tts_lang":            self.TTS_LANG,
            "use_elevenlabs":      self.USE_ELEVENLABS,
        }


# Singleton ΓÇö import and use `cfg` everywhere
cfg = VoiceConfig()
cfg._apply_mode()
