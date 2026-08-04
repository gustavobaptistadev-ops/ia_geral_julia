from __future__ import annotations

from typing import Any


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._conversations: dict[str, dict[str, Any]] = {}
        self._appointments: list[dict[str, Any]] = []

    def create_conversation(
        self,
        conversation_id: str,
        context: dict[str, Any] | None = None,
        status: str = "active",
        current_step: str = "greeting",
    ) -> str:
        self._conversations[conversation_id] = {
            "conversation_id": conversation_id,
            "context": context or {},
            "status": status,
            "current_step": current_step,
        }
        return conversation_id

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        return self._conversations.get(conversation_id)

    def update_context(
        self,
        conversation_id: str,
        context: dict[str, Any],
        status: str | None = None,
        current_step: str | None = None,
    ) -> None:
        conversation = self._conversations.get(conversation_id)
        if conversation is not None:
            conversation["context"].update(context)
            if status is not None:
                conversation["status"] = status
            if current_step is not None:
                conversation["current_step"] = current_step

    def create_appointment(
        self,
        conversation_id: str | None,
        patient_name: str,
        patient_phone: str,
        clinic_name: str,
        specialty: str,
        scheduled_at: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        appointment = {
            "conversation_id": conversation_id,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "clinic_name": clinic_name,
            "specialty": specialty,
            "scheduled_at": scheduled_at,
            "context": context,
        }
        self._appointments.append(appointment)
        return appointment

    def reset_conversations(self) -> None:
        self._conversations.clear()
        self._appointments.clear()
