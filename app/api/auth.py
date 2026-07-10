from fastapi import APIRouter, HTTPException, status

from app.db.session import SessionDep
from app.services.register import UserAlreadyExistsError
from app.schemas.users import UserRegister, UserResponse, UserLogin, Token
from app.services.register import register_user
from app.services.login import login_user, InvalidCredentialsError

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
        db: SessionDep,
        user: UserRegister
):
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
        user_in: UserLogin,
):
    try:
        access_token = login_user(
            db,
            user_in.email,
            user_in.password,
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




