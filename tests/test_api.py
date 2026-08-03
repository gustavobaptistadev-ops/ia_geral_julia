from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_conversation_endpoint_returns_reply() -> None:
    response = client.post(
        "/api/v1/conversations",
        json={"message": "Quero agendar uma consulta"},
    )

    assert response.status_code == 200
    assert response.json()["reply"]["next_step"] == "discover_symptoms"


def test_conversation_endpoint_accepts_empty_message() -> None:
    response = client.post(
        "/api/v1/conversations",
        json={"message": ""},
    )

    assert response.status_code == 200
    assert response.json()["reply"]["next_step"] == "greeting"
