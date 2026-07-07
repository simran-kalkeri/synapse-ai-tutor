"""
Auth router — login, register, token refresh, logout, me.
Persistence: users stored in synapse_ai_tutor/data/users.json (atomic writes).
             refresh tokens in synapse_ai_tutor/data/refresh_tokens.json.
"""
from __future__ import annotations

import json
import os
import pathlib as _pathlib
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt
import bcrypt as _bcrypt

from dependencies import get_username, JWT_SECRET_KEY, JWT_ALGORITHM
from services.auth_service import verify_oauth_state
from .rate_limiter import get_rate_limiter
from schemas import LoginRequest, RegisterRequest, TokenResponse, RefreshRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS   = 7

# Absolute data directory — same anchor as all other backend routers
_DATA_DIR = _pathlib.Path(__file__).resolve().parent.parent.parent.parent / "synapse_ai_tutor" / "data"
_USERS_FILE    = _DATA_DIR / "users.json"
_TOKENS_FILE   = _DATA_DIR / "refresh_tokens.json"

# ── Password hashing ───────────────────────────────────────────────────────────
# Uses the `bcrypt` library directly — compatible with bcrypt>=4.0.0 / Python 3.13.
# passlib 1.7.x has a known incompatibility with bcrypt>=4.0.0 (__about__ removal).

def _hash_password(password: str) -> str:
    """Hash password with bcrypt (industry standard, unique salt per hash)."""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

