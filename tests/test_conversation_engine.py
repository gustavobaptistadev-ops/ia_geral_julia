from app.application.conversation.service import ConversationEngine
from app.domain.conversation.models import ConversationState, ConversationStatus, ConversationStep
from app.domain.conversation.state_machine import ConversationStateMachine


def test_engine_returns_greeting_message_for_new_conversation() -> None:
    engine = ConversationEngine()
    state = ConversationStateMachine().start()

    response = engine.generate_reply(state, "")

    assert response["message"].startswith("Oi! Aqui e a Julia")
    assert response["next_step"] == ConversationStep.GREETING


def test_engine_returns_emergency_message_for_alarm_state() -> None:
    engine = ConversationEngine()
    machine = ConversationStateMachine()
    state = machine.process_message(machine.start(), "Estou com falta de ar grave")

    response = engine.generate_reply(state, "Estou com falta de ar grave")

    assert "Samu" in response["message"]
    assert response["next_step"] == ConversationStep.EMERGENCY


def test_engine_returns_safety_message_when_context_requires_handoff() -> None:
    engine = ConversationEngine()
    state = ConversationState(
        current_step=ConversationStep.GREETING,
        status=ConversationStatus.ACTIVE,
        context={"safety_message": "Nao posso prescrever medicamentos por aqui."},
    )

    response = engine.generate_reply(state, "Qual remedio eu tomo?")

    assert response["message"] == "Nao posso prescrever medicamentos por aqui."
    assert response["should_handoff"] is True


def test_engine_requests_main_complaint_when_only_appointment_intent_exists() -> None:
    engine = ConversationEngine()
    machine = ConversationStateMachine()
    state = machine.process_message(machine.start(), "Preciso agendar uma consulta")

    response = engine.generate_reply(state, "Preciso agendar uma consulta")

    assert response["message"] == "Certo, me conta qual sintoma ou motivo principal da consulta."
    assert response["next_step"] == ConversationStep.DISCOVER_SYMPTOMS


def test_engine_asks_only_missing_duration_from_summary() -> None:
    engine = ConversationEngine()
    state = ConversationState(
        current_step=ConversationStep.DISCOVER_SYMPTOMS,
        status=ConversationStatus.ACTIVE,
        context={
            "clinical_summary": {
                "main_complaint": "coceira nos dedos",
                "missing_fields": ["duration", "severity_or_progression"],
            }
        },
    )

    response = engine.generate_reply(state, "estou com coceira nos dedos")

    assert response["message"] == "Entendi, ha quanto tempo isto esta ocorrendo?"
    assert "contexto" not in response["message"].lower()
