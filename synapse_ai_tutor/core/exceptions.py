"""
Custom exception hierarchy for Synapse AI Tutor.
Replaces magic strings (__LLM_OFFLINE__, __LLM_TIMEOUT__, etc.)
with proper, catchable exceptions.
"""

from __future__ import annotations


class SynapseError(Exception):
    """Base exception for all Synapse errors."""

    def __init__(self, message: str = "", code: str = "SYNAPSE_ERROR"):
        self.code = code
        super().__init__(message)


# ── LLM Errors ──────────────────────────────────────────────────────────────

class LLMError(SynapseError):
    """Base for all LLM-related errors."""

    def __init__(self, message: str = "LLM error", code: str = "LLM_ERROR"):
        super().__init__(message, code)


class LLMOfflineError(LLMError):
    """LLM server is unreachable."""

    def __init__(self, provider: str = "unknown"):
        super().__init__(
            f"LLM provider '{provider}' is offline or unreachable.",
            "LLM_OFFLINE",
        )
        self.provider = provider


class LLMTimeoutError(LLMError):
    """LLM request timed out."""

    def __init__(self, timeout_seconds: float = 0):
        super().__init__(
            f"LLM request timed out after {timeout_seconds}s.",
            "LLM_TIMEOUT",
        )
        self.timeout_seconds = timeout_seconds


class LLMRateLimitError(LLMError):
    """LLM rate limit exceeded."""

    def __init__(self, retry_after: float = 0):
        super().__init__(
            f"LLM rate limit exceeded. Retry after {retry_after}s.",
            "LLM_RATE_LIMIT",
        )
        self.retry_after = retry_after


class LLMResponseError(LLMError):
    """LLM returned an unparseable or invalid response."""

    def __init__(self, message: str = "Invalid LLM response"):
        super().__init__(message, "LLM_RESPONSE_ERROR")


# ── RAG Errors ──────────────────────────────────────────────────────────────

class RAGError(SynapseError):
    """Base for RAG pipeline errors."""

    def __init__(self, message: str = "RAG error", code: str = "RAG_ERROR"):
        super().__init__(message, code)


class RAGNotReadyError(RAGError):
    """RAG pipeline has not been initialized."""

    def __init__(self):
        super().__init__(
            "RAG pipeline is not initialized. Upload documents first.",
            "RAG_NOT_READY",
        )


class RAGIndexError(RAGError):
    """FAISS index is missing or corrupted."""

    def __init__(self, path: str = ""):
        super().__init__(
            f"FAISS index not found or corrupted: {path}",
            "RAG_INDEX_ERROR",
        )


# ── Storage Errors ──────────────────────────────────────────────────────────

class StorageError(SynapseError):
    """Base for data storage errors."""

    def __init__(self, message: str = "Storage error", code: str = "STORAGE_ERROR"):
        super().__init__(message, code)


class StorageCorruptionError(StorageError):
    """Data file is corrupted or unparseable."""

    def __init__(self, filepath: str = ""):
        super().__init__(
            f"Data file corrupted: {filepath}",
            "STORAGE_CORRUPTION",
        )


class StorageWriteError(StorageError):
    """Failed to write data to storage."""

    def __init__(self, filepath: str = "", reason: str = ""):
        super().__init__(
            f"Write failed for {filepath}: {reason}",
            "STORAGE_WRITE_ERROR",
        )


# ── Auth Errors ─────────────────────────────────────────────────────────────

class AuthError(SynapseError):
    """Base for authentication errors."""

    def __init__(self, message: str = "Authentication error", code: str = "AUTH_ERROR"):
        super().__init__(message, code)


class InvalidCredentialsError(AuthError):
    """Invalid username or password."""

    def __init__(self):
        super().__init__("Invalid credentials.", "AUTH_INVALID_CREDENTIALS")


class TokenExpiredError(AuthError):
    """JWT token has expired."""

    def __init__(self):
        super().__init__("Session expired. Please log in again.", "AUTH_TOKEN_EXPIRED")


class OAuthError(AuthError):
    """OAuth flow failed."""

    def __init__(self, provider: str = "", reason: str = ""):
        super().__init__(
            f"OAuth error with {provider}: {reason}",
            "AUTH_OAUTH_ERROR",
        )
        self.provider = provider


# ── Voice Errors ────────────────────────────────────────────────────────────

class VoiceError(SynapseError):
    """Base for voice processing errors."""

    def __init__(self, message: str = "Voice error", code: str = "VOICE_ERROR"):
        super().__init__(message, code)


class STTError(VoiceError):
    """Speech-to-text failed."""

    def __init__(self, message: str = "Speech recognition failed"):
        super().__init__(message, "STT_ERROR")


class TTSError(VoiceError):
    """Text-to-speech failed."""

    def __init__(self, message: str = "Speech synthesis failed"):
        super().__init__(message, "TTS_ERROR")
