from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import AuthSession
from app.models.user import RefreshToken


def create_auth_session(
    db: Session,
    auth_session: AuthSession,
) -> AuthSession:
    db.add(auth_session)
    db.flush()
    return auth_session


def create_refresh_token(db: Session, refresh_token: RefreshToken) -> RefreshToken:
    db.add(refresh_token)
    return refresh_token


def get_refresh_token_by_token_hash(
    db: Session,
    token_hash: str,
) -> RefreshToken | None:
    statement = (
        select(RefreshToken)
        .where(RefreshToken.refresh_token_hash == token_hash)
        .with_for_update()
    )
    return db.scalar(statement)


def get_auth_session_by_session_id(
    db: Session,
    session_id: UUID,
) -> AuthSession | None:
    statement = (
        select(AuthSession).where(AuthSession.id == session_id).with_for_update()
    )
    return db.scalar(statement)


def revoke_all_sessions_by_user_id(db: Session, user_id: int) -> None:
    statement = (
        update(AuthSession)
        .where(
            AuthSession.user_id == user_id,
            AuthSession.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )

    db.execute(statement)
