from app.domain.conversation.models import ConversationState, ConversationStep
from app.application.conversation.service import ConversationEngine
from app.domain.conversation.state_machine import ConversationStateMachine


def test_engine_returns_greeting_message_for_new_conversation() -> None:
    engine = ConversationEngine()
    state = ConversationStateMachine().start()

    response = engine.generate_reply(state, "")

    assert response["message"].startswith("Olá")
    assert response["next_step"] == ConversationStep.GREETING


def test_engine_returns_emergency_message_for_alarm_state() -> None:
    engine = ConversationEngine()
    machine = ConversationStateMachine()
    state = machine.process_message(machine.start(), "Estou com falta de ar grave")

    response = engine.generate_reply(state, "Estou com falta de ar grave")

    assert "Samu" in response["message"]
    assert response["next_step"] == ConversationStep.EMERGENCY


def test_engine_acknowledges_reason_and_requests_symptoms() -> None:
    engine = ConversationEngine()
    machine = ConversationStateMachine()
    state = machine.process_message(machine.start(), "Preciso agendar uma consulta para dor de cabeça")

    response = engine.generate_reply(state, "Preciso agendar uma consulta para dor de cabeça")

    assert "dor de cabeça" in response["message"]
    assert response["next_step"] == ConversationStep.DISCOVER_SYMPTOMS
