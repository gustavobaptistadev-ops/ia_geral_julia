from __future__ import annotations

from typing import Any


class PostgresConversationRepository:
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
