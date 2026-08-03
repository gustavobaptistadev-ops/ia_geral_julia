from app.infrastructure.repositories.memory_repository import InMemoryConversationRepository


def test_repository_can_store_and_retrieve_conversation() -> None:
    repository = InMemoryConversationRepository()
    conversation_id = repository.create_conversation("conversation-1")

    stored = repository.get_conversation(conversation_id)

    assert stored is not None
    assert stored["conversation_id"] == "conversation-1"


def test_repository_can_update_context() -> None:
    repository = InMemoryConversationRepository()
    conversation_id = repository.create_conversation("conversation-2")

    repository.update_context(conversation_id, {"reason": "consulta"})
    stored = repository.get_conversation(conversation_id)

    assert stored is not None
    assert stored["context"]["reason"] == "consulta"
