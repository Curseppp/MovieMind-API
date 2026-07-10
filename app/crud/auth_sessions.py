from sqlalchemy.orm import Session

from app.models import AuthSession


def create_auth_session(
    db: Session,
    auth_session: AuthSession,
) -> AuthSession:
    db.add(auth_session)
    return auth_session
