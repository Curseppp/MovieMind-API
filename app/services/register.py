from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pwdlib import PasswordHash

from app.models.user import User
from app.crud.users import get_user_by_email, create_user
from app.schemas.users import UserRegister


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


class UserAlreadyExistsError(Exception):
    pass


def register_user(db: Session, user: UserRegister) -> User:
    if get_user_by_email(db, user.email) is not None:
        raise UserAlreadyExistsError(f"User with email {user.email} already exists")

    data = User(
        email=user.email,
        username=user.username,
        password_hash=hash_password(user.password),
    )

    try:
        new_user = create_user(db, data)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise UserAlreadyExistsError("User already exists") from exc

    db.refresh(new_user)
    return new_user
