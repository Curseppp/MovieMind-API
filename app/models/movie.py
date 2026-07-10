from datetime import datetime, date
from typing import TYPE_CHECKING

from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Column, Table, ForeignKey, func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import FavoriteMovie


movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[int] = mapped_column(unique=True, index=True)
    original_title: Mapped[str | None] = mapped_column()
    release_date: Mapped[date | None] = mapped_column()
    poster_path: Mapped[str | None] = mapped_column()
    vote_average: Mapped[float | None] = mapped_column()
    vote_count: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column()
    genres: Mapped[list["Genre"]] = relationship(
        secondary=movie_genres,
        back_populates="movies",
    )
    favorites: Mapped[list["FavoriteMovie"]] = relationship(
        back_populates="movie",
    )


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    tmdb_id: Mapped[int] = mapped_column(unique=True, index=True)
    name: Mapped[str] = mapped_column()

    movies: Mapped[list[Movie]] = relationship(
        secondary=movie_genres,
        back_populates="genres",
    )
