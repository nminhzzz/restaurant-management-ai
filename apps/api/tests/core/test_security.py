from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_is_hashed_and_verifiable() -> None:
    hashed = hash_password("mat-khau-123")

    assert hashed != "mat-khau-123"
    assert verify_password("mat-khau-123", hashed)
    assert not verify_password("sai-mat-khau", hashed)


def test_access_token_round_trip() -> None:
    token = create_access_token("7", {"role": "MANAGER"})

    claims = decode_access_token(token)

    assert claims["sub"] == "7"
    assert claims["role"] == "MANAGER"


def test_expired_token_is_rejected() -> None:
    settings = get_settings()
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired)
