from __future__ import annotations

from app.application.agenda import AgendaAgent
from app.domain.conversation.models import (
    ConversationState,
    ConversationStatus,
    ConversationStep,
)


class ConversationStateMachine:
    def __init__(self, agenda_agent: AgendaAgent | None = None) -> None:
        self.agenda_agent = agenda_agent or AgendaAgent()

    def start(self) -> ConversationState:
        return ConversationState(
            current_step=ConversationStep.GREETING,
            status=ConversationStatus.ACTIVE,
            context={"messages": [], "symptoms": [], "clinical_summary": {}},
            conversation_id=None,
        )

    def process_message(self, state: ConversationState, message: str) -> ConversationState:
        normalized = message.strip().lower()
        context = self._append_message(state.context, message)

        if self._is_emergency(normalized):
            return ConversationState(
                current_step=ConversationStep.EMERGENCY,
                status=ConversationStatus.EMERGENCY,
                context={**context, "last_message": message},
                conversation_id=state.conversation_id,
            )

        if self._is_greeting(normalized) and not context.get("symptoms"):
            return ConversationState(
                current_step=ConversationStep.GREETING,
                status=state.status,
                context=context,
                conversation_id=state.conversation_id,
            )

        if state.current_step == ConversationStep.COLLECT_INFORMATION:
            return ConversationState(
                current_step=ConversationStep.CHECK_CALENDAR,
                status=state.status,
                context={**context, "patient_details": message, "available_slots": self.default_available_slots()},
                conversation_id=state.conversation_id,
            )

        if state.current_step == ConversationStep.CHECK_CALENDAR:
            selected_slot = self.select_slot(message, context.get("available_slots", []))
            if selected_slot is not None:
                return ConversationState(
                    current_step=ConversationStep.BOOK_APPOINTMENT,
                    status=state.status,
                    context={**context, "selected_slot": selected_slot},
                    conversation_id=state.conversation_id,
                )

            return ConversationState(
                current_step=ConversationStep.CHECK_CALENDAR,
                status=state.status,
                context={**context, "calendar_selection_error": True},
                conversation_id=state.conversation_id,
            )

        if state.current_step == ConversationStep.CONFIRM_APPOINTMENT:
            if self._is_affirmative(normalized) or self._is_appointment_intent(normalized):
                return ConversationState(
                    current_step=ConversationStep.COLLECT_INFORMATION,
                    status=state.status,
                    context={**context, "appointment_intent": True},
                    conversation_id=state.conversation_id,
                )

            if self._is_negative(normalized):
                return ConversationState(
                    current_step=ConversationStep.DISCOVER_SYMPTOMS,
                    status=state.status,
                    context={**context, "appointment_intent": False},
                    conversation_id=state.conversation_id,
                )

        appointment_intent = self._is_appointment_intent(normalized)
        symptoms = self._updated_symptoms(context, message, appointment_intent)
        context = {**context, "symptoms": symptoms}
        has_enough_context = self._has_enough_clinical_context(context)

        if appointment_intent and (symptoms or has_enough_context):
            return ConversationState(
                current_step=ConversationStep.COLLECT_INFORMATION,
                status=state.status,
                context={**context, "appointment_intent": True},
                conversation_id=state.conversation_id,
            )

        if appointment_intent:
            return ConversationState(
                current_step=ConversationStep.DISCOVER_SYMPTOMS,
                status=state.status,
                context={**context, "appointment_intent": True, "reason": context.get("reason", message)},
                conversation_id=state.conversation_id,
            )

        if has_enough_context or len(symptoms) >= 2:
            return ConversationState(
                current_step=ConversationStep.CONFIRM_APPOINTMENT,
                status=state.status,
                context={**context, "reason": context.get("reason", symptoms[0])},
                conversation_id=state.conversation_id,
            )

        return ConversationState(
            current_step=ConversationStep.DISCOVER_SYMPTOMS,
            status=state.status,
            context={**context, "reason": context.get("reason", message)},
            conversation_id=state.conversation_id,
        )

    def default_available_slots(self) -> list[str]:
        return self.agenda_agent.default_available_slots()

    def append_message(self, context: dict[str, object], message: str) -> dict[str, object]:
        return self._append_message(context, message)

    def select_slot(self, message: str, slots: object) -> str | None:
        return self.agenda_agent.select_slot(message, slots)

    def slot_candidates(self, message: str, slots: object) -> list[str]:
        return self.agenda_agent.slot_candidates(message, slots)

    def _append_message(self, context: dict[str, object], message: str) -> dict[str, object]:
        messages = list(context.get("messages", []))
        messages.append({"role": "patient", "content": message})
        return {**context, "messages": messages, "last_message": message}

    def _updated_symptoms(self, context: dict[str, object], message: str, appointment_intent: bool) -> list[str]:
        symptoms = list(context.get("symptoms", []))
        normalized = message.strip().lower()
        summary = context.get("clinical_summary")
        main_complaint = summary.get("main_complaint") if isinstance(summary, dict) else None
        if main_complaint:
            return symptoms

        if not appointment_intent and not self._is_affirmative(normalized) and not self._is_negative(normalized) and message.strip():
            symptoms.append(message)
        return symptoms

    def _is_emergency(self, message: str) -> bool:
        emergency_keywords = [
            "falta de ar grave",
            "convulsao",
            "dor intensa no peito",
            "perda de consciencia",
            "choque anafilatico",
            "sangramento intenso",
            "reacao alergica grave",
        ]
        return any(keyword in message for keyword in emergency_keywords)

    def _is_appointment_intent(self, message: str) -> bool:
        appointment_keywords = ["agendar", "consulta", "marcar", "atendimento"]
        return any(keyword in message for keyword in appointment_keywords)

    def _has_enough_clinical_context(self, context: dict[str, object]) -> bool:
        summary = context.get("clinical_summary")
        return isinstance(summary, dict) and summary.get("appointment_readiness") == "enough_context"

    def _is_greeting(self, message: str) -> bool:
        greetings = {"oi", "ola", "olá", "bom dia", "boa tarde", "boa noite"}
        return message in greetings

    def _is_affirmative(self, message: str) -> bool:
        affirmatives = {
            "sim",
            "quero",
            "pode ser",
            "vamos",
            "vamos sim",
            "por favor",
            "me ajuda",
            "quero marcar",
            "quero agendar",
        }
        return message in affirmatives

    def _is_negative(self, message: str) -> bool:
        negatives = {"nao", "não", "agora nao", "agora não", "nao quero", "não quero"}
        return message in negatives
