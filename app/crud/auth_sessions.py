from uuid import UUID

from sqlalchemy import select
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


def create_refresh_token(
        db: Session,
        refresh_token: RefreshToken
) -> RefreshToken:
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
        select(AuthSession)
        .where(AuthSession.id == session_id)
        .with_for_update()
    )
    return db.scalar(statement)
