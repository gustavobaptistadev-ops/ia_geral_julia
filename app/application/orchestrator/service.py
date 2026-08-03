from __future__ import annotations

from app.application.conversation.service import ConversationEngine
from app.application.decision.service import DecisionEngine
from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus
from app.domain.conversation.state_machine import ConversationStateMachine


class ConversationOrchestrator:
    def __init__(self) -> None:
        self.state_machine = ConversationStateMachine()
        self.conversation_engine = ConversationEngine()
        self.decision_engine = DecisionEngine()

    def handle_message(self, message: str, state: ConversationState | None) -> dict[str, object]:
        current_state = state or self.state_machine.start()

        if not message.strip():
            next_state = current_state
            reply = self.conversation_engine.generate_reply(next_state, message)
            return {"state": next_state, "reply": reply}

        decision = self.decision_engine.decide(current_state, message)

        if decision["next_step"] == ConversationStep.EMERGENCY:
            next_state = ConversationState(
                current_step=ConversationStep.EMERGENCY,
                status=ConversationStatus.EMERGENCY,
                context={**current_state.context, "last_message": message},
                conversation_id=current_state.conversation_id,
            )
        else:
            next_state = self.state_machine.process_message(current_state, message)

        reply = self.conversation_engine.generate_reply(next_state, message)

        return {"state": next_state, "reply": reply}
