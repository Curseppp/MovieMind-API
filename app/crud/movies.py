from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Movie, FavoriteMovie
from app.schemas.movies import PublicMovie
from app.services.tmdb import tmdb_client


def get_movie_by_tmdb_id(db: Session, tmdb_id: int) -> Movie | None:
    return db.scalar(select(Movie).where(Movie.tmdb_id == tmdb_id))


def create_movie(db: Session, movie: Movie) -> Movie:
    db.add(movie)
    db.flush()
    return movie


def get_favorite_movies_by_user_id(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Movie]:
    statement = (
        select(Movie)
        .join(
            FavoriteMovie,
            FavoriteMovie.movie_id == Movie.id,
        )
        .options(selectinload(Movie.genres))
        .where(FavoriteMovie.user_id == user_id)
        .order_by(FavoriteMovie.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def to_public_movie(movie: Movie) -> PublicMovie:
    return PublicMovie(
        original_title=movie.original_title or "",
        release_date=(movie.release_date.isoformat() if movie.release_date else ""),
        genres=[genre.name for genre in movie.genres],
        vote_average=movie.vote_average or 0,
        vote_count=movie.vote_count or 0,
        poster_url=tmdb_client.get_tmdb_poster_url(movie.poster_path),
    )
