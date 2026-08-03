from app.infrastructure.repositories.postgres_repository import PostgresConversationRepository


def test_postgres_repository_uses_sql_statements() -> None:
    repository = PostgresConversationRepository()

    assert repository.create_conversation_sql().startswith("INSERT INTO conversations")
    assert repository.get_conversation_sql().startswith("SELECT")
    assert repository.update_context_sql().startswith("UPDATE conversations")
