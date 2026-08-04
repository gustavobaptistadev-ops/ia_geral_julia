from app.infrastructure.repositories.postgres_repository import PostgresConversationRepository


def test_postgres_repository_uses_sql_statements() -> None:
    repository = PostgresConversationRepository()

    assert "CREATE TABLE IF NOT EXISTS conversations" in repository.schema_sql()
    assert "CREATE TABLE IF NOT EXISTS appointments" in repository.schema_sql()
    assert repository.create_conversation_sql().startswith("INSERT INTO conversations")
    assert repository.get_conversation_sql().startswith("SELECT")
    assert repository.update_context_sql().startswith("UPDATE conversations")
    assert repository.create_appointment_sql().startswith("INSERT INTO appointments")
    assert repository.reset_conversations_sql().startswith("TRUNCATE TABLE")


def test_postgres_repository_executes_create_get_and_update() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_executor(sql: str, params: dict[str, object]) -> str:
        calls.append((sql, params))
        return "ok"

    repository = PostgresConversationRepository(executor=fake_executor)

    assert repository.create_conversation("conv-1", {"status": "new"}) == "ok"
    assert repository.get_conversation("conv-1") == "ok"
    assert repository.update_context("conv-1", {"status": "updated"}) == "ok"
    assert repository.create_appointment(
        "conv-1",
        "Ana",
        "11999999999",
        "Clinica Vida",
        "Cardiologia",
        "2026-08-10 09:00",
        {"source": "test"},
    ) == "ok"
    assert repository.reset_conversations() == "ok"
    assert len(calls) == 5