def _verify_password(plain: str, hashed: str) -> bool:
    """Verify password against a bcrypt hash."""
    if not (hashed.startswith("$2b$") or hashed.startswith("$2a$") or hashed.startswith("$2y$")):
        return False
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _atomic_write(filepath: _pathlib.Path, data) -> None:
    """Atomic JSON write via tempfile + os.replace()."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(filepath.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, str(filepath))
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise

# ── Persistent user store ──────────────────────────────────────────────────────

_DEMO_CREDENTIALS = {
    "demo": "demo123",
    "admin": "admin123",
    "student": "student123",
}


def _make_demo_users() -> dict:
    """Create demo accounts matching the documented demo credentials."""
    return {
        "demo":    {"id": "00000000-0000-0000-0000-000000000001", "username": "demo",    "email": "demo@synapse.ai",    "display_name": "Demo User", "password_hash": _hash_password(_DEMO_CREDENTIALS["demo"]), "created_at": "2024-01-01T00:00:00Z"},
        "admin":   {"id": "00000000-0000-0000-0000-000000000002", "username": "admin",   "email": "admin@synapse.ai",   "display_name": "Admin",     "password_hash": _hash_password(_DEMO_CREDENTIALS["admin"]), "created_at": "2024-01-01T00:00:00Z"},
        "student": {"id": "00000000-0000-0000-0000-000000000003", "username": "student", "email": "student@synapse.ai", "display_name": "Student",   "password_hash": _hash_password(_DEMO_CREDENTIALS["student"]), "created_at": "2024-01-01T00:00:00Z"},
    }


def _repair_demo_users(users: dict) -> bool:
    """Keep bundled review/demo accounts aligned with documented passwords."""
    changed = False
    defaults = None
    for username, password in _DEMO_CREDENTIALS.items():
        user = users.get(username)
        if not user:
            if defaults is None:
                defaults = _make_demo_users()
            users[username] = defaults[username]
            changed = True
            continue

        if not _verify_password(password, user.get("password_hash", "")):
            if defaults is None:
                defaults = _make_demo_users()
            user["password_hash"] = defaults[username]["password_hash"]
            changed = True

        for key in ("id", "username", "email", "display_name", "created_at"):
            if not user.get(key):
                if defaults is None:
                    defaults = _make_demo_users()
                user[key] = defaults[username][key]
                changed = True
    return changed

def _load_users() -> dict:
    if _USERS_FILE.exists():
        try:
            users = json.loads(_USERS_FILE.read_text(encoding="utf-8"))
            if _repair_demo_users(users):
                _atomic_write(_USERS_FILE, users)
            return users
        except Exception:
            pass
    # First run — seed demo accounts with properly hashed passwords
    demo = _make_demo_users()
    _atomic_write(_USERS_FILE, demo)
    return dict(demo)

def _save_users(data: dict) -> None:
    _atomic_write(_USERS_FILE, data)

# ── Persistent refresh token store ─────────────────────────────────────────────

def _load_refresh_tokens() -> set:
    if _TOKENS_FILE.exists():
        try:
            return set(json.loads(_TOKENS_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()

def _save_refresh_tokens(tokens: set) -> None:
    _atomic_write(_TOKENS_FILE, list(tokens))


def _make_token(subject: str, expires_delta: timedelta, token_type: str = "access") -> str:
    expire  = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "exp": expire, "type": token_type, "jti": str(uuid.uuid4())}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def _issue_tokens(username: str) -> TokenResponse:
    access  = _make_token(username, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")
    refresh = _make_token(username, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "refresh")
    tokens = _load_refresh_tokens()
    tokens.add(refresh)
    _save_refresh_tokens(tokens)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse, summary="Login")
async def login(body: LoginRequest):
    """
    Authenticate with username + password.
    Checks the persistent JSON user store (users.json).
    Falls back to the legacy Streamlit auth module for users created before
    the JSON store was introduced.
    """
    limiter = get_rate_limiter()
    if not limiter.check(f"login:{body.username}"):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    users = _load_users()

    # 1. Check persistent user store (primary)
    user = users.get(body.username)
    if user and _verify_password(body.password, user.get("password_hash", "")):
        return _issue_tokens(body.username)

    # 2. Try legacy Streamlit auth (covers accounts created before persistence)
    try:
        from backend.auth import authenticate as legacy_auth   # type: ignore
        if legacy_auth(body.username, body.password):
            # Migrate to persistent store on successful legacy login
            if body.username not in users:
                users[body.username] = {
                    "id":           str(uuid.uuid4()),
                    "username":     body.username,
                    "email":        None,
                    "display_name": body.username.capitalize(),
                    "created_at":   datetime.now(timezone.utc).isoformat(),
                }
                _save_users(users)
            return _issue_tokens(body.username)
    except ImportError:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
    )


@router.post("/register", response_model=TokenResponse, summary="Register")
async def register(request: Request, body: RegisterRequest):
    """Register a new user account (persisted to users.json)."""
    limiter = get_rate_limiter()
    if not limiter.check(f"register:{request.client.host}", max_requests=3, window_seconds=300):
        raise HTTPException(status_code=429, detail="Too many registration attempts. Try again later.")

    users = _load_users()
    if body.username in users:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    users[body.username] = {
        "id":           str(uuid.uuid4()),
        "username":     body.username,
        "email":        body.email,
        "display_name": body.display_name or body.username.capitalize(),
        "password_hash": _hash_password(body.password),
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }
    _save_users(users)
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
        tokens = _load_refresh_tokens()
        if body.refresh_token not in tokens:
            raise HTTPException(status_code=401, detail="Refresh token not recognized or already revoked")
        tokens.discard(body.refresh_token)
        _save_refresh_tokens(tokens)
        return _issue_tokens(username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.post("/logout", summary="Logout")
async def logout(body: RefreshRequest):
    """Invalidate the given refresh token."""
    tokens = _load_refresh_tokens()
    tokens.discard(body.refresh_token)
    _save_refresh_tokens(tokens)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse, summary="Current user")
async def get_me(username: str = Depends(get_username)):
    """Return the profile of the currently authenticated user."""
    users = _load_users()
    user = users.get(username, {
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


# ── Google OAuth ───────────────────────────────────────────────────────────────

@router.get("/google", summary="Initiate Google OAuth")
async def google_oauth_init():
    """Redirect the user to Google OAuth."""
    try:
        from services.auth_service import get_google_auth_url, is_google_oauth_configured  # type: ignore
        if not is_google_oauth_configured():
            raise HTTPException(
                status_code=501,
                detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
            )
        url, state = get_google_auth_url()
        return {"auth_url": url, "state": state}
    except ImportError:
        raise HTTPException(status_code=501, detail="OAuth service not available")


@router.get("/google/callback", response_model=TokenResponse, summary="Google OAuth callback")
async def google_oauth_callback(request: Request, code: str, state: str):
    """Handle the Google OAuth callback and issue JWT tokens."""
    try:
        import httpx  # noqa: F401  (imported to confirm httpx is available)
        from services.auth_service import exchange_google_code  # type: ignore
        stored_state = request.headers.get("X-OAuth-State")
        verify_oauth_state(stored_state, state)
        user_info = await exchange_google_code(code)
        username = user_info.get("email", "").split("@")[0]
        users = _load_users()
        if username not in users:
            users[username] = {
                "id":           str(uuid.uuid4()),
                "username":     username,
                "email":        user_info.get("email"),
                "display_name": user_info.get("name", username.capitalize()),
                "avatar_url":   user_info.get("picture"),
                "created_at":   datetime.now(timezone.utc).isoformat(),
            }
            _save_users(users)
        return _issue_tokens(username)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"OAuth failed: {e}")
