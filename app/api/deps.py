from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import InvalidAccessTokenError
from app.db.session import SessionDep
from app.models import User
from app.services.auth import get_user_from_token


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
)

TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(
    db: SessionDep,
    token: TokenDep,
) -> User:
    try:
        return get_user_from_token(db, token)
    except InvalidAccessTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


CurrentUserDep = Annotated[
    User,
    Depends(get_current_user),
]
