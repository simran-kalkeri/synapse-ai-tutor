"""
Centralized application settings using pydantic-settings.
Single source of truth for ALL configuration.

Usage:
    from config.settings import get_settings
    settings = get_settings()
    print(settings.GROQ_API_KEY)
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the project root (synapse_ai_tutor/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """All application configuration, loaded from .env + environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ───────────────────────────────────────────────────────
    APP_NAME: str = "Synapse AI Tutor"
    APP_ENV: str = "development"   # development | staging | production
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"     # console | json

    # ── Paths ─────────────────────────────────────────────────────────────
    PROJECT_ROOT: Path = _PROJECT_ROOT
    DATA_DIR: Path = _PROJECT_ROOT / "data"
    BOOKS_DIR: Path = _PROJECT_ROOT / "data" / "books"
    NOTES_DIR: Path = _PROJECT_ROOT / "data" / "notes"
    STATIC_DIR: Path = _PROJECT_ROOT / "static"

    # ── LLM — Ollama (Primary) ──────────────────────────────────────────
    # Remote Ollama server used for all LLM operations.
    OLLAMA_ENABLED: bool = True
    OLLAMA_BASE_URL: str = "http://10.1.17.65:11434"
    OLLAMA_MODEL: str = "llama3"

    # ── LLM — Groq (Fallback) ───────────────────────────────────────────
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_TEMPERATURE: float = 0.7
    GROQ_MAX_TOKENS: int = 4096

    # ── LLM — NVIDIA NIM (Secondary fallback) ───────────────────────────
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MAX_TOKENS: int = 4096
    NVIDIA_TEMPERATURE: float = 0.6

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://synapse:synapse@localhost:5432/synapse_db"
    DATABASE_URL_SYNC: str = "postgresql://synapse:synapse@localhost:5432/synapse_db"

    # ── Authentication ────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    JWT_EXPIRY_HOURS: int = 168  # 7 days

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── Voice ─────────────────────────────────────────────────────────────
    VOICE_MODE: str = "premium"
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    GROQ_STT_MODEL: str = "whisper-large-v3"
    ELEVENLABS_ENABLED: bool = False
    ELEVENLABS_API_KEY: Optional[str] = None
    TTS_LANG: str = "en"

    # ── Embedding / RAG ───────────────────────────────────────────────────
    # IMPORTANT: This MUST match the model used to build the FAISS index.
    # Currently: BAAI/bge-large-en-v1.5 (1024-dim vectors, higher quality)
    # If you change this, delete data/chunks.pkl and data/faiss_index.bin
    # and restart the backend to rebuild the index.
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    FAISS_INDEX_PATH: Optional[Path] = None
    CHUNKS_PATH: Optional[Path] = None
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    RAG_TOP_K: int = 5


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Derive default paths from DATA_DIR if not explicitly set
        if self.FAISS_INDEX_PATH is None:
            object.__setattr__(self, "FAISS_INDEX_PATH", self.DATA_DIR / "faiss_index.bin")
        if self.CHUNKS_PATH is None:
            object.__setattr__(self, "CHUNKS_PATH", self.DATA_DIR / "chunks.pkl")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def llm_provider(self) -> str:
        """Return the primary active LLM provider name."""
        if self.OLLAMA_ENABLED:
            return "ollama"
        if self.GROQ_API_KEY:
            return "groq"
        if self.NVIDIA_API_KEY:
            return "nvidia"
        return "none"

    @property
    def nvidia_enabled(self) -> bool:
        """True when the NVIDIA NIM API is configured."""
        return bool(self.NVIDIA_API_KEY)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get the application settings singleton.
    Cached so .env is only read once per process.
    """
    return Settings()
