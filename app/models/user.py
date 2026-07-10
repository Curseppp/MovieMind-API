from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.movie import Movie


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column()
    password_hash: Mapped[str] = mapped_column()

    favorites: Mapped[list["FavoriteMovie"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class FavoriteMovie(Base):
    __tablename__ = "favorite_movies"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(
        back_populates="favorites",
    )

    movie: Mapped["Movie"] = relationship(
        back_populates="favorites",
    )
