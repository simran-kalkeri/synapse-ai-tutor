"""
voice_components.py ΓÇö Shared Streamlit UI helpers for voice I/O
================================================================
Uses Streamlit's NATIVE st.audio_input() widget (available since 1.35.0).
No third-party audio-recorder package required ΓÇö zero dependency conflicts.

Provides two reusable render functions used by both tutor.py and chatbot.py:

    render_voice_input(page_key)          ΓåÆ Optional[str]  (transcript)
    render_tts_controls(text, ...)        ΓåÆ None           (plays audio)
    render_tts_settings(page_key)         ΓåÆ bool           (auto-play toggle)

Design decisions
----------------
* Each page gets its own session-state namespace via ``page_key`` to prevent
  cross-page state bleed (e.g. "tutor" vs "chatbot").
* Audio bytes are MD5-hashed so the same recording is NOT re-transcribed on
  every Streamlit rerun (st.audio_input re-sends the UploadedFile each run).
* TTS is triggered on explicit "≡ƒöè Listen" button click or automatically when
  the auto-play toggle is enabled.
* All errors are surfaced as Streamlit warnings ΓÇö never silent crashes.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Optional

import streamlit as st

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Voice Input (STT) ΓÇö uses native st.audio_input()
# ---------------------------------------------------------------------------
def render_voice_input(page_key: str) -> Optional[str]:
    """
    Render the microphone widget and handle STT transcription.

    Uses ``st.audio_input()`` ΓÇö built into Streamlit ΓëÑ 1.35.0.
    Deduplicates recordings via MD5 so the same clip is only transcribed once
    even across multiple Streamlit reruns.

    Args:
        page_key : Unique identifier for this page (e.g. ``'tutor'``, ``'chatbot'``).

    Returns:
        Transcribed text string if new audio was successfully transcribed,
        otherwise ``None``.
    """
    _HASH_KEY = f"_voice_last_hash_{page_key}"

    # ── Render native mic widget ──────────────────────────────────────────────
    audio_file = st.audio_input(
        "🎙️ Click to record your question",
        key=f"_native_audio_{page_key}",
        help="Click the microphone, speak your question, then click stop.",
    )

    if audio_file is None:
        return None

    # ── Deduplicate: skip if same audio was already transcribed ───────────────
    audio_bytes: bytes = audio_file.read()
    if not audio_bytes:
        return None

    audio_hash = hashlib.md5(audio_bytes).hexdigest()
    if st.session_state.get(_HASH_KEY) == audio_hash:
        return None  # Already processed this recording
    st.session_state[_HASH_KEY] = audio_hash

    # ── Transcribe ────────────────────────────────────────────────────────────
    try:
        from backend.stt import transcribe_audio

        with st.spinner("🎙️ Transcribing your voice..."):
            result = transcribe_audio(audio_bytes)

    except Exception as exc:
        st.error(f"Voice input error: {exc}")
        return None

    if result.get("error"):
        st.warning(f"Could not transcribe: {result['error']}")
        return None

    transcript = result.get("text", "").strip()
    if not transcript:
        st.warning("🎙️ Could not understand the audio. Please try speaking again.")
        return None

    # ── Show success indicator ────────────────────────────────────────────────
    lang = result.get("language", "")
    conf = result.get("confidence", 0.0)
    lang_tag = f" • **{lang.upper()}**" if lang else ""
    conf_tag = f" • {conf:.0%} confidence" if conf > 0 else ""
    preview = transcript[:90] + ("..." if len(transcript) > 90 else "")
    st.success(f'✅ **Heard:** "{preview}"{lang_tag}{conf_tag}')

    return transcript


# ---------------------------------------------------------------------------
# Voice Output (TTS)
# ---------------------------------------------------------------------------
def render_tts_controls(
    response_text: str,
    page_key: str,
    message_index: int,
    auto_play: bool = False,
) -> None:
    """
    Render a TTS player for a single assistant response.

    Shows a "🔊 Listen" button. On click, generates the MP3 (cached by MD5)
    and embeds a ``st.audio`` player. Subsequent calls serve from file cache.

    Args:
        response_text : Assistant text to speak.
        page_key      : Page namespace (``'tutor'`` or ``'chatbot'``).
        message_index : Index of this message in history (for unique widget keys).
        auto_play     : If ``True``, generate and play audio without a button click.
    """
    _PATH_KEY = f"_tts_path_{page_key}_{message_index}"
    btn_key   = f"_tts_btn_{page_key}_{message_index}"

    # Auto-play: generate immediately on first render
    if auto_play and _PATH_KEY not in st.session_state:
        _do_generate_tts(response_text, _PATH_KEY)

    # Manual listen button (only shown when auto-play is off)
    if not auto_play:
        if st.button("🔊 Listen", key=btn_key, use_container_width=False):
            _do_generate_tts(response_text, _PATH_KEY)

    # Render audio player if we have a file path
    _render_audio_player(_PATH_KEY)


def _do_generate_tts(text: str, session_key: str) -> None:
    """Generate TTS audio and persist the MP3 file path to session state."""
    try:
        from backend.tts import text_to_speech

        with st.spinner("🔊 Generating audio..."):
            path = text_to_speech(text)

        if path:
            st.session_state[session_key] = path
        else:
            st.warning(
                "⚠️ TTS generation failed. "
                "Check your ElevenLabs API key / internet connection. "
                "gTTS fallback also attempted."
            )
    except Exception as exc:
        st.error(f"TTS error: {exc}")


def _render_audio_player(session_key: str) -> None:
    """Render an st.audio player if an MP3 path exists in session state."""
    path = st.session_state.get(session_key)
    if path:
        try:
            with open(path, "rb") as f:
                audio_data = f.read()
            st.audio(audio_data, format="audio/mp3")
        except Exception as exc:
            st.caption(f"⚠️ Could not load audio: {exc}")


# ---------------------------------------------------------------------------
# TTS Settings — auto-play toggle
# ---------------------------------------------------------------------------
def render_tts_settings(page_key: str) -> bool:
    """
    Render a compact "Auto-play responses" toggle.

    Returns:
        ``True`` if auto-play is currently enabled, ``False`` otherwise.
    """
    _TOGGLE_KEY = f"_tts_autoplay_{page_key}"
    if _TOGGLE_KEY not in st.session_state:
        st.session_state[_TOGGLE_KEY] = False

    st.session_state[_TOGGLE_KEY] = st.toggle(
        "🔊 Auto-play",
        value=st.session_state[_TOGGLE_KEY],
        key=f"_tts_toggle_{page_key}",
        help="Automatically read each response aloud when it arrives.",
    )
    return st.session_state[_TOGGLE_KEY]
