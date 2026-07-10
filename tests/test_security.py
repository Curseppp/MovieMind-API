from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def encode_token(payload: dict[str, object], secret: str | None = None) -> str:
    return jwt.encode(
        payload,
        secret or settings.secret_key,
        algorithm=settings.algorithm,
    )


def test_password_hash_can_be_verified() -> None:
    password = "a-secure-test-password"
    hashed_password = hash_password(password)

    assert hashed_password != password
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrong-password", hashed_password) is False


def test_refresh_token_hash_is_deterministic_and_hides_token() -> None:
    refresh_token = "refresh-token-value"

    first_hash = hash_refresh_token(refresh_token)
    second_hash = hash_refresh_token(refresh_token)

    assert first_hash == second_hash
    assert first_hash != refresh_token
    assert len(first_hash) == 64


def test_access_token_round_trip() -> None:
    token = create_access_token(user_id=42)

    assert decode_access_token(token) == 42


def test_expired_access_token_is_rejected() -> None:
    token = encode_token(
        {
            "sub": "42",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


def test_access_token_with_wrong_signature_is_rejected() -> None:
    token = encode_token(
        {
            "sub": "42",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        secret="a-different-secret-that-is-long-enough",
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)


@pytest.mark.parametrize("subject", [None, "not-an-integer"])
def test_access_token_with_invalid_subject_is_rejected(
    subject: str | None,
) -> None:
    token = encode_token(
        {
            "sub": subject,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token)
