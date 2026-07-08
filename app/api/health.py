from fastapi import APIRouter
from sqlalchemy import select

from app.db.session import SessionDep


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
def root():
    return {"message": "App OK"}


@router.get("/db")
def ping(db: SessionDep):
    db.execute(select(1)).scalar_one()
    return {"message": "Db OK"}
