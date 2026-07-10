from sqlalchemy.orm import Session

from app.models import FavoriteMovie


def get_favorite(
    db: Session,
    user_id: int,
    movie_id: int,
) -> FavoriteMovie | None:
    return db.get(FavoriteMovie, (user_id, movie_id))


def create_favorite(
    db: Session,
    user_id: int,
    movie_id: int,
) -> FavoriteMovie:
    favorite = FavoriteMovie(user_id=user_id, movie_id=movie_id)
    db.add(favorite)
    db.flush()
    return favorite
