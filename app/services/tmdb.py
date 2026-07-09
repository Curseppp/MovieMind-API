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


class TmdbClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def get_movie_by_id(self, movie_id: str, language: TmdbLanguage) -> dict:
        response = requests.get(
            f"{self.base_url}/movie/{movie_id}",
            headers=self.headers,
            params={"language": language.value},
            timeout=self.timeout,
        )

        return self._handle_response(response, movie_id)

    def _handle_response(self, response: requests.Response, movie_id: str) -> dict:
        if response.status_code == 200:
            return response.json()

        details = response.json()
        status_code = details.get("status_code")
        message = details.get("status_message", "TMDB request failed")

        if status_code == 34:
            raise TmdbMovieNotFoundError(f"Movie with id {movie_id} not found")

        raise TmdbError(f"{status_code}: {message}")

    def get_tmdb_poster_url(self, path: str | None, size: str = "w500") -> str | None:
        if not path:
            return None

        return f"{settings.tmdb_image_url}/{size}{path}"


tmdb_client = TmdbClient(
    base_url=settings.tmdb_base_url,
    api_key=settings.tmdb_api_key,
)
