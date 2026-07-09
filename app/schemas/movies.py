from pydantic import BaseModel


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
