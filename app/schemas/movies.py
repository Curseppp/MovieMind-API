from pydantic import BaseModel


class Genre(BaseModel):
    id: int
    name: str


class PublicMovie(BaseModel):
    original_title: str
    release_date: str
    genres: list[Genre]
    vote_average: float
    vote_count: int
