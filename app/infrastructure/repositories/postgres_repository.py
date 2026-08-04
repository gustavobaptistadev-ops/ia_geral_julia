from __future__ import annotations

from typing import Any, Callable


class PsycopgExecutor:
    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def __call__(self, sql: str, params: dict[str, Any]) -> Any:
        try:
            import psycopg
            from psycopg.rows import dict_row
            from psycopg.types.json import Jsonb
        except ImportError as exc:
            raise RuntimeError("Instale psycopg para usar a persistencia PostgreSQL real.") from exc

        prepared_params = {
            key: Jsonb(value) if isinstance(value, dict) else value
            for key, value in params.items()
        }

        with psycopg.connect(self.connection_string) as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(sql, prepared_params)
                if cursor.description is None:
                    return None
                return cursor.fetchone()


class PostgresConversationRepository:
    def __init__(self, executor: Callable[[str, dict[str, Any]], Any] | None = None) -> None:
        self.executor = executor

    def schema_sql(self) -> str:
        return """
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'active',
            current_step TEXT NOT NULL DEFAULT 'greeting',
            context JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id BIGSERIAL PRIMARY KEY,
            conversation_id TEXT REFERENCES conversations(conversation_id),
            patient_name TEXT NOT NULL,
            patient_phone TEXT,
            clinic_name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            scheduled_at TEXT NOT NULL,
            context JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_appointments_conversation_id
            ON appointments(conversation_id);
        """.strip()

    def create_conversation_sql(self) -> str:
        return """
        INSERT INTO conversations (conversation_id, status, current_step, context)
        VALUES (%(conversation_id)s, %(status)s, %(current_step)s, %(context)s)
        ON CONFLICT (conversation_id) DO UPDATE
        SET status = EXCLUDED.status,
            current_step = EXCLUDED.current_step,
            context = EXCLUDED.context,
            updated_at = NOW()
        RETURNING conversation_id
        """.strip()

    def get_conversation_sql(self) -> str:
        return """
        SELECT conversation_id, status, current_step, context
        FROM conversations
        WHERE conversation_id = %(conversation_id)s
        """.strip()

    def update_context_sql(self) -> str:
        return """
        UPDATE conversations
        SET context = context || %(context)s,
            status = COALESCE(%(status)s, status),
            current_step = COALESCE(%(current_step)s, current_step),
            updated_at = NOW()
        WHERE conversation_id = %(conversation_id)s
        RETURNING conversation_id
        """.strip()

    def create_appointment_sql(self) -> str:
        return """
        INSERT INTO appointments (
            conversation_id,
            patient_name,
            patient_phone,
            clinic_name,
            specialty,
            scheduled_at,
            context
        )
        VALUES (
            %(conversation_id)s,
            %(patient_name)s,
            %(patient_phone)s,
            %(clinic_name)s,
            %(specialty)s,
            %(scheduled_at)s,
            %(context)s
        )
        RETURNING appointment_id
        """.strip()

    def reset_conversations_sql(self) -> str:
        return "TRUNCATE TABLE appointments, conversations RESTART IDENTITY"

    def build_connection_kwargs(self, connection_string: str) -> dict[str, Any]:
        return {"connection_string": connection_string}

    def create_conversation(
        self,
        conversation_id: str,
        context: dict[str, Any],
        status: str = "active",
        current_step: str = "greeting",
    ) -> Any | None:
        if self.executor is None:
            return None

        return self.executor(
            self.create_conversation_sql(),
            {
                "conversation_id": conversation_id,
                "status": status,
                "current_step": current_step,
                "context": context,
            },
        )

    def get_conversation(self, conversation_id: str) -> Any | None:
        if self.executor is None:
            return None

        return self.executor(self.get_conversation_sql(), {"conversation_id": conversation_id})

    def update_context(
        self,
        conversation_id: str,
        context: dict[str, Any],
        status: str | None = None,
        current_step: str | None = None,
    ) -> Any | None:
        if self.executor is None:
            return None

        return self.executor(
            self.update_context_sql(),
            {
                "conversation_id": conversation_id,
                "context": context,
                "status": status,
                "current_step": current_step,
            },
        )

    def create_appointment(
        self,
        conversation_id: str | None,
        patient_name: str,
        patient_phone: str,
        clinic_name: str,
        specialty: str,
        scheduled_at: str,
        context: dict[str, Any],
    ) -> Any | None:
        if self.executor is None:
            return None

        return self.executor(
            self.create_appointment_sql(),
            {
                "conversation_id": conversation_id,
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "clinic_name": clinic_name,
                "specialty": specialty,
                "scheduled_at": scheduled_at,
                "context": context,
            },
        )

    def reset_conversations(self) -> Any | None:
        if self.executor is None:
            return None

        return self.executor(self.reset_conversations_sql(), {})
