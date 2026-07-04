"""
Auth router — login, register, token refresh, logout, me.
"""
from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt

from dependencies import get_username, JWT_SECRET_KEY, JWT_ALGORITHM
from schemas import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS   = 7
_SALT = "synapse_salt_v1"

# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), _SALT.encode(), 100_000).hex()

def _verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(_hash_password(password), hashed)

def _make_token(subject: str, expires_delta: timedelta, token_type: str = "access") -> str:
    expire  = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "exp": expire, "type": token_type, "jti": str(uuid.uuid4())}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def _issue_tokens(username: str) -> TokenResponse:
    access  = _make_token(username, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")
    refresh = _make_token(username, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")
    _REFRESH_TOKENS.add(refresh)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

# ── In-memory stores ───────────────────────────────────────────────────────────

_REFRESH_TOKENS: set[str] = set()

# Pre-seeded demo accounts (work without a database)
_USERS: dict[str, dict] = {
    "demo": {
        "id":           "00000000-0000-0000-0000-000000000001",
        "username":     "demo",
        "email":        "demo@synapse.ai",
        "display_name": "Demo User",
        "password_hash": _hash_password("demo123"),
        "created_at":   "2024-01-01T00:00:00Z",
    },
    "admin": {
        "id":           "00000000-0000-0000-0000-000000000002",
        "username":     "admin",
        "email":        "admin@synapse.ai",
        "display_name": "Admin",
        "password_hash": _hash_password("admin123"),
        "created_at":   "2024-01-01T00:00:00Z",
    },
    "student": {
        "id":           "00000000-0000-0000-0000-000000000003",
        "username":     "student",
        "email":        "student@synapse.ai",
        "display_name": "Student",
        "password_hash": _hash_password("student123"),
        "created_at":   "2024-01-01T00:00:00Z",
    },
}

# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse, summary="Login")
async def login(body: LoginRequest):
    """
    Authenticate with username + password.
    Falls back to the legacy Streamlit auth module if available,
    otherwise checks the in-memory user store.
    """
    # 1. Try legacy Streamlit auth (uses per-user PBKDF2 salts)
    try:
        from backend.auth import authenticate as legacy_auth   # type: ignore
        if legacy_auth(body.username, body.password):
            if body.username not in _USERS:
                _USERS[body.username] = {
                    "id":           str(uuid.uuid4()),
                    "username":     body.username,
                    "email":        None,
                    "display_name": body.username.capitalize(),
                    "created_at":   datetime.now(timezone.utc).isoformat(),
                }
            return _issue_tokens(body.username)
    except ImportError:
        pass

    # 2. Check in-memory store
    user = _USERS.get(body.username)
    if user and _verify_password(body.password, user.get("password_hash", "")):
        return _issue_tokens(body.username)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
    )


@router.post("/register", response_model=TokenResponse, summary="Register")
async def register(body: RegisterRequest):
    """Register a new user account (stored in-memory)."""
    if body.username in _USERS:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    _USERS[body.username] = {
        "id":           str(uuid.uuid4()),
        "username":     body.username,
        "email":        body.email,
        "display_name": body.display_name or body.username.capitalize(),
        "password_hash": _hash_password(body.password),
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }
    return _issue_tokens(body.username)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh token")
async def refresh_token(body: RefreshRequest):
    """Exchange a valid refresh token for a new access + refresh pair."""
    from jose import JWTError
    try:
        payload  = jwt.decode(body.refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        _REFRESH_TOKENS.discard(body.refresh_token)
        return _issue_tokens(username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.post("/logout", summary="Logout")
async def logout(body: RefreshRequest):
    """Invalidate the given refresh token."""
    _REFRESH_TOKENS.discard(body.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse, summary="Current user")
async def get_me(username: str = Depends(get_username)):
    """Return the profile of the currently authenticated user."""
    user = _USERS.get(username, {
        "id":           str(uuid.uuid5(uuid.NAMESPACE_DNS, username)),
        "username":     username,
        "email":        None,
        "display_name": username.capitalize(),
        "created_at":   None,
    })
    return UserResponse(
        id=user.get("id", str(uuid.uuid4())),
        username=username,
        email=user.get("email"),
        display_name=user.get("display_name", username.capitalize()),
        avatar_url=user.get("avatar_url"),
        created_at=user.get("created_at"),
    )
