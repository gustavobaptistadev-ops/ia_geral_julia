from __future__ import annotations

from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus


class DecisionEngine:
    def decide(self, state: ConversationState, message: str) -> dict[str, object]:
        normalized = message.strip().lower()

        if state.status == ConversationStatus.EMERGENCY:
            return {"next_step": ConversationStep.EMERGENCY, "reason": "emergency"}

        if self._is_emergency(normalized):
            return {"next_step": ConversationStep.EMERGENCY, "reason": "emergency"}

        if self._is_appointment_intent(normalized):
            return {"next_step": ConversationStep.DISCOVER_SYMPTOMS, "reason": "appointment_intent"}

        if state.current_step == ConversationStep.GREETING:
            return {"next_step": ConversationStep.GREETING, "reason": "initial_greeting"}

        return {"next_step": state.current_step, "reason": "continue_flow"}

    def _is_emergency(self, message: str) -> bool:
        emergency_keywords = [
            "falta de ar grave",
            "convulsao",
            "dor intensa no peito",
            "perda de consciência",
            "choque anafilático",
            "sangramento intenso",
            "reação alérgica grave",
        ]
        return any(keyword in message for keyword in emergency_keywords)

    def _is_appointment_intent(self, message: str) -> bool:
        appointment_keywords = ["agendar", "consulta", "marcar", "atendimento"]
        return any(keyword in message for keyword in appointment_keywords)
