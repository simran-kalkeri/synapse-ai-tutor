"""
LLM Client for Synapse AI Tutor.
Primary: Groq API (cloud, fast inference)
Fallback: Ollama (local, optional)

Replaces backend/llm_client.py with proper error handling,
structured logging, and Groq as primary provider.

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

    Provider priority: Groq (primary) → Ollama (fallback)

    Args:
        prompt: User prompt text.
        system_prompt: System/instruction prompt.
        temperature: Sampling temperature.
        max_tokens: Max tokens to generate.
        model: Override the model name.
        provider: Force a specific provider ("groq" or "ollama").

    Returns:
        Generated text string.

    Note:
        For backward compatibility, this function catches LLM errors
        and returns the legacy magic strings when called from old code
        paths. New code should catch LLMError exceptions instead.
    """
    settings = get_settings()

    # Determine provider order
    if provider:
        providers = [provider]
    elif settings.GROQ_API_KEY:
        providers = ["groq"]
        if settings.OLLAMA_ENABLED:
            providers.append("ollama")
    elif settings.OLLAMA_ENABLED:
        providers = ["ollama"]
    else:
        providers = []

    last_error: Optional[Exception] = None

    for p in providers:
        try:
            if p == "groq":
                return _call_groq(prompt, system_prompt, temperature, max_tokens, model)
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
    Check the status of configured LLM providers.

    Returns:
        Dict with provider availability info.
    """
    settings = get_settings()
    status = {
        "primary_provider": settings.llm_provider,
        "groq_configured": bool(settings.GROQ_API_KEY),
        "groq_model": settings.GROQ_MODEL,
        "ollama_enabled": settings.OLLAMA_ENABLED,
        "ollama_url": settings.OLLAMA_BASE_URL if settings.OLLAMA_ENABLED else None,
        "ollama_model": settings.OLLAMA_MODEL if settings.OLLAMA_ENABLED else None,
    }

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

    return status
