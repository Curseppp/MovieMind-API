from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.db.session import SessionDep
from app.services.register import UserAlreadyExistsError
from app.schemas.users import UserRegister, UserResponse, Token
from app.services.register import register_user
from app.services.auth import login_user, InvalidCredentialsError

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(db: SessionDep, user: UserRegister):
    try:
        user = register_user(db, user)
        return user
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/token", response_model=Token)
def token(
    db: SessionDep,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
):
    try:
        access_token = login_user(
            db=db,
            email=form_data.username,
            password=form_data.password,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return Token(
        access_token=access_token,
        token_type="bearer",
    )
