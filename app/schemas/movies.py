from pydantic import BaseModel, ConfigDict
from app.services.tmdb import TmdbLanguage


class Genre(BaseModel):
    id: int
    name: str


class Movie(BaseModel):
    original_title: str
    release_date: str
    genres: list[Genre]
    vote_average: float
    vote_count: int
    poster_url: str | None


class PublicMovie(BaseModel):
    original_title: str
    release_date: str
    genres: list[str]
    vote_average: float
    vote_count: int
    poster_url: str | None

    model_config = ConfigDict(from_attributes=True)


class QueryParams(BaseModel):
    query: str
    page: int | None = None
    per_page: int | None = None
    primary_release_year: str | None = None
    region: str | None = None
    language: TmdbLanguage | None = TmdbLanguage.EN_US
    year: str | None = None

    model_config = ConfigDict(from_attributes=True)

