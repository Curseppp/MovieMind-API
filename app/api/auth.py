from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import SessionDep
from app.services.register import UserAlreadyExistsError
from app.schemas.users import UserRegister, UserResponse, Token
from app.services.register import register_user
from app.services.auth import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    login_user,
    refresh_tokens,
    revoke_session,
)

router = APIRouter(prefix="/auth")


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/auth",
    )


def delete_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite="strict",
        path="/auth",
    )


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
def issue_token(
    response: Response,
    db: SessionDep,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
) -> Token:
    try:
        tokens = login_user(
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

    set_refresh_cookie(response, tokens.refresh_token)

    return Token(
        access_token=tokens.access_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    response: Response,
    db: SessionDep,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> Token | Response:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing",
        )

    try:
        tokens = refresh_tokens(db, refresh_token)
    except InvalidRefreshTokenError:
        error_response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired refresh token"},
        )
        delete_refresh_cookie(error_response)
        return error_response

    set_refresh_cookie(response, tokens.refresh_token)
    return Token(
        access_token=tokens.access_token,
        token_type="bearer",
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
def logout(
        db: SessionDep,
        response: Response,
        refresh_token: Annotated[str | None, Cookie()] = None,
) -> None:
    if refresh_token is not None:
        revoke_session(db, refresh_token)

    delete_refresh_cookie(response)


