from app.schemas.movies import PublicMovie
from app.services.tmdb import tmdb_client, TmdbLanguage


def get_movie_details(movie_id: str, language: TmdbLanguage) -> PublicMovie:
    movie = tmdb_client.get_movie_by_id(movie_id, language)

    details = PublicMovie(
        original_title=movie["original_title"],
        release_date=movie["release_date"],
        genres=movie["genres"],
        vote_average=movie["vote_average"],
        vote_count=movie["vote_count"],
    )

    return details
