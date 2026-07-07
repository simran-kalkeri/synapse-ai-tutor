"""
stt.py ΓÇö Speech-to-Text module for Synapse AI Tutor
======================================================
Primary  : faster-whisper  (local CPU, int8 ΓÇö always available)
Optional : Groq Whisper API (cloud acceleration, auto-fallback on any failure)
Fallback : openai-whisper   (local, pure Python, no ffmpeg dependency)

Transcription pipeline
----------------------
USE_GROQ_STT = False  (hackathon/default):
    audio ΓåÆ faster-whisper ΓåÆ text

USE_GROQ_STT = True  (optional acceleration):
    audio ΓåÆ Groq Whisper ΓöÇΓöÇΓöÇ success ΓöÇΓöÇΓåÆ text
                         ΓööΓöÇΓöÇ failure ΓåÆ faster-whisper ΓåÆ text

Logging convention: all [STT] prefix for easy filtering.

Public API  (unchanged)
----------
    load_whisper_model(model_size)               ΓåÆ (model, backend_name)
    transcribe_audio(audio_bytes, language, ...)  ΓåÆ dict
    validate_stt_startup()                        ΓåÆ dict   ΓåÉ NEW
"""

from __future__ import annotations

import logging
import math
import os
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Model cache — replaces Streamlit's @st.cache_resource for FastAPI context
_whisper_model_cache: dict[str, tuple] = {}

# ---------------------------------------------------------------------------
# Config — single source of truth from voice_config
# ---------------------------------------------------------------------------
try:
    from backend.voice_config import cfg as _cfg
    _MODEL_SIZE    = _cfg.WHISPER_MODEL_SIZE
    _DEVICE        = _cfg.WHISPER_DEVICE
    _COMPUTE_TYPE  = _cfg.WHISPER_COMPUTE_TYPE
    _USE_GROQ      = _cfg.USE_GROQ_STT
    _GROQ_MODEL    = _cfg.GROQ_STT_MODEL
except Exception:
    # Defensive fallback if voice_config is unavailable
    _MODEL_SIZE   = os.getenv("WHISPER_MODEL_SIZE", "base")
    _DEVICE       = "cpu"
    _COMPUTE_TYPE = "int8"
    _USE_GROQ     = False
    _GROQ_MODEL   = "whisper-large-v3"


# ---------------------------------------------------------------------------
# ffmpeg — ensure it is on PATH (uses bundled imageio-ffmpeg on Windows)
# ---------------------------------------------------------------------------
def _ensure_ffmpeg() -> None:
    """
    Add the imageio-ffmpeg bundled binary directory to PATH so that
    openai-whisper (and pydub) can find ffmpeg without a system install.
    Safe to call multiple times — only adds the path once.
    """
    try:
        import imageio_ffmpeg  # type: ignore
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
            logger.info(f"[STT] ffmpeg injected into PATH from imageio-ffmpeg: {ffmpeg_dir}")
    except Exception as exc:
        logger.debug(f"[STT] imageio-ffmpeg not available, skipping PATH injection: {exc}")


# ---------------------------------------------------------------------------
# Groq API key resolution
# ---------------------------------------------------------------------------
def _get_groq_key() -> Optional[str]:
    """Retrieve Groq API key from env var."""
    return os.getenv("GROQ_API_KEY")


# ---------------------------------------------------------------------------
# Groq STT backend  (optional acceleration layer)
# ---------------------------------------------------------------------------
def _groq_transcribe(audio_path: str, language: Optional[str]) -> Optional[dict]:
    """
    Attempt transcription via Groq Whisper API.

    Returns a normalised result dict on success, or None on any failure.
    The caller MUST fall back to local Whisper when this returns None.
    """
    if not _USE_GROQ:
        return None

    api_key = _get_groq_key()
    if not api_key:
        logger.debug("[STT] Groq key not configured ΓÇö skipping Groq.")
        return None

    try:
        from groq import Groq  # type: ignore

        logger.info("[STT] Trying Groq Whisper API")
        client = Groq(api_key=api_key)

        with open(audio_path, "rb") as f:
            kwargs: dict = {"model": _GROQ_MODEL, "response_format": "verbose_json"}
            if language:
                kwargs["language"] = language
            response = client.audio.transcriptions.create(file=f, **kwargs)

        text = getattr(response, "text", "") or ""
        detected_lang = getattr(response, "language", language or "")
        logger.debug(f"[STT] Groq transcribed {len(text)} chars")

        return {
            "text":       text.strip(),
            "language":   detected_lang,
            "confidence": 0.95,   # Groq doesn't expose per-segment logprobs
            "error":      None,
            "provider":   "groq",
        }

    except ImportError:
        logger.warning("[STT] Groq package not installed (pip install groq)")
        return None
    except Exception as exc:
        logger.warning(f"[STT] Groq unavailable: {exc}")
        logger.info("[STT] Falling back to Faster-Whisper")
        return None


