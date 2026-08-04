from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["ENABLE_POSTGRES_PERSISTENCE"] = "true"
os.environ["POSTGRES_URL"] = "postgresql://postgres:postgres@127.0.0.1:55432/lifelineone"

logging.getLogger("httpx").setLevel(logging.WARNING)

from main import app


client = TestClient(app)


def main() -> None:
    _ensure_postgres_schema()
    token = _login()
    _reset_conversations(token)

    conversation_id: str | None = None
    print("LifelineOne IA - teste local")
    print("Digite /reset para limpar a conversa ou /sair para encerrar.")

    while True:
        message = input("\nVoce: ").strip()
        if message.lower() in {"/sair", "sair", "exit", "quit"}:
            print("Encerrado.")
            return

        if message.lower() == "/reset":
            _reset_conversations(token)
            conversation_id = None
            print("Conversas resetadas.")
            continue

        response = client.post(
            "/api/v1/conversations",
            json={"message": message, "conversation_id": conversation_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            print(f"Erro {response.status_code}: {response.text}")
            continue

        payload = response.json()
        conversation_id = payload["conversation_id"]
        reply = payload["reply"]
        print(f"IA: {reply['message']}")
        print(f"Etapa: {reply['next_step']} | Handoff: {reply['should_handoff']} | ID: {conversation_id}")


def _login() -> str:
    response = client.post("/login", json={"username": "admin", "password": "admin"})
    if response.status_code != 200:
        raise RuntimeError(f"Falha no login local: {response.text}")

    return response.json()["access_token"]


def _reset_conversations(token: str) -> None:
    response = client.delete("/api/v1/conversations", headers={"Authorization": f"Bearer {token}"})
    if response.status_code not in {200, 403}:
        raise RuntimeError(f"Falha ao resetar conversas: {response.text}")


def _ensure_postgres_schema() -> None:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("Instale as dependencias com: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt") from exc

    schema_path = PROJECT_ROOT / "app" / "infrastructure" / "database" / "001_initial_schema.sql"
    try:
        with psycopg.connect(os.environ["POSTGRES_URL"]) as connection:
            with connection.cursor() as cursor:
                cursor.execute(schema_path.read_text(encoding="utf-8"))
    except psycopg.OperationalError as exc:
        raise RuntimeError(
            "PostgreSQL nao esta acessivel. Inicie com: docker compose up -d postgres"
        ) from exc


if __name__ == "__main__":
    main()
