"""Password hashing + JWT helpers.

We use bcrypt directly (not passlib) because passlib 1.7.4 is unmaintained and
crashes against bcrypt >= 4.1: its `detect_wrap_bug` probe hashes a >72-byte
secret at import time, which modern bcrypt rejects. The bcrypt API we need
is tiny (hashpw / checkpw), so passlib bought us nothing here.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    if not isinstance(token, str):
        return None
    try:
        # The application chooses the algorithm, never the untrusted JWT header.
        # Preserve existing issuer claims/key/TTL and optional-auth semantics.
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        return subject if isinstance(subject, str) else None
    except (jwt.InvalidTokenError, TypeError, ValueError, OverflowError):
        return None
