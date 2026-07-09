from app.schemas.movies import PublicMovie
from app.services.tmdb import tmdb_client, TmdbLanguage


def get_movie_details(movie_id: str, language: TmdbLanguage) -> PublicMovie:
    movie = tmdb_client.get_movie_by_id(movie_id, language)
    poster_path = movie.get("poster_path")

    details = PublicMovie(
        original_title=movie["original_title"],
        release_date=movie["release_date"],
        genres=[genre["name"] for genre in movie["genres"]],
        vote_average=movie["vote_average"],
        vote_count=movie["vote_count"],
        poster_url=tmdb_client.get_tmdb_poster_url(poster_path),
    )

    return details
