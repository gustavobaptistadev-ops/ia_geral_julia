from __future__ import annotations

from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus


class ConversationEngine:
    def generate_reply(self, state: ConversationState, message: str) -> dict[str, object]:
        if state.status == ConversationStatus.EMERGENCY:
            return {
                "message": "Estou vendo que você precisa de ajuda imediata. Por favor, procure o Samu pelo 192 agora mesmo e peça apoio médico urgente.",
                "next_step": ConversationStep.EMERGENCY,
                "should_handoff": True,
            }

        if state.current_step == ConversationStep.GREETING:
            return {
                "message": "Olá! Eu sou a LifelineOne. Estou aqui para te ajudar de forma acolhedora e simples. Como posso te ajudar hoje?",
                "next_step": ConversationStep.GREETING,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.DISCOVER_SYMPTOMS:
            return {
                "message": f"Entendi que você está falando sobre: {state.context.get('reason', 'seu motivo')}. Pode me contar um pouco mais sobre os sintomas ou o que você sente?",
                "next_step": ConversationStep.DISCOVER_SYMPTOMS,
                "should_handoff": False,
            }

        return {
            "message": "Entendi. Vou te acompanhar com calma e vou tentar te ajudar a encontrar o melhor próximo passo.",
            "next_step": state.current_step,
            "should_handoff": False,
        }
