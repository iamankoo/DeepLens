import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

ACCESS_TOKEN_TYPE = "access"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(*, user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (expired, malformed, bad signature, ...) on failure."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise jwt.InvalidTokenError("Not an access token")
    return payload


def _hash_token(raw_token: str) -> str:
    # SHA-256, not bcrypt: these are high-entropy random tokens looked up by
    # exact hash match, not low-entropy passwords needing a slow, salted KDF
    # to resist brute-forcing.
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> tuple[str, str, datetime]:
    """Returns (raw_token, token_hash, expires_at). The raw token is
    returned to the client once and never stored; only its hash is
    persisted, so a leaked DB can't be replayed as a bearer credential."""
    raw_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return raw_token, _hash_token(raw_token), expires_at


def hash_refresh_token(raw_token: str) -> str:
    return _hash_token(raw_token)


def generate_email_token(*, expires_delta: timedelta) -> tuple[str, str, datetime]:
    """Same shape/rationale as generate_refresh_token, for password-reset
    and email-verification links: (raw_token, token_hash, expires_at)."""
    raw_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + expires_delta
    return raw_token, _hash_token(raw_token), expires_at


def hash_email_token(raw_token: str) -> str:
    return _hash_token(raw_token)