# ---------------------------------------------------------------------------
# Local Whisper backend loaders
# ---------------------------------------------------------------------------
def _try_faster_whisper(model_size: str):
    """Load faster-whisper WhisperModel. Returns (model, 'faster_whisper') or (None, None)."""
    try:
        from faster_whisper import WhisperModel  # type: ignore

        model = WhisperModel(
            model_size,
            device=_DEVICE,
            compute_type=_COMPUTE_TYPE,
        )
        logger.info(
            f"[STT] Faster-Whisper loaded: model={model_size} "
            f"device={_DEVICE} compute={_COMPUTE_TYPE}"
        )
        return model, "faster_whisper"

    except Exception as exc:
        logger.warning(f"[STT] faster-whisper unavailable ({exc})")
        return None, None


def _try_openai_whisper(model_size: str):
    """Load openai-whisper model. Returns (model, 'openai_whisper') or (None, None)."""
    try:
        import whisper  # type: ignore

        model = whisper.load_model(model_size)
        logger.info(f"[STT] openai-whisper loaded: model={model_size}")
        return model, "openai_whisper"

    except Exception as exc:
        logger.error(f"[STT] openai-whisper also unavailable ({exc})")
        return None, None


def load_whisper_model(model_size: str = _MODEL_SIZE):
    """
    Load and cache the local Whisper model for the server lifetime.

    Tries faster-whisper first; falls back to openai-whisper.
    Cached in module-level dict — loads only once per server session.

    Returns:
        (model, backend_name: str)
    Raises:
        RuntimeError if neither backend is importable.
    """
    if model_size in _whisper_model_cache:
        return _whisper_model_cache[model_size]

    logger.info(f"[STT] Loading local Whisper model '{model_size}'…")
    model, backend = _try_faster_whisper(model_size)
    if model is None:
        model, backend = _try_openai_whisper(model_size)
    if model is None:
        raise RuntimeError(
            "[STT] No local Whisper backend available.\n"
            "Install one of:\n"
            "  pip install faster-whisper\n"
            "  pip install openai-whisper"
        )
    logger.info(f"[STT] Using Faster-Whisper Local (backend={backend})")
    _whisper_model_cache[model_size] = (model, backend)
    return model, backend


# ---------------------------------------------------------------------------
# Local transcription helpers
# ---------------------------------------------------------------------------
def _transcribe_faster_whisper(model, audio_path: str, language: Optional[str]) -> dict:
    """Run inference with faster-whisper and return a normalised result dict."""
    kwargs: dict = {"beam_size": 5}
    if language:
        kwargs["language"] = language

    segments, info = model.transcribe(audio_path, **kwargs)

    text_parts:  list[str]   = []
    confidences: list[float] = []

    for seg in segments:
        text_parts.append(seg.text.strip())
        if hasattr(seg, "avg_logprob"):
            conf = max(0.0, min(1.0, math.exp(seg.avg_logprob)))
            confidences.append(conf)

    full_text    = " ".join(text_parts).strip()
    avg_conf     = sum(confidences) / len(confidences) if confidences else 0.0
    detected_lang = getattr(info, "language", language or "")

    return {
        "text":       full_text,
        "language":   detected_lang,
        "confidence": round(avg_conf, 3),
        "error":      None,
        "provider":   "faster_whisper",
    }


