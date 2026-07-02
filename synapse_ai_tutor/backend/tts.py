"""
tts.py ΓÇö Text-to-Speech module for Synapse AI Tutor
======================================================
Primary  : gTTS  (Google TTS ΓÇö free, no API key, zero rate limits)
Fallback : ElevenLabs API  (optional premium, requires API key)

Provider Priority
-----------------
PROVIDER_PRIORITY = ["gtts", "elevenlabs"]

By default USE_ELEVENLABS = False (hackathon mode).
Controlled centrally by backend/voice_config.py ΓåÆ VOICE_MODE.
Set ELEVENLABS_ENABLED=true (env) to allow ElevenLabs as fallback.

Features
--------
* File-based MD5 cache in   <repo_root>/audio_cache/   (outside synapse_ai_tutor/)
* Automatic sentence-boundary chunking for long responses
* Pydub-based MP3 concatenation for chunked synthesis
* Markdown stripping before synthesis for clean audio
* Structured [TTS] logging for clear provider tracing

Public API  (unchanged ΓÇö fully backward-compatible)
----------
    text_to_speech(text, voice_id, lang, use_elevenlabs, strip_markdown) -> str | None
    get_available_voices() -> list[dict]
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths ΓÇö audio_cache lives OUTSIDE synapse_ai_tutor/
# ---------------------------------------------------------------------------
# backend/tts.py  ΓåÆ  .parent = backend/  ΓåÆ  .parent = synapse_ai_tutor/  ΓåÆ  .parent = repo_root/
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIO_CACHE_DIR = _REPO_ROOT / "audio_cache"
AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Provider configuration ΓÇö driven by voice_config (single source of truth)
# ---------------------------------------------------------------------------
# Priority order: first entry is tried first, second is the fallback.
PROVIDER_PRIORITY: list[str] = ["gtts", "elevenlabs"]

# Pull USE_ELEVENLABS from centralized config; fall back gracefully.
try:
    from backend.voice_config import cfg as _voice_cfg
    USE_ELEVENLABS: bool = _voice_cfg.USE_ELEVENLABS
except Exception:
    USE_ELEVENLABS: bool = os.getenv("ELEVENLABS_ENABLED", "false").lower() == "true"

# ElevenLabs voice config (only used when USE_ELEVENLABS is True)
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"   # "Bella" ΓÇö warm, educational tone
DEFAULT_MODEL_ID = "eleven_monolingual_v1"

# Chunk size ΓÇö consistent chunking regardless of provider
_CHUNK_MAX_CHARS = 2_500


# ---------------------------------------------------------------------------
# API key resolution (ElevenLabs only)
# ---------------------------------------------------------------------------
def _get_elevenlabs_key() -> Optional[str]:
    """Retrieve ElevenLabs API key from Streamlit secrets ΓåÆ env var ΓåÆ None."""
    try:
        import streamlit as st
        key = st.secrets.get("elevenlabs", {}).get("ELEVENLABS_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("ELEVENLABS_API_KEY")


# ---------------------------------------------------------------------------
# Text utilities  (unchanged)
# ---------------------------------------------------------------------------
def _strip_markdown(text: str) -> str:
    """Remove common Markdown syntax so TTS doesn't read asterisks, backticks, etc."""
    # Fenced code blocks
    text = re.sub(r"```[\s\S]*?```", " ", text)
    # Inline code
    text = re.sub(r"`[^`]+`", "", text)
    # ATX headings
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Bold / italic (**, *, __, _)
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
    # Markdown links  [label](url)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Unordered bullets
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    # Ordered lists
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Collapse multiple blank lines ΓåÆ sentence break
    text = re.sub(r"\n{2,}", ". ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_into_chunks(text: str, max_chars: int = _CHUNK_MAX_CHARS) -> list[str]:
    """Split *text* into sentence-boundary-aligned chunks, each Γëñ *max_chars*."""
    if len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i : i + max_chars])
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks or [text]


