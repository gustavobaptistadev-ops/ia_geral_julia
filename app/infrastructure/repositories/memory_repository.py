from __future__ import annotations

from typing import Any


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._conversations: dict[str, dict[str, Any]] = {}

    def create_conversation(self, conversation_id: str) -> str:
        self._conversations[conversation_id] = {"conversation_id": conversation_id, "context": {}}
        return conversation_id

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        return self._conversations.get(conversation_id)

    def update_context(self, conversation_id: str, context: dict[str, Any]) -> None:
        conversation = self._conversations.get(conversation_id)
        if conversation is not None:
            conversation["context"].update(context)
