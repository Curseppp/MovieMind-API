from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import FavoriteMovie, Movie, User
from tests.constants import TEST_PASSWORD


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/token",
        data={"username": email, "password": TEST_PASSWORD},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_favorites_expose_tmdb_id_and_can_be_removed(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    movie = Movie(
        tmdb_id=603,
        original_title="The Matrix",
        release_date=date(1999, 3, 30),
        poster_path=None,
        vote_average=8.2,
        vote_count=26000,
    )
    db_session.add(movie)
    db_session.flush()
    db_session.add(FavoriteMovie(user_id=user.id, movie_id=movie.id))
    db_session.commit()
    headers = auth_headers(client, user.email)

    list_response = client.get("/movies/", headers=headers)

    assert list_response.status_code == 200
    assert list_response.json()[0]["tmdb_id"] == 603

    delete_response = client.delete("/movies/603/favorite", headers=headers)

    assert delete_response.status_code == 204
    assert db_session.get(FavoriteMovie, (user.id, movie.id)) is None


def test_remove_missing_favorite_returns_not_found(
    client: TestClient,
    user: User,
) -> None:
    response = client.delete(
        "/movies/404/favorite",
        headers=auth_headers(client, user.email),
    )

    assert response.status_code == 404
