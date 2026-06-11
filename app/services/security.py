"""Password hashing and JWT token helpers.

Passwords use bcrypt directly (the `bcrypt` package) rather than passlib — this
avoids the noisy passlib/bcrypt 4.x version-detection warning and keeps the
dependency surface small.

Tokens are stateless JWTs. Each carries `sub` (user id), `role`, `exp`, and a
`type` claim ("access" or "refresh") so the refresh endpoint can reject access
tokens. With more time, refresh tokens would be tracked in a DB allowlist to
support rotation and revocation; here they are deliberately stateless.
"""

import datetime as dt
from typing import Any

import bcrypt
import jwt

from ..config import (
    ACCESS_TOKEN_TTL_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET,
    REFRESH_TOKEN_TTL_DAYS,
)

ACCESS_TOKEN = "access"
REFRESH_TOKEN = "refresh"


# --- passwords ---

def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt; returns a UTF-8 string."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Constant-time check of a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# --- JWT ---

def _create_token(subject: str, role: str, token_type: str, expires_delta: dt.timedelta) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        str(user_id), role, ACCESS_TOKEN,
        dt.timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES),
    )


def create_refresh_token(user_id: int, role: str) -> str:
    return _create_token(
        str(user_id), role, REFRESH_TOKEN,
        dt.timedelta(days=REFRESH_TOKEN_TTL_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt.PyJWTError on any problem."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
