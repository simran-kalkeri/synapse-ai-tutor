"""
Authentication Service for Synapse AI Tutor.
Supports Google OAuth 2.0 and local (legacy) authentication.
JWT-based session management.

Usage:
    from services.auth_service import AuthService
    auth = AuthService()
    jwt_token = await auth.google_oauth_callback(code)
    user = auth.verify_token(jwt_token)
"""

from __future__ import annotations

import hashlib
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from config.logging_config import get_logger
from core.exceptions import AuthError, InvalidCredentialsError, OAuthError, TokenExpiredError

logger = get_logger(__name__)


# ── JWT Configuration ───────────────────────────────────────────────────────

def _get_jwt_secret() -> str:
    return os.getenv("JWT_SECRET_KEY", "change-me-to-a-random-64-char-string")

def _get_jwt_expiry_hours() -> int:
    return int(os.getenv("JWT_EXPIRY_HOURS", "168"))


# ── JWT Token Management ───────────────────────────────────────────────────

def create_token(user_id: str, username: str, email: str = "",
                 provider: str = "local") -> str:
    """
    Create a JWT token for an authenticated user.

    Args:
        user_id: User's UUID as string.
        username: Username.
        email: User's email.
        provider: Auth provider (local, google, github).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "provider": provider,
        "iat": now,
        "exp": now + timedelta(hours=_get_jwt_expiry_hours()),
        "jti": secrets.token_hex(16),
    }
    token = jwt.encode(payload, _get_jwt_secret(), algorithm="HS256")
    logger.info("jwt_created", username=username, provider=provider)
    return token


def verify_token(token: str) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT string.

    Returns:
        Decoded payload dict with keys: sub, username, email, provider.

    Raises:
        TokenExpiredError: If token has expired.
        AuthError: If token is invalid.
    """
    try:
        payload = jwt.decode(token, _get_jwt_secret(), algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {e}")


# ── Legacy Local Auth (backward compatible with existing auth.py) ────────

# Preserved from backend/auth.py for backward compatibility.
# These users exist until they are migrated to PostgreSQL.
_LEGACY_USERS = {
    "simran": "pbkdf2:sha256:600000$GxK3qz$c3f8a4d1b7e9c2f5d8a0b3e6f9c2d5a8b1e4f7c0d3a6b9e2f5c8d1a4b7e0f3",
    "dev": "pbkdf2:sha256:600000$test$a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1",
    "demo": "pbkdf2:sha256:600000$demo$f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0",
    "test": "pbkdf2:sha256:600000$test$1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    "admin": "pbkdf2:sha256:600000$admin$fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
}


def authenticate_local(username: str, password: str) -> bool:
    """
    Legacy local authentication.
    Checks against the hardcoded user list (backward compatible).

    In production, this should check against the PostgreSQL users table
    with proper bcrypt password hashing.
    """
    if username not in _LEGACY_USERS:
        return False
    # For the demo, accept any password for known users
    # TODO: Replace with proper password verification after Phase 3
    return True


# ── Google OAuth ────────────────────────────────────────────────────────────

def get_google_auth_url() -> str:
    """
    Generate the Google OAuth authorization URL.

    Returns:
        Authorization URL to redirect the user to.
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise OAuthError("google", "GOOGLE_CLIENT_ID not configured")

    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/auth/callback")
    state = secrets.token_hex(16)

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    from urllib.parse import urlencode
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return url


async def exchange_google_code(code: str) -> dict:
    """
    Exchange Google OAuth authorization code for user info.

    Args:
        code: Authorization code from Google callback.

    Returns:
        Dict with keys: email, name, picture, provider_id.
    """
    import httpx

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/auth/callback")

    if not client_id or not client_secret:
        raise OAuthError("google", "OAuth credentials not configured")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )

        if token_resp.status_code != 200:
            raise OAuthError("google", f"Token exchange failed: {token_resp.text}")

        tokens = token_resp.json()
        access_token = tokens["access_token"]

        # Get user info
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_resp.status_code != 200:
            raise OAuthError("google", f"Userinfo failed: {userinfo_resp.text}")

        userinfo = userinfo_resp.json()

    return {
        "email": userinfo.get("email", ""),
        "name": userinfo.get("name", ""),
        "picture": userinfo.get("picture", ""),
        "provider_id": userinfo.get("sub", ""),
    }


def is_google_oauth_configured() -> bool:
    """Check if Google OAuth credentials are configured."""
    return bool(os.getenv("GOOGLE_CLIENT_ID")) and bool(os.getenv("GOOGLE_CLIENT_SECRET"))
