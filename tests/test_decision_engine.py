from app.application.decision.service import DecisionEngine
from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus
from app.domain.conversation.state_machine import ConversationStateMachine


def test_decision_engine_starts_with_greeting_step() -> None:
    engine = DecisionEngine()
    state = ConversationStateMachine().start()

    decision = engine.decide(state, "")

    assert decision["next_step"] == ConversationStep.GREETING
    assert decision["reason"] == "initial_greeting"


def test_decision_engine_detects_emergency() -> None:
    engine = DecisionEngine()
    state = ConversationStateMachine().process_message(ConversationStateMachine().start(), "Estou com falta de ar grave")

    decision = engine.decide(state, "Estou com falta de ar grave")

    assert decision["next_step"] == ConversationStep.EMERGENCY
    assert decision["reason"] == "emergency"


def test_decision_engine_detects_appointment_intent() -> None:
    engine = DecisionEngine()
    state = ConversationStateMachine().process_message(ConversationStateMachine().start(), "Quero agendar uma consulta")

    decision = engine.decide(state, "Quero agendar uma consulta")

    assert decision["next_step"] == ConversationStep.DISCOVER_SYMPTOMS
    assert decision["reason"] == "appointment_intent"
