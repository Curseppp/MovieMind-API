from fastapi import APIRouter

from app.db.session import SessionDep
from app.services.health import check_database


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
def root():
    return {"message": "App OK"}


@router.get("/db")
def ping(db: SessionDep):
    check_database(db)
    return {"message": "Db OK"}
