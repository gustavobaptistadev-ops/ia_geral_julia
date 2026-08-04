from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from main import app

client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    token = create_access_token("admin")
    return {"Authorization": f"Bearer {token}"}


def test_conversation_endpoint_returns_reply() -> None:
    response = client.post(
        "/api/v1/conversations",
        json={"message": "Quero agendar uma consulta"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["reply"]["next_step"] == "discover_symptoms"


def test_conversation_endpoint_accepts_empty_message() -> None:
    response = client.post(
        "/api/v1/conversations",
        json={"message": ""},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["reply"]["next_step"] == "greeting"
