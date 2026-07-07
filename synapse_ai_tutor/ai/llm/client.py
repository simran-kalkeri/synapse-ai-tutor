"""
LLM Client for Synapse AI Tutor — CANONICAL MODULE.
Primary  : Ollama            (remote server at http://10.1.17.65:11434)
Secondary: Groq API          (cloud, fast inference)
Fallback : NVIDIA NIM API    (nvidia/nemotron-3-ultra-550b-a55b via OpenAI-compat endpoint)

This is the single source of truth for LLM calls.
backend/llm_client.py is a thin wrapper that delegates _call_nvidia here;
all new code should import from this module directly.

Public API:
    generate_response(prompt, system_prompt, ...) -> str
    get_llm_status() -> dict
"""

from __future__ import annotations

import time
from typing import Optional

from config.logging_config import get_logger
from config.settings import get_settings
from core.exceptions import (
    LLMError,
    LLMOfflineError,
    LLMRateLimitError,
    LLMResponseError,
    LLMTimeoutError,
)

logger = get_logger(__name__)


# ── Groq Client ────────────────────────────────────────────────────────────

def _call_groq(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model: Optional[str] = None,
) -> str:
    """
    Call the Groq API for LLM inference.

    Returns:
        Generated text string.
    Raises:
        LLMOfflineError: if Groq is unreachable.
        LLMRateLimitError: if rate limit exceeded.
        LLMResponseError: if response is invalid.
    """
    settings = get_settings()
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise LLMOfflineError("groq")

    try:
        from groq import Groq
    except ImportError:
        raise LLMOfflineError("groq")

    model = model or settings.GROQ_MODEL

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        client = Groq(api_key=api_key)
        start = time.time()

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        elapsed = time.time() - start
        text = response.choices[0].message.content.strip()

        logger.info(
            "groq_response",
            model=model,
            tokens=getattr(response.usage, "total_tokens", 0),
            elapsed_s=round(elapsed, 2),
            response_len=len(text),
        )
        return text

    except Exception as exc:
        exc_str = str(exc).lower()
        if "rate_limit" in exc_str or "429" in exc_str:
            logger.warning("groq_rate_limit", error=str(exc))
            raise LLMRateLimitError() from exc
        if "timeout" in exc_str:
            logger.warning("groq_timeout", error=str(exc))
            raise LLMTimeoutError() from exc
        logger.error("groq_error", error=str(exc))
        raise LLMOfflineError("groq") from exc


# ── NVIDIA NIM Client ────────────────────────────────────────────────────

def _call_nvidia(
    prompt: str,
    system_prompt: str = "",
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: Optional[str] = None,
) -> str:
    """
    Call the NVIDIA NIM API (OpenAI-compatible endpoint) for LLM inference.

    Endpoint: https://integrate.api.nvidia.com/v1
    Compatible with the standard `openai` Python SDK.

    Returns:
        Generated text string.
    Raises:
        LLMOfflineError: if NVIDIA NIM is unreachable / not configured.
        LLMRateLimitError: if the rate limit is exceeded.
        LLMTimeoutError: on request timeout.
    """
    settings = get_settings()
    api_key = settings.NVIDIA_API_KEY
    if not api_key:
        raise LLMOfflineError("nvidia")

    try:
        from openai import OpenAI  # reuse openai SDK pointed at NIM base URL
    except ImportError:
        raise LLMOfflineError("nvidia")  # openai package not installed

    _model = model or settings.NVIDIA_MODEL
    _temperature = temperature if temperature is not None else settings.NVIDIA_TEMPERATURE
    _max_tokens = max_tokens or settings.NVIDIA_MAX_TOKENS

    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        client = OpenAI(
            base_url=settings.NVIDIA_BASE_URL,
            api_key=api_key,
        )
        start = time.time()

        response = client.chat.completions.create(
            model=_model,
            messages=messages,   # type: ignore[arg-type]
            temperature=_temperature,
            max_tokens=_max_tokens,
        )

        elapsed = time.time() - start
        text = (response.choices[0].message.content or "").strip()

        logger.info(
            "nvidia_response",
            model=_model,
            tokens=getattr(response.usage, "total_tokens", 0),
            elapsed_s=round(elapsed, 2),
            response_len=len(text),
        )
        return text

    except Exception as exc:
        exc_str = str(exc).lower()
        if "rate_limit" in exc_str or "429" in exc_str:
            logger.warning("nvidia_rate_limit", error=str(exc))
            raise LLMRateLimitError() from exc
        if "timeout" in exc_str:
            logger.warning("nvidia_timeout", error=str(exc))
            raise LLMTimeoutError() from exc
        logger.error("nvidia_error", error=str(exc))
        raise LLMOfflineError("nvidia") from exc


