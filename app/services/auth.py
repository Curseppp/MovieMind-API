from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    DUMMY_HASH,
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.crud.auth_sessions import (
    create_auth_session,
    get_auth_session_by_token_hash,
    rotate_auth_session,
)
from app.crud.users import get_user_by_email, get_user_by_id
from app.models import AuthSession, User


@dataclass(frozen=True)
class IssuedTokens:
    access_token: str
    refresh_token: str


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


def _refresh_token_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)

    if not user:
        verify_password(password, DUMMY_HASH)
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def login_user(
    db: Session,
    email: str,
    password: str,
) -> IssuedTokens:
    user = authenticate_user(db, email, password)

    if user is None:
        raise InvalidCredentialsError()

    access_token = create_access_token(user.id)
    refresh_token = generate_refresh_token()

    auth_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_refresh_token(refresh_token),
        expires_at=_refresh_token_expires_at(),
    )

    try:
        create_auth_session(db, auth_session)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return IssuedTokens(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def refresh_tokens(db: Session, refresh_token: str) -> IssuedTokens:
    auth_session = get_auth_session_by_token_hash(
        db,
        hash_refresh_token(refresh_token),
    )

    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or _as_utc(auth_session.expires_at) <= datetime.now(timezone.utc)
    ):
        raise InvalidRefreshTokenError()

    user = get_user_by_id(db, auth_session.user_id)
    if user is None:
        raise InvalidRefreshTokenError()

    new_refresh_token = generate_refresh_token()
    rotate_auth_session(
        auth_session,
        token_hash=hash_refresh_token(new_refresh_token),
        expires_at=_refresh_token_expires_at(),
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return IssuedTokens(
        access_token=create_access_token(user.id),
        refresh_token=new_refresh_token,
    )


def get_user_from_token(
    db: Session,
    token: str,
) -> User:
    user_id = decode_access_token(token)
    user = get_user_by_id(db, user_id)

    if user is None:
        raise InvalidAccessTokenError()

    return user
