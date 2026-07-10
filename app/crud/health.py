from sqlalchemy import select
from sqlalchemy.orm import Session


def ping_database(db: Session) -> None:
    db.execute(select(1)).scalar_one()
