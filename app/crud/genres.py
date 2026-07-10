from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Genre


def get_genres_by_tmdb_ids(
    db: Session,
    tmdb_ids: list[int],
) -> dict[int, Genre]:
    if not tmdb_ids:
        return {}

    genres = db.scalars(select(Genre).where(Genre.tmdb_id.in_(tmdb_ids))).all()
    return {genre.tmdb_id: genre for genre in genres}


def create_genre(db: Session, tmdb_id: int, name: str) -> Genre:
    genre = Genre(tmdb_id=tmdb_id, name=name)
    db.add(genre)
    return genre
