"""
Authentication module for Synapse AI Tutor.
Uses hardcoded credentials with Streamlit session_state.
"""

import hashlib
import hmac

# Secure salted PBKDF2 credentials
USERS = {
    "user1": {"salt": "user1", "hash": "735557894d613cb77b8389851afaec87f00262eee972d7517a90326a9fa9f19b"},
    "user2": {"salt": "user2", "hash": "4b7f11fe943e7572d3a33dcb97af3636b5bbc6400f1c0acd75418115925f3337"},
    "user3": {"salt": "user3", "hash": "20bfdfeb88e42d805854494052f5451c42b0321782a2f6d1c25f9f6ae56d1154"},
    "user4": {"salt": "user4", "hash": "716f61cee48f50f0f4f3d50482930b543a8a96313d841ba3c2869fe1e2d0e6e0"},
    "demo":  {"salt": "demo",  "hash": "078ed31b5646b2f14bddfa5c47ae9fa71eb1a5e3985a58d2e9ed164d0cbb48f1"}
}


def authenticate(username: str, password: str) -> bool:
    """
    Authenticate a user against secure pre-hashed credentials.
    Uses PBKDF2-HMAC-SHA256 and constant-time string comparison.
    
    Args:
        username: The username to authenticate
        password: The password to verify
        
    Returns:
        True if credentials are valid, False otherwise
    """
    if username not in USERS:
        return False
    
    record = USERS[username]
    salt = record["salt"]
    stored_hash = record["hash"]
    
    computed_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    
    return hmac.compare_digest(computed_hash, stored_hash)


def get_all_users() -> list:
    """Return list of all registered usernames."""
    return list(USERS.keys())
