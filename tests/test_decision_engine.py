from app.application.decision.service import DecisionEngine
from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus
from app.domain.conversation.state_machine import ConversationStateMachine


def test_decision_engine_starts_with_greeting_step() -> None:
    engine = DecisionEngine()
    state = ConversationStateMachine().start()

    decision = engine.decide(state, "")

    assert decision["next_step"] == ConversationStep.GREETING
    assert decision["reason"] == "greeting"


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
    assert decision["reason"] == "appointment_intent_needs_context"


def test_decision_engine_confirms_when_clinical_context_is_enough() -> None:
    engine = DecisionEngine()
    state = ConversationState(
        current_step=ConversationStep.GREETING,
        status=ConversationStatus.ACTIVE,
        context={"clinical_summary": {"appointment_readiness": "enough_context", "main_complaint": "coceira"}},
    )

    decision = engine.decide(state, "estou com coceira nos dedos tem 3 dias e incomoda muito")

    assert decision["next_step"] == ConversationStep.CONFIRM_APPOINTMENT
    assert decision["reason"] == "enough_clinical_context"


def test_decision_engine_moves_affirmative_confirmation_to_data_collection() -> None:
    engine = DecisionEngine()
    state = ConversationState(
        current_step=ConversationStep.CONFIRM_APPOINTMENT,
        status=ConversationStatus.ACTIVE,
        context={"clinical_summary": {"appointment_readiness": "enough_context", "main_complaint": "coceira"}},
    )

    decision = engine.decide(state, "sim")

    assert decision["next_step"] == ConversationStep.COLLECT_INFORMATION
    assert decision["reason"] == "appointment_confirmed_by_patient"


def test_decision_engine_moves_patient_contact_to_calendar_check() -> None:
    engine = DecisionEngine()
    state = ConversationState(
        current_step=ConversationStep.COLLECT_INFORMATION,
        status=ConversationStatus.ACTIVE,
        context={"patient": {"name": "Ana Silva", "phone": "11999999999"}},
    )

    decision = engine.decide(state, "Ana Silva 11999999999")

    assert decision["next_step"] == ConversationStep.CHECK_CALENDAR
    assert decision["reason"] == "patient_contact_collected"


def test_decision_engine_waits_when_patient_contact_is_partial() -> None:
    engine = DecisionEngine()
    state = ConversationState(
        current_step=ConversationStep.COLLECT_INFORMATION,
        status=ConversationStatus.ACTIVE,
        context={"patient": {"name": "Gustavo Henrique"}, "missing_patient_fields": ["phone"]},
    )

    decision = engine.decide(state, "Gustavo Henrique")

    assert decision["next_step"] == ConversationStep.COLLECT_INFORMATION
    assert decision["reason"] == "missing_patient_contact"


def test_decision_engine_treats_calendar_step_as_slot_selection() -> None:
    engine = DecisionEngine()
    state = ConversationState(
        current_step=ConversationStep.CHECK_CALENDAR,
        status=ConversationStatus.ACTIVE,
        context={"available_slots": ["2026-08-10 09:00"]},
    )

    decision = engine.decide(state, "1")

    assert decision["next_step"] == ConversationStep.BOOK_APPOINTMENT
    assert decision["reason"] == "slot_selection"


def test_decision_engine_finishes_when_appointment_is_already_booked() -> None:
    engine = DecisionEngine()
    state = ConversationState(
        current_step=ConversationStep.BOOK_APPOINTMENT,
        status=ConversationStatus.APPOINTMENT_BOOKED,
        context={"appointment": {"scheduled_at": "2026-08-10 14:00"}},
    )

    decision = engine.decide(state, "ok")

    assert decision["next_step"] == ConversationStep.FINISHED
    assert decision["reason"] == "appointment_already_booked"
