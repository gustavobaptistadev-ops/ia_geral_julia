from __future__ import annotations

from app.domain.conversation.models import (
    ConversationStatus,
    ConversationStep,
    ConversationState,
)


class ConversationStateMachine:
    def start(self) -> ConversationState:
        return ConversationState(
            current_step=ConversationStep.GREETING,
            status=ConversationStatus.ACTIVE,
            context={},
            conversation_id=None,
        )

    def process_message(self, state: ConversationState, message: str) -> ConversationState:
        normalized = message.strip().lower()

        if self._is_emergency(normalized):
            return ConversationState(
                current_step=ConversationStep.EMERGENCY,
                status=ConversationStatus.EMERGENCY,
                context={**state.context, "last_message": message},
                conversation_id=state.conversation_id,
            )

        if not state.context.get("reason"):
            return ConversationState(
                current_step=ConversationStep.DISCOVER_SYMPTOMS,
                status=state.status,
                context={**state.context, "reason": message, "last_message": message},
                conversation_id=state.conversation_id,
            )

        return ConversationState(
            current_step=ConversationStep.DISCOVER_REASON,
            status=state.status,
            context={**state.context, "last_message": message},
            conversation_id=state.conversation_id,
        )

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
