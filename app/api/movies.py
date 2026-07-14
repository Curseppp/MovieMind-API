from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserDep
from app.db.session import SessionDep
from app.schemas.favorites import FavoriteMovieResponse
from app.schemas.movies import PublicMovie
from app.services.favorites import (
    FavoriteAlreadyExistsError,
    UserNotFoundError,
    add_movie_to_user_favorites,
    get_favorite_movies,
)
from app.services.movies import get_movie_details
from app.services.tmdb import TmdbError, TmdbLanguage, TmdbMovieNotFoundError

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/{movie_id}", response_model=PublicMovie)
def get_movie(
    movie_id: int, language: TmdbLanguage = TmdbLanguage.EN_US
) -> PublicMovie:
    try:
        return get_movie_details(movie_id, language)
    except TmdbMovieNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except TmdbError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.post(
    "/{movie_id}/favorite",
    response_model=FavoriteMovieResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_movie_to_favorite(
    session: SessionDep,
    movie_id: int,
    user: CurrentUserDep,
    language: TmdbLanguage = TmdbLanguage.EN_US,
) -> FavoriteMovieResponse:
    try:
        return FavoriteMovieResponse.model_validate(
            add_movie_to_user_favorites(
                db=session,
                user_id=user.id,
                tmdb_id=movie_id,
                language=language,
            )
        )
    except UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except FavoriteAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except TmdbMovieNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except TmdbError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get("/", response_model=list[PublicMovie])
def get_my_favorites(
    db: SessionDep,
    user: CurrentUserDep,
    skip: int = 0,
    limit: int = 10,
):
    return get_favorite_movies(db, user, skip, limit)
