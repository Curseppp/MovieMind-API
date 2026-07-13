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
    create_refresh_token,
    get_refresh_token_by_token_hash,
    get_auth_session_by_session_id,
)
from app.crud.users import get_user_by_email, get_user_by_id
from app.models.user import AuthSession, User, RefreshToken


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


def _session_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        days=settings.session_expire_days
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

    try:
        auth_session = AuthSession(
            user_id=user.id,
            expires_at=_session_expires_at(),
        )

        access_token = create_access_token(user.id)
        refresh_token = generate_refresh_token()

        create_auth_session(db, auth_session)

        token = RefreshToken(
            refresh_token_hash=hash_refresh_token(refresh_token),
            session_id=auth_session.id,
            expires_at=_refresh_token_expires_at(),
        )
        create_refresh_token(db, token)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return IssuedTokens(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def refresh_tokens(db: Session, refresh_token: str) -> IssuedTokens:
    token = get_refresh_token_by_token_hash(
        db,
        hash_refresh_token(refresh_token),
    )

    if token is None:
        raise InvalidRefreshTokenError()

    auth_session = get_auth_session_by_session_id(
        db, session_id=token.session_id
    )

    if auth_session is None:
        raise InvalidRefreshTokenError()

    if (
        _as_utc(auth_session.expires_at) <= datetime.now(timezone.utc)
        or auth_session.revoked_at is not None
    ):
        raise InvalidRefreshTokenError()

    if _as_utc(token.expires_at) <= datetime.now(timezone.utc):
        raise InvalidRefreshTokenError()

    if token.revoked_at is not None:
        auth_session.revoked_at = datetime.now(timezone.utc)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        raise InvalidRefreshTokenError

    user = get_user_by_id(db, auth_session.user_id)
    if user is None:
        raise InvalidRefreshTokenError()

    new_access_token = create_access_token(
        user.id,
    )
    token.revoked_at = datetime.now(timezone.utc)
    new_refresh_token = generate_refresh_token()
    new_token = RefreshToken(
        refresh_token_hash=hash_refresh_token(new_refresh_token),
        session_id=auth_session.id,
        expires_at=min(
            _refresh_token_expires_at(),
            _as_utc(auth_session.expires_at),
),
    )

    try:
        create_refresh_token(
            db,
            new_token
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return IssuedTokens(
        access_token=new_access_token,
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


def revoke_session(
        db: Session,
        refresh_token: str,
) -> None:
    token = get_refresh_token_by_token_hash(
        db,
        hash_refresh_token(refresh_token),
    )

    if token is None:
        return

    auth_session = get_auth_session_by_session_id(
        db, session_id=token.session_id
    )

    if auth_session is None:
        return

    try:
        token.revoked_at = token.revoked_at or datetime.now(timezone.utc)
        auth_session.revoked_at = auth_session.revoked_at or datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise