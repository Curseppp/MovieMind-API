from datetime import date

from sqlalchemy.orm import Session

from app.crud import genres as genres_crud
from app.crud import movies as movies_crud
from app.models import Genre, Movie
from app.schemas.movies import PublicMovie, QueryParams
from app.services.tmdb import TmdbLanguage, tmdb_client


def search_movie(
    db: Session, query: QueryParams, skip: int, limit: int
) -> list[PublicMovie]:
    payload = dict(query)
    start_page = skip // 20 + 1
    offset_page = skip % 20
    movies = []
    payload["page"] = start_page
    total_pages = 999

    while len(movies) < limit and payload["page"] <= total_pages:
        response = tmdb_client.get_tmdb_movies_by_title(payload)
        if payload["page"] == start_page:
            results = response.get("results", [])[offset_page:]
            total_pages = response.get("total_pages")
        else:
            results = response.get("results", [])

        for movie in results:
            if len(movies) < limit:
                poster_path = movie.get("poster_path")
                genres = genres_crud.get_genres_by_tmdb_ids(db, movie["genre_ids"])
                details = PublicMovie(
                    tmdb_id=movie["id"],
                    original_title=movie["original_title"],
                    release_date=movie["release_date"],
                    genres=[genre.name for genre in genres.values()],
                    vote_average=movie["vote_average"],
                    vote_count=movie["vote_count"],
                    poster_url=tmdb_client.get_tmdb_poster_url(poster_path),
                )
                movies.append(details)
        payload["page"] += 1

    return movies


def get_movie_details(movie_id: int, language: TmdbLanguage) -> PublicMovie:
    movie = tmdb_client.get_movie_by_id(movie_id, language)
    poster_path = movie.get("poster_path")

    details = PublicMovie(
        tmdb_id=movie["id"],
        original_title=movie["original_title"],
        release_date=movie["release_date"],
        genres=[genre["name"] for genre in movie["genres"]],
        vote_average=movie["vote_average"],
        vote_count=movie["vote_count"],
        poster_url=tmdb_client.get_tmdb_poster_url(poster_path),
    )

    return details


def get_or_create_movie_from_tmdb(
    db: Session,
    tmdb_id: int,
    language: TmdbLanguage,
) -> Movie:
    movie = movies_crud.get_movie_by_tmdb_id(db, tmdb_id)

    if movie is not None:
        return movie

    tmdb_movie = tmdb_client.get_movie_by_id(
        tmdb_id,
        language,
    )

    genres = _get_or_create_genres(db, tmdb_movie.get("genres", []))
    release_date = tmdb_movie.get("release_date")

    movie = Movie(
        tmdb_id=tmdb_movie["id"],
        original_title=tmdb_movie["original_title"],
        release_date=date.fromisoformat(release_date) if release_date else None,
        poster_path=tmdb_movie.get("poster_path"),
        vote_average=tmdb_movie.get("vote_average"),
        vote_count=tmdb_movie.get("vote_count"),
        genres=genres,
    )

    return movies_crud.create_movie(db, movie)


def _get_or_create_genres(
    db: Session,
    tmdb_genres: list[dict],
) -> list[Genre]:
    genre_ids = [genre["id"] for genre in tmdb_genres]
    genres_by_tmdb_id = genres_crud.get_genres_by_tmdb_ids(db, genre_ids)
    genres = []

    for genre_data in tmdb_genres:
        tmdb_id = genre_data["id"]
        genre = genres_by_tmdb_id.get(tmdb_id)

        if genre is None:
            genre = genres_crud.create_genre(
                db,
                tmdb_id=tmdb_id,
                name=genre_data["name"],
            )

        genres.append(genre)

    return genres


def set_genres(db: Session) -> None:
    genres = tmdb_client.get_all_tmdb_movies_genres()
    _get_or_create_genres(db, genres.get("genres", []))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
