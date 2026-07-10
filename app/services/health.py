from sqlalchemy.orm import Session

from app.crud import health as health_crud


def check_database(db: Session) -> None:
    health_crud.ping_database(db)
