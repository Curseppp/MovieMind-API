from sqlalchemy.orm import Session

from app.crud.users import get_user_by_email
from app.core.security import verify_password, DUMMY_HASH, create_access_token
from app.models.user import User


class InvalidCredentialsError(Exception):
    pass


def authenticate_user(
  db: Session,
  email: str,
  password: str
) -> User |  None:
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


