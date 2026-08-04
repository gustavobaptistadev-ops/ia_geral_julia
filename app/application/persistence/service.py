from __future__ import annotations

from typing import Any, Protocol

from app.domain.clinic.models import Appointment, Clinic, Patient
from app.domain.conversation.models import ConversationState


class ConversationPersistenceRepository(Protocol):
    def create_conversation(
        self,
        conversation_id: str,
        context: dict[str, Any],
        status: str = "active",
        current_step: str = "greeting",
    ) -> Any | None:
        ...

    def update_context(
        self,
        conversation_id: str,
        context: dict[str, Any],
        status: str | None = None,
        current_step: str | None = None,
    ) -> Any | None:
        ...

    def get_conversation(self, conversation_id: str) -> Any | None:
        ...

    def reset_conversations(self) -> Any | None:
        ...

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
        ...


class PersistenceService:
    def __init__(self, repository: ConversationPersistenceRepository | None = None) -> None:
        self.repository = repository

    def load_conversation_state(self, conversation_id: str | None) -> ConversationState | None:
        if self.repository is None or conversation_id is None:
            return None

        stored = self.repository.get_conversation(conversation_id)
        if stored is None:
            return None

        return ConversationState(
            current_step=self._safe_step(stored.get("current_step")),
            status=self._safe_status(stored.get("status")),
            context=stored.get("context") or {},
            conversation_id=stored.get("conversation_id") or conversation_id,
        )

    def save_conversation_state(self, state: ConversationState) -> None:
        if self.repository is None or state.conversation_id is None:
            return

        self.repository.create_conversation(
            state.conversation_id,
            state.context,
            status=state.status.value,
            current_step=state.current_step.value,
        )

    def update_conversation_context(self, state: ConversationState) -> None:
        if self.repository is None or state.conversation_id is None:
            return

        self.repository.update_context(
            state.conversation_id,
            state.context,
            status=state.status.value,
            current_step=state.current_step.value,
        )

    def save_appointment(
        self,
        patient: Patient,
        clinic: Clinic,
        appointment: Appointment,
        conversation_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, str] | None:
        if not patient.name.strip() or not appointment.patient_name.strip():
            return None

        stored = {
            "patient_name": appointment.patient_name,
            "specialty": appointment.specialty,
            "scheduled_at": appointment.scheduled_at,
            "clinic_name": clinic.name,
        }

        if self.repository is not None:
            self.repository.create_appointment(
                conversation_id,
                appointment.patient_name,
                patient.phone,
                clinic.name,
                appointment.specialty,
                appointment.scheduled_at,
                context or {},
            )

        return stored

    def reset_conversations(self) -> dict[str, object]:
        if self.repository is None:
            return {"reset": True, "provider": "none", "detail": "Nenhuma persistencia ativa para limpar."}

        self.repository.reset_conversations()
        return {"reset": True, "provider": self.repository.__class__.__name__}

    def _safe_step(self, value: object) -> Any:
        from app.domain.conversation.models import ConversationStep

        try:
            return ConversationStep(value)
        except ValueError:
            return ConversationStep.GREETING

    def _safe_status(self, value: object) -> Any:
        from app.domain.conversation.models import ConversationStatus

        try:
            return ConversationStatus(value)
        except ValueError:
            return ConversationStatus.ACTIVE
