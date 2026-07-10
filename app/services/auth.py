from sqlalchemy.orm import Session

from app.crud.users import get_user_by_email
from app.core.security import (
    verify_password,
    DUMMY_HASH,
    create_access_token,
    decode_access_token,
    InvalidAccessTokenError,
)
from app.models.user import User
from app.crud.users import get_user_by_id


class InvalidCredentialsError(Exception):
    pass


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)

    if not user:
        verify_password(password, DUMMY_HASH)
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def login_user(db: Session, email: str, password: str) -> str:
    user = authenticate_user(db, email, password)

    if user is None:
        raise InvalidCredentialsError()

    return create_access_token(user.id)


def get_user_from_token(
    db: Session,
    token: str,
) -> User:
    user_id = decode_access_token(token)
    user = get_user_by_id(db, user_id)

    if user is None:
        raise InvalidAccessTokenError()

    return user
