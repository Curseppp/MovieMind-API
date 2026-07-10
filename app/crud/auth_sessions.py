from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuthSession


def create_auth_session(
    db: Session,
    auth_session: AuthSession,
) -> AuthSession:
    db.add(auth_session)
    return auth_session


def get_auth_session_by_token_hash(
    db: Session,
    token_hash: str,
) -> AuthSession | None:
    statement = (
        select(AuthSession)
        .where(AuthSession.refresh_token_hash == token_hash)
        .with_for_update()
    )
    return db.scalar(statement)


def rotate_auth_session(
    auth_session: AuthSession,
    token_hash: str,
    expires_at: datetime,
) -> AuthSession:
    auth_session.refresh_token_hash = token_hash
    auth_session.expires_at = expires_at
    return auth_session
