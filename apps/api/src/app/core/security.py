"""Password hashing and access-token helpers (NFR-04)."""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def create_access_token(subject: str, extra_claims: dict[str, object] | None = None) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_ttl_minutes),
    }
    payload.update(extra_claims or {})
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, object]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