# ---------------------------------------------------------------------------
# Synthesis backends
# ---------------------------------------------------------------------------
def _gtts_synthesize(text: str, lang: str, output_path: Path) -> bool:
    """
    Synthesize *text* via Google TTS (gTTS) and write MP3 to *output_path*.

    PRIMARY provider ΓÇö free, no API key, no rate limits.
    Returns True on success, False on any error.
    """
    try:
        from gtts import gTTS  # type: ignore

        logger.info("[TTS] Using gTTS")
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(str(output_path))
        logger.debug(f"[TTS] gTTS [{lang}] -> {output_path.name}")
        return True

    except Exception as exc:
        logger.warning(f"[TTS] gTTS failed: {exc}")
        return False


def _elevenlabs_synthesize(text: str, voice_id: str, output_path: Path) -> bool:
    """
    Synthesize *text* via ElevenLabs API and write MP3 to *output_path*.

    OPTIONAL FALLBACK ΓÇö only called when USE_ELEVENLABS is True and gTTS fails.
    Returns True on success, False on any error.
    """
    if not USE_ELEVENLABS:
        logger.debug("[TTS] ElevenLabs disabled (USE_ELEVENLABS=False)")
        return False

    api_key = _get_elevenlabs_key()
    if not api_key:
        logger.warning("[TTS] ElevenLabs API key not configured ΓÇö skipping.")
        return False

    try:
        from elevenlabs.client import ElevenLabs  # type: ignore
        from elevenlabs import save               # type: ignore

        logger.info("[TTS] gTTS failed, falling back to ElevenLabs")
        client = ElevenLabs(api_key=api_key)
        audio = client.generate(
            text=text,
            voice=voice_id,
            model=DEFAULT_MODEL_ID,
        )
        save(audio, str(output_path))
        logger.debug(f"[TTS] ElevenLabs -> {output_path.name}")
        return True

    except Exception as exc:
        logger.error(f"[TTS] ElevenLabs synthesis also failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# Core synthesis dispatcher  (respects PROVIDER_PRIORITY)
# ---------------------------------------------------------------------------
def _synthesize_single(
    text: str,
    lang: str,
    voice_id: str,
    output_path: Path,
) -> bool:
    """
    Try each provider in PROVIDER_PRIORITY order until one succeeds.

    gTTS is always first. ElevenLabs is only attempted when USE_ELEVENLABS=True.
    """
    for provider in PROVIDER_PRIORITY:
        if provider == "gtts":
            if _gtts_synthesize(text, lang, output_path):
                return True
        elif provider == "elevenlabs":
            if _elevenlabs_synthesize(text, voice_id, output_path):
                return True
        else:
            logger.warning(f"[TTS] Unknown provider in PROVIDER_PRIORITY: '{provider}'")

    logger.error("[TTS] All providers failed for this chunk.")
    return False


# ---------------------------------------------------------------------------
# Audio concatenation  (unchanged)
# ---------------------------------------------------------------------------
def _concatenate_mp3s(paths: list[Path], output_path: Path) -> bool:
    """Merge multiple MP3 files into one using pydub. Returns True on success."""
    try:
        from pydub import AudioSegment  # type: ignore

        combined = AudioSegment.empty()
        for p in paths:
            combined += AudioSegment.from_mp3(str(p))
        combined.export(str(output_path), format="mp3")
        return True

    except Exception as exc:
        logger.error(f"[TTS] MP3 concatenation failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# Public API  (fully backward-compatible)
# ---------------------------------------------------------------------------
def text_to_speech(
    text: str,
    voice_id: str = DEFAULT_VOICE_ID,
    lang: str = "en",
    use_elevenlabs: bool = False,   # ΓåÉ default changed: False = gTTS primary
    strip_markdown: bool = True,
) -> Optional[str]:
    """
    Convert *text* to speech and return the absolute path of the generated MP3.

    Provider order: gTTS (primary) ΓåÆ ElevenLabs (optional fallback).

    Results are cached by MD5(text + voice_id + lang) so identical responses
    are served instantly without hitting any provider.

    Args:
        text            : Text to synthesise.
        voice_id        : ElevenLabs voice ID (ignored by gTTS).
        lang            : BCP-47 language tag for gTTS (e.g. ``'en'``, ``'fr'``).
        use_elevenlabs  : When ``True``, overrides the module-level USE_ELEVENLABS
                          flag to allow ElevenLabs as a fallback for this call only.
                          Kept for backward compatibility ΓÇö callers that previously
                          passed ``use_elevenlabs=True`` will still work.
        strip_markdown  : Remove Markdown syntax before synthesis.

    Returns:
        Absolute path string to the MP3 file, or ``None`` on failure.
    """
    if not text or not text.strip():
        return None

    clean_text = _strip_markdown(text) if strip_markdown else text
    if not clean_text:
        return None

    # Honour per-call override: if the caller explicitly requests ElevenLabs,
    # temporarily enable it for this call without mutating the global flag.
    global USE_ELEVENLABS
    _saved_flag = USE_ELEVENLABS
    if use_elevenlabs:
        USE_ELEVENLABS = True

    try:
        return _synthesize(clean_text, lang, voice_id)
    finally:
        USE_ELEVENLABS = _saved_flag   # always restore


def _synthesize(clean_text: str, lang: str, voice_id: str) -> Optional[str]:
    """Internal synthesis entry point (after markdown stripping)."""

    # ΓöÇΓöÇ Cache look-up ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    cache_key   = hashlib.md5(f"{clean_text}:{voice_id}:{lang}".encode()).hexdigest()
    cached_path = AUDIO_CACHE_DIR / f"{cache_key}.mp3"

    if cached_path.exists() and cached_path.stat().st_size > 0:
        logger.info(f"[TTS] Audio cache hit -> {cached_path.name}")
        return str(cached_path)

    # ΓöÇΓöÇ Hackathon / gTTS-only mode: skip chunking entirely ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    # gTTS handles its own internal text splitting ΓÇö no API char limit.
    # This avoids pydub MP3 concatenation which requires a system ffmpeg binary.
    if not USE_ELEVENLABS:
        success = _gtts_synthesize(clean_text, lang, cached_path)
        return str(cached_path) if success and cached_path.exists() else None

    # ΓöÇΓöÇ ElevenLabs enabled: chunk to stay within API size limits ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    chunks = _split_into_chunks(clean_text)

    if len(chunks) == 1:
        success = _synthesize_single(clean_text, lang, voice_id, cached_path)
        return str(cached_path) if success and cached_path.exists() else None

    # Multi-chunk: synthesise each piece then merge
    chunk_paths: list[Path] = []
    for i, chunk in enumerate(chunks):
        c_key  = hashlib.md5(f"{chunk}:{voice_id}:{lang}".encode()).hexdigest()
        c_path = AUDIO_CACHE_DIR / f"chunk_{c_key}.mp3"

        if not (c_path.exists() and c_path.stat().st_size > 0):
            if not _synthesize_single(chunk, lang, voice_id, c_path):
                logger.error(f"[TTS] Failed on chunk {i + 1}/{len(chunks)}")
                return None

        chunk_paths.append(c_path)

    if len(chunk_paths) == 1:
        chunk_paths[0].rename(cached_path)
    else:
        if not _concatenate_mp3s(chunk_paths, cached_path):
            return None

    return str(cached_path) if cached_path.exists() else None


def get_available_voices() -> list[dict]:
    """
    Return a list of available ElevenLabs voices.

    Returns an empty list when USE_ELEVENLABS is False or the key is absent.
    Each entry is a dict with ``voice_id`` and ``name`` keys.
    """
    if not USE_ELEVENLABS:
        return []

    api_key = _get_elevenlabs_key()
    if not api_key:
        return []

    try:
        from elevenlabs.client import ElevenLabs  # type: ignore

        client   = ElevenLabs(api_key=api_key)
        response = client.voices.get_all()
        return [{"voice_id": v.voice_id, "name": v.name} for v in response.voices]

    except Exception as exc:
        logger.warning(f"[TTS] get_available_voices() failed: {exc}")
        return []
