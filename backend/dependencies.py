"""
FastAPI dependency injection providers.
All shared resources are accessed through these functions.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional, Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from jose import JWTError, jwt

# JWT config
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-to-a-random-64-char-string")
JWT_ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


# ── RAG Pipeline ──────────────────────────────────────────────────────────────

def get_rag_pipeline(request: Request):
    """Return the RAGPipeline singleton (may be None if not initialised)."""
    return getattr(request.app.state, "rag_pipeline", None)


def get_knowledge_graph(request: Request):
    """Return the NetworkX knowledge graph singleton (may be None)."""
    return getattr(request.app.state, "knowledge_graph", None)


# ── Authentication ────────────────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """
    Strict auth dependency — raises 401 if token missing or invalid.
    Returns the decoded JWT payload dict with at least 'sub' (username).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Optional auth — returns None if no token present; raises 401 on invalid token.
    """
    if credentials is None:
        return None
    return decode_token(credentials.credentials)


def get_username(current_user: dict = Depends(get_current_user)) -> str:
    """Convenience dependency — extracts 'sub' (username) from JWT payload."""
    username = current_user.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return username
