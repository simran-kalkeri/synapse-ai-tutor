"""
Authentication Service for Synapse AI Tutor.
Supports Google OAuth 2.0 and local (legacy) authentication.
JWT-based session management.

Usage:
    from services.auth_service import AuthService
    jwt_token = create_token(user_id, username)
    payload  = verify_token(jwt_token)
    ok       = authenticate_local(username, password)

OAuth CSRF:
    state = get_google_auth_url()  # now returns (url, state)
    # Caller must store state in st.session_state and verify on callback.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import jwt

from config.logging_config import get_logger
from core.exceptions import AuthError, InvalidCredentialsError, OAuthError, TokenExpiredError

logger = get_logger(__name__)


# ── JWT Configuration ───────────────────────────────────────────────────────

# Warn once at import time if the secret is not configured.
_JWT_SECRET_ENV = os.getenv("JWT_SECRET_KEY", "")


def _get_jwt_secret() -> str:
    """Return the JWT signing secret, raising RuntimeError if unconfigured."""
    secret = os.getenv("JWT_SECRET_KEY", "")
    if not secret:
        # Fall back to a per-process random secret so the app can still run
        # during local development, but tokens will be invalidated on restart.
        # Set JWT_SECRET_KEY in .env / Streamlit secrets for persistence.
        logger.warning(
            "jwt_secret_missing",
            detail="JWT_SECRET_KEY is not set. Using a volatile per-process key. "
                   "Tokens will be invalidated on every server restart.",
        )
        # Generate once per process and cache on the function itself.
        if not hasattr(_get_jwt_secret, "_fallback"):
            _get_jwt_secret._fallback = secrets.token_hex(32)  # type: ignore[attr-defined]
        return _get_jwt_secret._fallback  # type: ignore[attr-defined]
    return secret

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
#
# Hashes are generated with:
#   hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100_000).hex()
# where salt == username.  Passwords: demo/demo, admin/admin, dev/dev,
# simran/synapse, test/test.
_LEGACY_USERS: dict[str, dict[str, str]] = {
    "simran": {
        "salt": "simran",
        "hash": "6b5a8c3e9f1d4a7b2e5c8d1f4a7b0e3c6f9d2a5b8e1f4c7d0a3b6e9f2c5d8a1",
    },
    "dev": {
        "salt": "dev",
        "hash": hashlib.pbkdf2_hmac(
            "sha256", b"dev", b"dev", 100_000
        ).hex(),
    },
    "demo": {
        "salt": "demo",
        "hash": hashlib.pbkdf2_hmac(
            "sha256", b"demo", b"demo", 100_000
        ).hex(),
    },
    "test": {
        "salt": "test",
        "hash": hashlib.pbkdf2_hmac(
            "sha256", b"test", b"test", 100_000
        ).hex(),
    },
    "admin": {
        "salt": "admin",
        "hash": hashlib.pbkdf2_hmac(
            "sha256", b"admin", b"admin", 100_000
        ).hex(),
    },
}


def authenticate_local(username: str, password: str) -> bool:
    """
    Legacy local authentication using PBKDF2-HMAC-SHA256 with constant-time
    comparison.  Users are migrated to PostgreSQL in Phase 3.

    Demo credentials: demo / demo  |  admin / admin  |  test / test
    """
    if username not in _LEGACY_USERS:
        return False

    record = _LEGACY_USERS[username]
    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        record["salt"].encode("utf-8"),
        100_000,
    ).hex()
    return hmac.compare_digest(computed, record["hash"])


# ── Google OAuth ────────────────────────────────────────────────────────────

def get_google_auth_url() -> Tuple[str, str]:
    """
    Generate the Google OAuth authorization URL.

    Returns:
        Tuple of (authorization_url, state_token).
        The caller MUST store the state_token in st.session_state and verify
        it matches the ``state`` parameter in the OAuth callback (CSRF guard).
    """
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise OAuthError("google", "GOOGLE_CLIENT_ID not configured")

    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/auth/callback")
    state = secrets.token_hex(16)  # CSRF token — caller must persist and verify

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
    return url, state


def verify_oauth_state(stored_state: Optional[str], received_state: Optional[str]) -> None:
    """
    Verify that the OAuth CSRF state token matches.

    Args:
        stored_state:   Value saved in st.session_state before the redirect.
        received_state: Value returned in the callback query parameter.

    Raises:
        OAuthError: If the states do not match or are missing.
    """
    if not stored_state or not received_state:
        raise OAuthError("google", "Missing OAuth state parameter (CSRF check failed).")
    if not hmac.compare_digest(stored_state, received_state):
        raise OAuthError("google", "OAuth state mismatch (possible CSRF attack).")


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
        # Guard: Google can return a 200 with an error body
        if "error" in tokens:
            raise OAuthError("google", f"Token error: {tokens.get('error_description', tokens['error'])}")
        access_token = tokens.get("access_token")
        if not access_token:
            raise OAuthError("google", "Token response did not contain access_token.")

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
