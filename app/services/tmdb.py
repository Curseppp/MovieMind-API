import requests
from enum import StrEnum

from app.core.config import settings


class TmdbLanguage(StrEnum):
    EN_US = "en-US"
    RU_RU = "ru-RU"


headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {settings.tmdb_api_key}",
}


class TmdbError(Exception):
    pass


class TmdbMovieNotFoundError(TmdbError):
    pass


def search_movies(title: str) -> dict:
    query_params = f"query={title}&page=1"
    url = f"{settings.tmdb_base_url}/search/movie?{query_params}"
    response = requests.get(url, headers=headers, timeout=10)

    res = response.json()

    return res["results"]


def get_movie_by_id(movie_id: str, language: TmdbLanguage) -> dict:
    url = f"{settings.tmdb_base_url}/movie/{movie_id}"

    response = requests.get(
        url,
        headers=headers,
        params={"language": language.value},
        timeout=10,
    )

    if response.status_code != 200:
        details = response.json()
        status_code = details.get("status_code")
        message = details.get("status_message", "TMDB request failed")

        if status_code == 34:
            raise TmdbMovieNotFoundError(f"Movie with id {movie_id} not found")

        raise TmdbError(f"{status_code}: {message}")

    return response.json()
