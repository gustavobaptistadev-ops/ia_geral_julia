from fastapi.testclient import TestClient

from app.core.auth import create_access_token, create_refresh_token
from main import app

client = TestClient(app)


def test_login_returns_tokens_for_valid_credentials() -> None:
    response = client.post(
        "/login",
        json={"username": "admin", "password": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


def test_login_rejects_invalid_password() -> None:
    response = client.post(
        "/login",
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_refresh_endpoint_returns_new_access_token() -> None:
    login_response = client.post(
        "/login",
        json={"username": "admin", "password": "admin"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_token_helpers_issue_tokens() -> None:
    access_token = create_access_token("admin")
    refresh_token = create_refresh_token("admin")

    assert access_token
    assert refresh_token
