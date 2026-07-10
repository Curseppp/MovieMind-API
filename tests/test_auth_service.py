from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, hash_refresh_token
from app.models import AuthSession, User
from app.services.auth import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    authenticate_user,
    login_user,
    refresh_tokens,
)
from tests.constants import TEST_PASSWORD


def test_authenticate_user_with_correct_credentials(
    db_session: Session,
    user: User,
) -> None:
    authenticated_user = authenticate_user(
        db_session,
        user.email,
        TEST_PASSWORD,
    )

    assert authenticated_user == user


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("user@example.com", "wrong-password"),
        ("missing@example.com", TEST_PASSWORD),
    ],
)
def test_authenticate_user_rejects_invalid_credentials(
    db_session: Session,
    user: User,
    email: str,
    password: str,
) -> None:
    assert authenticate_user(db_session, email, password) is None


def test_login_creates_access_token_and_hashed_refresh_session(
    db_session: Session,
    user: User,
) -> None:
    tokens = login_user(db_session, user.email, TEST_PASSWORD)
    auth_session = db_session.scalar(select(AuthSession))

    assert decode_access_token(tokens.access_token) == user.id
    assert auth_session is not None
    assert auth_session.user_id == user.id
    assert auth_session.refresh_token_hash == hash_refresh_token(tokens.refresh_token)
    assert auth_session.refresh_token_hash != tokens.refresh_token
    assert auth_session.revoked_at is None


def test_login_rejects_invalid_credentials_without_creating_session(
    db_session: Session,
    user: User,
) -> None:
    with pytest.raises(InvalidCredentialsError):
        login_user(db_session, user.email, "wrong-password")

    assert db_session.scalar(select(AuthSession)) is None


def test_refresh_rotates_token_and_rejects_old_token(
    db_session: Session,
    user: User,
) -> None:
    issued_tokens = login_user(db_session, user.email, TEST_PASSWORD)
    auth_session = db_session.scalar(select(AuthSession))
    assert auth_session is not None
    auth_session_id = auth_session.id

    refreshed_tokens = refresh_tokens(db_session, issued_tokens.refresh_token)
    db_session.refresh(auth_session)

    assert refreshed_tokens.refresh_token != issued_tokens.refresh_token
    assert decode_access_token(refreshed_tokens.access_token) == user.id
    assert auth_session.id == auth_session_id
    assert auth_session.refresh_token_hash == hash_refresh_token(
        refreshed_tokens.refresh_token
    )

    with pytest.raises(InvalidRefreshTokenError):
        refresh_tokens(db_session, issued_tokens.refresh_token)


@pytest.mark.parametrize("session_state", ["expired", "revoked"])
def test_refresh_rejects_unusable_session(
    db_session: Session,
    user: User,
    session_state: str,
) -> None:
    tokens = login_user(db_session, user.email, TEST_PASSWORD)
    auth_session = db_session.scalar(select(AuthSession))
    assert auth_session is not None

    if session_state == "expired":
        auth_session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    else:
        auth_session.revoked_at = datetime.now(timezone.utc)
    db_session.commit()

    with pytest.raises(InvalidRefreshTokenError):
        refresh_tokens(db_session, tokens.refresh_token)


def test_refresh_rejects_unknown_token(db_session: Session) -> None:
    with pytest.raises(InvalidRefreshTokenError):
        refresh_tokens(db_session, "unknown-refresh-token")
