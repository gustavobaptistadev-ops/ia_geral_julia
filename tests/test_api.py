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
    assert response.json()["conversation_id"] is not None


def test_conversation_endpoint_accepts_empty_message() -> None:
    response = client.post(
        "/api/v1/conversations",
        json={"message": ""},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["reply"]["next_step"] == "greeting"


def test_conversation_endpoint_preserves_conversation_id() -> None:
    response = client.post(
        "/api/v1/conversations",
        json={"message": "Quero agendar uma consulta", "conversation_id": "conv-1"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "conv-1"


def test_reset_conversations_endpoint_requires_authentication() -> None:
    response = client.delete("/api/v1/conversations")

    assert response.status_code == 401


def test_reset_conversations_endpoint_returns_success_in_development() -> None:
    response = client.delete("/api/v1/conversations", headers=_auth_headers())

    assert response.status_code == 200
    assert response.json()["reset"] is True