def _transcribe_openai_whisper(model, audio_path: str, language: Optional[str]) -> dict:
    """Run inference with openai-whisper and return a normalised result dict."""
    kwargs: dict = {}
    if language:
        kwargs["language"] = language

    result    = model.transcribe(audio_path, **kwargs)
    segments  = result.get("segments", [])
    confidences: list[float] = []
    for seg in segments:
        if "avg_logprob" in seg:
            conf = max(0.0, min(1.0, math.exp(seg["avg_logprob"])))
            confidences.append(conf)

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.8

    return {
        "text":       result.get("text", "").strip(),
        "language":   result.get("language", language or ""),
        "confidence": round(avg_conf, 3),
        "error":      None,
        "provider":   "openai_whisper",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def transcribe_audio(
    audio_bytes: bytes,
    language: Optional[str] = None,
    model_size: Optional[str] = None,
) -> dict:
    """
    Transcribe raw audio bytes into text.

    Pipeline (hackathon mode):
        audio ΓåÆ faster-whisper ΓåÆ text

    Pipeline (with USE_GROQ_STT=True):
        audio ΓåÆ Groq API ΓåÆ text
                ΓööΓöÇΓöÇ on failure ΓåÆ faster-whisper ΓåÆ text

    Args:
        audio_bytes : Raw audio (WAV, MP3, OGG, FLAC ΓÇª).
        language    : Optional ISO-639-1 hint (e.g. ``'en'``). Auto-detect if None.
        model_size  : Whisper model size. Uses voice_config default if None.

    Returns:
        dict with keys:
            ``text``        ΓÇô transcribed string
            ``language``    ΓÇô detected / provided code
            ``confidence``  ΓÇô [0, 1]
            ``error``       ΓÇô None on success, string on failure
            ``provider``    ΓÇô which backend produced the result
    """
    if not audio_bytes:
        return {"text": "", "language": "", "confidence": 0.0,
                "error": "No audio data received.", "provider": "none"}

    if model_size is None:
        model_size = _MODEL_SIZE

    tmp_path: Optional[str] = None
    try:
        # Ensure ffmpeg binary is on PATH (needed by openai-whisper and pydub)
        _ensure_ffmpeg()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # ── Step 1: Try Groq (only when enabled and key is present) ───────────
        groq_result = _groq_transcribe(tmp_path, language)
        if groq_result is not None:
            return groq_result

        # ── Step 2: Local Whisper (always available) ──────────────────────────
        logger.info("[STT] Using Faster-Whisper Local")
        model, backend = load_whisper_model(model_size)

        if backend == "faster_whisper":
            return _transcribe_faster_whisper(model, tmp_path, language)
        else:
            return _transcribe_openai_whisper(model, tmp_path, language)

    except Exception as exc:
        logger.error(f"[STT] transcribe_audio() failed: {exc}")
        return {"text": "", "language": "", "confidence": 0.0,
                "error": str(exc), "provider": "none"}
    finally:
        if tmp_path and Path(tmp_path).exists():
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Startup validation (new)
# ---------------------------------------------------------------------------
def validate_stt_startup() -> dict:
    """
    Validate that the STT stack is correctly configured at startup.

    Checks:
    * faster-whisper importable
    * Model can be instantiated (without loading weights ΓÇö just import check)
    * Groq package present (if USE_GROQ_STT=True)
    * Groq API key present (if USE_GROQ_STT=True)

    Returns a dict:
        {
            "faster_whisper": bool,
            "openai_whisper": bool,
            "groq_package":   bool,
            "groq_key":       bool,
            "ready":          bool,   # True if at least one local backend is ready
            "errors":         list[str],
        }
    """
    result: dict = {
        "faster_whisper": False,
        "openai_whisper": False,
        "groq_package":   False,
        "groq_key":       False,
        "ready":          False,
        "errors":         [],
    }

    # faster-whisper
    try:
        from faster_whisper import WhisperModel  # noqa: F401  type: ignore
        result["faster_whisper"] = True
        logger.info("[STT] Startup check: faster-whisper OK")
    except ImportError as e:
        result["errors"].append(f"faster-whisper not installed: {e}")
        logger.warning(f"[STT] Startup check: faster-whisper MISSING ({e})")

    # openai-whisper (fallback)
    try:
        import whisper  # noqa: F401  type: ignore
        result["openai_whisper"] = True
        logger.info("[STT] Startup check: openai-whisper OK (fallback available)")
    except ImportError:
        logger.debug("[STT] Startup check: openai-whisper not installed (optional)")

    # Groq (only relevant when enabled)
    try:
        import groq  # noqa: F401  type: ignore
        result["groq_package"] = True
    except ImportError:
        if _USE_GROQ:
            result["errors"].append("groq package not installed (pip install groq)")

    if _USE_GROQ:
        result["groq_key"] = bool(_get_groq_key())
        if not result["groq_key"]:
            result["errors"].append("GROQ_API_KEY not set (required when USE_GROQ_STT=True)")

    result["ready"] = result["faster_whisper"] or result["openai_whisper"]

    if result["ready"]:
        logger.info("[STT] Startup validation PASSED")
    else:
        logger.error("[STT] Startup validation FAILED ΓÇö no local Whisper backend found")

    return result
