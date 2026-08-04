from __future__ import annotations

from app.application.response import ResponseAgent
from app.domain.conversation.models import ConversationState


class ConversationEngine:
    def __init__(self, response_agent: ResponseAgent | None = None) -> None:
        self.response_agent = response_agent or ResponseAgent()

    def generate_reply(self, state: ConversationState, message: str) -> dict[str, object]:
        return self.response_agent.generate_reply(state, message)
