"""
voice_health.py ΓÇö Voice layer startup health check for Synapse AI Tutor
=========================================================================
Checks every component of the voice stack and reports status.

Two entry points
----------------
log_health_check()          ΓåÆ prints results to console at startup
render_voice_health(st)     ΓåÆ renders a Streamlit expandable status panel

Check results key
-----------------
  PASS  Component is ready
  WARN  Optional component missing (non-blocking)
  FAIL  Required component missing (blocking)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Column widths for console output
_W = 42


# ---------------------------------------------------------------------------
# Individual component checks
# ---------------------------------------------------------------------------
def _check_faster_whisper() -> tuple[bool, str]:
    try:
        from faster_whisper import WhisperModel  # noqa  type: ignore
        return True, "faster-whisper installed"
    except ImportError:
        return False, "faster-whisper NOT installed (pip install faster-whisper)"


def _check_openai_whisper() -> tuple[bool, str]:
    try:
        import whisper  # noqa  type: ignore
        return True, "openai-whisper installed (fallback available)"
    except ImportError:
        return False, "openai-whisper not installed (optional fallback)"


def _check_gtts() -> tuple[bool, str]:
    try:
        from gtts import gTTS  # noqa  type: ignore
        return True, "gTTS installed"
    except ImportError:
        return False, "gTTS NOT installed (pip install gTTS)"


def _check_audio_cache() -> tuple[bool, str]:
    try:
        _repo_root = Path(__file__).resolve().parent.parent.parent
        cache_dir  = _repo_root / "audio_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        test_file  = cache_dir / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        return True, f"Writable: {cache_dir}"
    except Exception as exc:
        return False, f"Audio cache NOT writable: {exc}"


def _check_pydub() -> tuple[bool, str]:
    try:
        from pydub import AudioSegment  # noqa  type: ignore
        return True, "pydub installed (audio concatenation ready)"
    except ImportError:
        return False, "pydub NOT installed (pip install pydub)"


def _check_microphone() -> tuple[bool, str]:
    """Microphone availability is browser-side; st.audio_input() handles it."""
    try:
        import streamlit as st
        ver = tuple(int(x) for x in st.__version__.split(".")[:2])
        if ver >= (1, 35):
            return True, f"st.audio_input() available (Streamlit {st.__version__})"
        else:
            return False, f"Streamlit {st.__version__} < 1.35 ΓÇö st.audio_input() unavailable"
    except Exception as exc:
        return False, f"Streamlit check failed: {exc}"


def _check_elevenlabs() -> tuple[str, str]:
    """Returns 'ok'/'warn'/'skip' ΓÇö ElevenLabs is always optional."""
    try:
        from backend.voice_config import cfg
        if not cfg.USE_ELEVENLABS:
            return "skip", "Disabled in voice_config (VOICE_MODE=hackathon)"
    except Exception:
        pass

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("elevenlabs", {}).get("ELEVENLABS_API_KEY")
        except Exception:
            pass

    try:
        from elevenlabs.client import ElevenLabs  # noqa  type: ignore
        if api_key:
            return "ok", "elevenlabs package installed, API key present"
        else:
            return "warn", "elevenlabs package installed but API key not set"
    except ImportError:
        return "warn", "elevenlabs not installed (optional ΓÇö pip install elevenlabs)"


def _check_groq() -> tuple[str, str]:
    """Returns 'ok'/'warn'/'skip' ΓÇö Groq is always optional."""
    try:
        from backend.voice_config import cfg
        if not cfg.USE_GROQ_STT:
            return "skip", "Disabled in voice_config (USE_GROQ_STT=False)"
    except Exception:
        pass

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("groq", {}).get("GROQ_API_KEY")
        except Exception:
            pass

    try:
        import groq  # noqa  type: ignore
        if api_key:
            return "ok", "groq package installed, API key present"
        else:
            return "warn", "groq package installed but GROQ_API_KEY not set"
    except ImportError:
        return "warn", "groq not installed (optional ΓÇö pip install groq)"


# ---------------------------------------------------------------------------
# Aggregated health check
# ---------------------------------------------------------------------------
def run_health_check() -> dict[str, Any]:
    """
    Run all voice component checks.

    Returns
    -------
    dict with keys:
        checks      : list of (label, status, message) tuples
                      status in {'PASS', 'FAIL', 'WARN', 'SKIP'}
        voice_ready : bool  ΓÇö True if minimum required components present
        stt_ready   : bool
        tts_ready   : bool
        errors      : list[str]
    """
    checks: list[tuple[str, str, str]] = []
    errors: list[str] = []

    # ΓöÇΓöÇ Required components ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    fw_ok,  fw_msg  = _check_faster_whisper()
    ow_ok,  ow_msg  = _check_openai_whisper()
    gt_ok,  gt_msg  = _check_gtts()
    ac_ok,  ac_msg  = _check_audio_cache()
    pd_ok,  pd_msg  = _check_pydub()
    mic_ok, mic_msg = _check_microphone()

    checks.append(("Faster-Whisper (STT)",    "PASS" if fw_ok  else "FAIL", fw_msg))
    checks.append(("openai-whisper (fallback)","PASS" if ow_ok  else "WARN", ow_msg))
    checks.append(("gTTS (TTS primary)",       "PASS" if gt_ok  else "FAIL", gt_msg))
    checks.append(("Audio Cache",              "PASS" if ac_ok  else "FAIL", ac_msg))
    checks.append(("pydub (audio merge)",      "PASS" if pd_ok  else "WARN", pd_msg))
    checks.append(("Microphone (st.audio_input)", "PASS" if mic_ok else "WARN", mic_msg))

    if not fw_ok:  errors.append(fw_msg)
    if not gt_ok:  errors.append(gt_msg)
    if not ac_ok:  errors.append(ac_msg)

    # ΓöÇΓöÇ Optional components ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    el_status, el_msg = _check_elevenlabs()
    gq_status, gq_msg = _check_groq()

    _STATUS_MAP = {"ok": "PASS", "warn": "WARN", "skip": "SKIP"}
    checks.append(("ElevenLabs (optional TTS)", _STATUS_MAP.get(el_status, "WARN"), el_msg))
    checks.append(("Groq (optional STT accel)", _STATUS_MAP.get(gq_status, "WARN"), gq_msg))

    # ΓöÇΓöÇ Voice config ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    try:
        from backend.voice_config import cfg
        checks.append(("Voice Mode", "PASS", f"VOICE_MODE={cfg.VOICE_MODE}"))
    except Exception as exc:
        checks.append(("Voice Mode", "WARN", f"voice_config unavailable: {exc}"))

    stt_ready   = fw_ok or ow_ok
    tts_ready   = gt_ok
    voice_ready = stt_ready and tts_ready and ac_ok

    return {
        "checks":      checks,
        "voice_ready": voice_ready,
        "stt_ready":   stt_ready,
        "tts_ready":   tts_ready,
        "errors":      errors,
    }


# ---------------------------------------------------------------------------
# Console logger
# ---------------------------------------------------------------------------
def log_health_check() -> None:
    """Log the full voice health check to the Python logger (console / Streamlit logs)."""
    result = run_health_check()

    logger.info("=" * 60)
    logger.info("  Synapse Voice Layer -- Startup Health Check")
    logger.info("=" * 60)

    icons = {"PASS": "[OK]  ", "FAIL": "[FAIL]", "WARN": "[WARN]", "SKIP": "[SKIP]"}
    for label, status, message in result["checks"]:
        icon = icons.get(status, "[?]   ")
        logger.info(f"  {icon} {label:<36} {message}")

    logger.info("-" * 60)
    overall = "READY" if result["voice_ready"] else "NOT READY"
    logger.info(f"  Voice Layer: {overall}")
    if result["errors"]:
        for err in result["errors"]:
            logger.error(f"  ERROR: {err}")
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Streamlit renderer
# ---------------------------------------------------------------------------
def render_voice_health(location: Any = None) -> None:
    """
    Render a collapsible voice health panel in Streamlit.

    Args:
        location : A Streamlit column/container, or None for main area.
    """
    import streamlit as st
    target = location or st

    result = run_health_check()
    voice_ready = result["voice_ready"]

    badge_color = "#2ECC71" if voice_ready else "#E74C3C"
    badge_label = "Voice Ready" if voice_ready else "Voice Issues"

    with target.expander(f"≡ƒÄÖ∩╕Å Voice Status ΓÇö {badge_label}", expanded=not voice_ready):
        _STATUS_STYLE = {
            "PASS": ("Γ£à", "#2ECC71"),
            "FAIL": ("Γ¥î", "#E74C3C"),
            "WARN": ("ΓÜá∩╕Å", "#F39C12"),
            "SKIP": ("Γèÿ",  "#6B6B8D"),
        }

        for label, status, message in result["checks"]:
            icon, color = _STATUS_STYLE.get(status, ("?", "#FFFFFF"))
            st.markdown(
                f'<div style="display:flex;align-items:flex-start;gap:0.6rem;'
                f'padding:0.28rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
                f'<span style="font-size:1rem;flex-shrink:0;">{icon}</span>'
                f'<div><span style="color:#FFFFFF;font-size:0.78rem;font-weight:600;">'
                f'{label}</span><br>'
                f'<span style="color:{color};font-size:0.7rem;">{message}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        if result["errors"]:
            st.error("Fix required: " + " | ".join(result["errors"]))
        else:
            st.success("All required voice components are operational.")
