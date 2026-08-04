from __future__ import annotations

from typing import Any, Callable


class PostgresConversationRepository:
    def __init__(self, executor: Callable[[str, dict[str, Any]], Any] | None = None) -> None:
        self.executor = executor

    def create_conversation_sql(self) -> str:
        return """
        INSERT INTO conversations (conversation_id, context)
        VALUES (%(conversation_id)s, %(context)s)
        RETURNING conversation_id
        """.strip()

    def get_conversation_sql(self) -> str:
        return """
        SELECT conversation_id, context
        FROM conversations
        WHERE conversation_id = %(conversation_id)s
        """.strip()

    def update_context_sql(self) -> str:
        return """
        UPDATE conversations
        SET context = %(context)s
        WHERE conversation_id = %(conversation_id)s
        """.strip()

    def build_connection_kwargs(self, connection_string: str) -> dict[str, Any]:
        return {"connection_string": connection_string}

    def create_conversation(self, conversation_id: str, context: dict[str, Any]) -> Any | None:
        if self.executor is None:
            return None

        return self.executor(
            self.create_conversation_sql(),
            {"conversation_id": conversation_id, "context": context},
        )

    def get_conversation(self, conversation_id: str) -> Any | None:
        if self.executor is None:
            return None

        return self.executor(self.get_conversation_sql(), {"conversation_id": conversation_id})

    def update_context(self, conversation_id: str, context: dict[str, Any]) -> Any | None:
        if self.executor is None:
            return None

        return self.executor(
            self.update_context_sql(),
            {"conversation_id": conversation_id, "context": context},
        )
