from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Movie


def get_movie_by_tmdb_id(db: Session, tmdb_id: int) -> Movie | None:
    return db.scalar(select(Movie).where(Movie.tmdb_id == tmdb_id))


def create_movie(db: Session, movie: Movie) -> Movie:
    db.add(movie)
    db.flush()
    return movie
