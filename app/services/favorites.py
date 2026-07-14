from sqlalchemy.orm import Session

from app.crud import favorites as favorites_crud
from app.crud import users as users_crud
from app.models import FavoriteMovie, User
from app.crud.movies import (
    get_favorite_movies_by_user_id as crud_get_favorite_movies,
    to_public_movie,
)
from app.schemas.movies import PublicMovie
from app.services.movies import get_or_create_movie_from_tmdb
from app.services.tmdb import TmdbLanguage


class UserNotFoundError(Exception):
    pass


class FavoriteAlreadyExistsError(Exception):
    pass


def add_movie_to_user_favorites(
    db: Session,
    user_id: int,
    tmdb_id: int,
    language: TmdbLanguage,
) -> FavoriteMovie:
    try:
        user = users_crud.get_user_by_id(db, user_id)

        if user is None:
            raise UserNotFoundError(f"User with id {user_id} not found")

        movie = get_or_create_movie_from_tmdb(db, tmdb_id, language)
        favorite = favorites_crud.get_favorite(db, user_id, movie.id)

        if favorite is not None:
            raise FavoriteAlreadyExistsError(
                f"Movie with TMDB id {tmdb_id} is already in favorites"
            )

        favorite = favorites_crud.create_favorite(db, user_id, movie.id)
        db.commit()
        db.refresh(favorite)
        return favorite
    except Exception:
        db.rollback()
        raise


def get_favorite_movies(
    db: Session,
    user: User,
    skip: int,
    limit: int,
) -> list[PublicMovie]:
    movies = crud_get_favorite_movies(
        db,
        user.id,
        skip,
        limit,
    )

    return [to_public_movie(movie) for movie in movies]
