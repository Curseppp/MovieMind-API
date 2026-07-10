from fastapi import APIRouter, HTTPException, status

from app.db.session import SessionDep
from app.services.register import UserAlreadyExistsError
from app.schemas.users import UserRegister, UserResponse
from app.services.register import register_user

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



