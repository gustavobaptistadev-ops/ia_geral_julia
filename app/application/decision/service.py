from __future__ import annotations

from unicodedata import combining, normalize

from app.domain.conversation.context import ConversationContext
from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus


class DecisionEngine:
    def decide(self, state: ConversationState, message: str) -> dict[str, object]:
        normalized = self._normalize(message)
        context = ConversationContext.from_dict(state.context)

        if not normalized and state.current_step == ConversationStep.GREETING:
            return {"next_step": ConversationStep.GREETING, "reason": "greeting"}

        if state.status == ConversationStatus.EMERGENCY or self._is_emergency(normalized):
            return {"next_step": ConversationStep.EMERGENCY, "reason": "emergency"}

        if state.status == ConversationStatus.APPOINTMENT_BOOKED or state.current_step == ConversationStep.BOOK_APPOINTMENT:
            return {"next_step": ConversationStep.FINISHED, "reason": "appointment_already_booked"}

        if self._is_greeting(normalized) and not context.clinical.has_main_complaint():
            return {"next_step": ConversationStep.GREETING, "reason": "greeting"}

        if state.current_step == ConversationStep.CHECK_CALENDAR:
            return {"next_step": ConversationStep.BOOK_APPOINTMENT, "reason": "slot_selection"}

        if state.current_step == ConversationStep.COLLECT_INFORMATION:
            if context.patient_is_complete():
                return {"next_step": ConversationStep.CHECK_CALENDAR, "reason": "patient_contact_collected"}
            return {"next_step": ConversationStep.COLLECT_INFORMATION, "reason": "missing_patient_contact"}

        if state.current_step == ConversationStep.CONFIRM_APPOINTMENT:
            if self._is_affirmative(normalized) or self._is_appointment_intent(normalized):
                return {"next_step": ConversationStep.COLLECT_INFORMATION, "reason": "appointment_confirmed_by_patient"}
            if self._is_negative(normalized):
                return {"next_step": ConversationStep.DISCOVER_SYMPTOMS, "reason": "appointment_declined_by_patient"}
            return {"next_step": ConversationStep.CONFIRM_APPOINTMENT, "reason": "awaiting_appointment_confirmation"}

        if context.clinical.is_ready_for_appointment():
            return {"next_step": ConversationStep.CONFIRM_APPOINTMENT, "reason": "enough_clinical_context"}

        if self._is_appointment_intent(normalized):
            return {"next_step": ConversationStep.DISCOVER_SYMPTOMS, "reason": "appointment_intent_needs_context"}

        if context.has_partial_clinical_context():
            return {"next_step": ConversationStep.DISCOVER_SYMPTOMS, "reason": "missing_clinical_context"}

        return {"next_step": state.current_step, "reason": "continue_flow"}

    def _is_emergency(self, message: str) -> bool:
        emergency_keywords = [
            "falta de ar grave",
            "nao consigo respirar",
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

    def _is_greeting(self, message: str) -> bool:
        greetings = {"oi", "ola", "bom dia", "boa tarde", "boa noite"}
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
        negatives = {"nao", "agora nao", "nao quero"}
        return message in negatives

    def _normalize(self, message: str) -> str:
        without_accents = "".join(
            char for char in normalize("NFD", message.strip().lower())
            if not combining(char)
        )
        return without_accents
