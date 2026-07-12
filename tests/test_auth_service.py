from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, hash_refresh_token
from app.models import AuthSession, User
from app.models.user import RefreshToken
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


def get_refresh_token_record(
    db_session: Session,
    refresh_token: str,
) -> RefreshToken:
    token = db_session.scalar(
        select(RefreshToken).where(
            RefreshToken.refresh_token_hash == hash_refresh_token(refresh_token)
        )
    )
    assert token is not None
    return token


def test_login_creates_session_and_hashed_refresh_token(
    db_session: Session,
    user: User,
) -> None:
    tokens = login_user(db_session, user.email, TEST_PASSWORD)
    auth_session = db_session.scalar(select(AuthSession))
    refresh_token = get_refresh_token_record(db_session, tokens.refresh_token)

    assert decode_access_token(tokens.access_token) == user.id
    assert auth_session is not None
    assert auth_session.user_id == user.id
    assert auth_session.revoked_at is None
    assert refresh_token.session_id == auth_session.id
    assert refresh_token.refresh_token_hash == hash_refresh_token(tokens.refresh_token)
    assert refresh_token.refresh_token_hash != tokens.refresh_token
    assert refresh_token.revoked_at is None


def test_login_rejects_invalid_credentials_without_creating_session(
    db_session: Session,
    user: User,
) -> None:
    with pytest.raises(InvalidCredentialsError):
        login_user(db_session, user.email, "wrong-password")

    assert db_session.scalar(select(AuthSession)) is None
    assert db_session.scalar(select(RefreshToken)) is None


def test_refresh_rotates_token_and_rejects_old_token(
    db_session: Session,
    user: User,
) -> None:
    issued_tokens = login_user(db_session, user.email, TEST_PASSWORD)
    auth_session = db_session.scalar(select(AuthSession))
    assert auth_session is not None
    old_token = get_refresh_token_record(db_session, issued_tokens.refresh_token)

    refreshed_tokens = refresh_tokens(db_session, issued_tokens.refresh_token)
    db_session.refresh(auth_session)
    db_session.refresh(old_token)
    new_token = get_refresh_token_record(
        db_session,
        refreshed_tokens.refresh_token,
    )

    assert refreshed_tokens.refresh_token != issued_tokens.refresh_token
    assert decode_access_token(refreshed_tokens.access_token) == user.id
    assert old_token.revoked_at is not None
    assert new_token.session_id == auth_session.id
    assert new_token.revoked_at is None

    with pytest.raises(InvalidRefreshTokenError):
        refresh_tokens(db_session, issued_tokens.refresh_token)

    db_session.refresh(auth_session)
    assert auth_session.revoked_at is not None


def test_refresh_rejects_expired_token_without_revoking_session(
    db_session: Session,
    user: User,
) -> None:
    tokens = login_user(db_session, user.email, TEST_PASSWORD)
    auth_session = db_session.scalar(select(AuthSession))
    refresh_token = get_refresh_token_record(db_session, tokens.refresh_token)
    assert auth_session is not None

    refresh_token.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    with pytest.raises(InvalidRefreshTokenError):
        refresh_tokens(db_session, tokens.refresh_token)

    db_session.refresh(auth_session)
    assert auth_session.revoked_at is None


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
