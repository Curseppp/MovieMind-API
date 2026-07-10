from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep
from app.core.config import settings
from app.core.security import decode_access_token, hash_refresh_token
from app.db.session import get_db
from app.models import AuthSession, User
from tests.constants import TEST_PASSWORD


def login(client: TestClient, email: str = "user@example.com"):
    return client.post(
        "/auth/token",
        data={"username": email, "password": TEST_PASSWORD},
    )


def get_auth_session(db_session: Session, refresh_token: str) -> AuthSession:
    auth_session = db_session.scalar(
        select(AuthSession).where(
            AuthSession.refresh_token_hash == hash_refresh_token(refresh_token)
        )
    )
    assert auth_session is not None
    return auth_session


def test_login_returns_access_token_and_secure_cookie_contract(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    response = login(client, user.email)

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert decode_access_token(response.json()["access_token"]) == user.id

    refresh_token = response.cookies.get("refresh_token")
    assert refresh_token is not None
    get_auth_session(db_session, refresh_token)

    cookie_header = response.headers["set-cookie"].lower()
    assert "httponly" in cookie_header
    assert "samesite=strict" in cookie_header
    assert "path=/auth" in cookie_header
    assert f"max-age={settings.refresh_token_expire_days * 86400}" in cookie_header


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("user@example.com", "wrong-password"),
        ("missing@example.com", TEST_PASSWORD),
    ],
)
def test_login_rejects_invalid_credentials(
    client: TestClient,
    user: User,
    email: str,
    password: str,
) -> None:
    response = client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.cookies.get("refresh_token") is None


def test_login_rejects_missing_form_fields(client: TestClient) -> None:
    response = client.post("/auth/token", data={})

    assert response.status_code == 422


def test_refresh_rotates_cookie_and_returns_new_access_token(
    client: TestClient,
    db_session: Session,
    user: User,
) -> None:
    login_response = login(client, user.email)
    old_refresh_token = login_response.cookies["refresh_token"]
    old_session = get_auth_session(db_session, old_refresh_token)
    old_session_id = old_session.id

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert decode_access_token(response.json()["access_token"]) == user.id
    new_refresh_token = response.cookies["refresh_token"]
    assert new_refresh_token != old_refresh_token
    new_session = get_auth_session(db_session, new_refresh_token)
    assert new_session.id == old_session_id


def test_refresh_rejects_replayed_token(
    client: TestClient,
    user: User,
) -> None:
    login_response = login(client, user.email)
    old_refresh_token = login_response.cookies["refresh_token"]
    assert client.post("/auth/refresh").status_code == 200
    client.cookies.set(
        "refresh_token",
        old_refresh_token,
        domain="testserver.local",
        path="/auth",
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired refresh token"}


def test_refresh_rejects_missing_cookie(client: TestClient) -> None:
    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {"detail": "Refresh token is missing"}


def test_refresh_rejects_unknown_token_and_deletes_cookie(
    client: TestClient,
) -> None:
    client.cookies.set(
        "refresh_token",
        "unknown-token",
        domain="testserver.local",
        path="/auth",
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert "max-age=0" in response.headers["set-cookie"].lower()
    assert client.cookies.get("refresh_token") is None


@pytest.mark.parametrize("session_state", ["expired", "revoked"])
def test_refresh_rejects_expired_or_revoked_session(
    client: TestClient,
    db_session: Session,
    user: User,
    session_state: str,
) -> None:
    login_response = login(client, user.email)
    refresh_token = login_response.cookies["refresh_token"]
    auth_session = get_auth_session(db_session, refresh_token)

    if session_state == "expired":
        auth_session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    else:
        auth_session.revoked_at = datetime.now(timezone.utc)
    db_session.commit()

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or expired refresh token"}


@pytest.fixture()
def protected_client(db_session: Session) -> Generator[TestClient, None, None]:
    protected_app = FastAPI()

    @protected_app.get("/protected")
    def protected(user: CurrentUserDep) -> dict[str, int]:
        return {"user_id": user.id}

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    protected_app.dependency_overrides[get_db] = override_get_db
    with TestClient(protected_app) as test_client:
        yield test_client


def test_bearer_authentication_returns_current_user(
    protected_client: TestClient,
    client: TestClient,
    user: User,
) -> None:
    access_token = login(client, user.email).json()["access_token"]

    response = protected_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"user_id": user.id}


def test_bearer_authentication_requires_token(
    protected_client: TestClient,
) -> None:
    response = protected_client.get("/protected")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_bearer_authentication_rejects_invalid_token(
    protected_client: TestClient,
) -> None:
    response = protected_client.get(
        "/protected",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_bearer_authentication_rejects_expired_token(
    protected_client: TestClient,
) -> None:
    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = protected_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


def test_bearer_authentication_rejects_missing_user(
    protected_client: TestClient,
) -> None:
    token = jwt.encode(
        {
            "sub": "999999",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    response = protected_client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
