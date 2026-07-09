from fastapi import APIRouter, HTTPException, status

from app.schemas.movies import PublicMovie
from app.services.movies import get_movie_details
from app.services.tmdb import TmdbError, TmdbLanguage, TmdbMovieNotFoundError

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/{movie_id}", response_model=PublicMovie)
def get_movie(
    movie_id: str, language: TmdbLanguage = TmdbLanguage.EN_US
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