# ── Ollama Client (Fallback) ──────────────────────────────────────────────

def _call_ollama(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model: Optional[str] = None,
) -> str:
    """
    Call the Ollama API for LLM inference (fallback).

    Returns:
        Generated text string.
    Raises:
        LLMOfflineError: if Ollama is unreachable.
    """
    import requests

    settings = get_settings()
    if not settings.OLLAMA_ENABLED:
        raise LLMOfflineError("ollama")

    model = model or settings.OLLAMA_MODEL
    base_url = settings.OLLAMA_BASE_URL.rstrip("/")

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        start = time.time()
        resp = requests.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        elapsed = time.time() - start

        data = resp.json()
        text = data.get("response", "").strip()

        logger.info(
            "ollama_response",
            model=model,
            elapsed_s=round(elapsed, 2),
            response_len=len(text),
        )
        return text

    except requests.exceptions.Timeout:
        raise LLMTimeoutError(30)
    except requests.exceptions.ConnectionError:
        raise LLMOfflineError("ollama")
    except Exception as exc:
        logger.error("ollama_error", error=str(exc))
        raise LLMOfflineError("ollama") from exc


# ── Unified Public API ────────────────────────────────────────────────────

def generate_response(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    model: Optional[str] = None,
    provider: Optional[str] = None,
) -> str:
    """
    Generate a response using the configured LLM provider.

    Provider priority: Ollama (primary) → Groq → NVIDIA NIM (fallback)

    Args:
        prompt:        User prompt text.
        system_prompt: System / instruction prompt.
        temperature:   Sampling temperature.
        max_tokens:    Max tokens to generate.
        model:         Override the model name (must match the target provider's catalogue).
        provider:      Force a specific provider ("groq" | "nvidia" | "ollama").

    Returns:
        Generated text string.
    """
    settings = get_settings()

    # Determine provider order — Ollama primary, Groq/NVIDIA as fallback
    if provider:
        providers = [provider]
    else:
        providers = []
        if settings.OLLAMA_ENABLED:
            providers.append("ollama")
        if settings.GROQ_API_KEY:
            providers.append("groq")
        if settings.NVIDIA_API_KEY:
            providers.append("nvidia")

    last_error: Optional[Exception] = None

    for p in providers:
        try:
            if p == "groq":
                return _call_groq(prompt, system_prompt, temperature, max_tokens, model)
            elif p == "nvidia":
                return _call_nvidia(prompt, system_prompt, temperature, max_tokens, model)
            elif p == "ollama":
                return _call_ollama(prompt, system_prompt, temperature, max_tokens, model)
        except LLMError as exc:
            last_error = exc
            logger.warning("llm_fallback", failed_provider=p, error=str(exc))
            continue

    # All providers failed — return legacy magic string for backward compat
    if isinstance(last_error, LLMTimeoutError):
        return "__LLM_TIMEOUT__"
    return "__LLM_OFFLINE__"


def get_llm_status() -> dict:
    """
    Check the status of all configured LLM providers.

    Returns:
        Dict with provider availability info.
    """
    settings = get_settings()
    status = {
        "primary_provider": settings.llm_provider,
        "groq_configured": bool(settings.GROQ_API_KEY),
        "groq_model": settings.GROQ_MODEL,
        "nvidia_configured": settings.nvidia_enabled,
        "nvidia_model": settings.NVIDIA_MODEL if settings.nvidia_enabled else None,
        "nvidia_base_url": settings.NVIDIA_BASE_URL if settings.nvidia_enabled else None,
        "ollama_enabled": settings.OLLAMA_ENABLED,
        "ollama_url": settings.OLLAMA_BASE_URL if settings.OLLAMA_ENABLED else None,
        "ollama_model": settings.OLLAMA_MODEL if settings.OLLAMA_ENABLED else None,
    }

    # Quick connectivity check for Ollama (primary)
    if settings.OLLAMA_ENABLED:
        try:
            import requests
            resp = requests.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=5)
            status["ollama_reachable"] = resp.status_code == 200
        except Exception:
            status["ollama_reachable"] = False
    else:
        status["ollama_reachable"] = False

    # Quick connectivity check for Groq
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            client.models.list()
            status["groq_reachable"] = True
        except Exception:
            status["groq_reachable"] = False
    else:
        status["groq_reachable"] = False

    # Quick connectivity check for NVIDIA NIM
    if settings.nvidia_enabled:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=settings.NVIDIA_BASE_URL, api_key=settings.NVIDIA_API_KEY)
            client.models.list()
            status["nvidia_reachable"] = True
        except Exception:
            status["nvidia_reachable"] = False
    else:
        status["nvidia_reachable"] = False

    return status
