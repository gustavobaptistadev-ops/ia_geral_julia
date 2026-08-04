from app.infrastructure.repositories.postgres_repository import PostgresConversationRepository


def test_postgres_repository_uses_sql_statements() -> None:
    repository = PostgresConversationRepository()

    assert repository.create_conversation_sql().startswith("INSERT INTO conversations")
    assert repository.get_conversation_sql().startswith("SELECT")
    assert repository.update_context_sql().startswith("UPDATE conversations")


def test_postgres_repository_executes_create_get_and_update() -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_executor(sql: str, params: dict[str, object]) -> str:
        calls.append((sql, params))
        return "ok"

    repository = PostgresConversationRepository(executor=fake_executor)

    assert repository.create_conversation("conv-1", {"status": "new"}) == "ok"
    assert repository.get_conversation("conv-1") == "ok"
    assert repository.update_context("conv-1", {"status": "updated"}) == "ok"
    assert len(calls) == 3
