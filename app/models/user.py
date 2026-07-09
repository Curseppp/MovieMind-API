from datetime import datetime

from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import ForeignKey, func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column()
    password_hash: Mapped[str] = mapped_column()


class FavoriteMovie(Base):
    __tablename__ = "favorite_movies"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )