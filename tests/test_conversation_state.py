from app.domain.conversation.models import ConversationStatus, ConversationStep
from app.domain.conversation.state_machine import ConversationStateMachine


def test_state_machine_starts_in_greeting() -> None:
    state = ConversationStateMachine().start()

    assert state.current_step == ConversationStep.GREETING
    assert state.status == ConversationStatus.ACTIVE


def test_emergency_message_transitions_to_emergency() -> None:
    machine = ConversationStateMachine()
    initial_state = machine.start()

    next_state = machine.process_message(initial_state, "Estou com falta de ar grave e nao consigo respirar")

    assert next_state.current_step == ConversationStep.EMERGENCY
    assert next_state.status == ConversationStatus.EMERGENCY


def test_reason_message_advances_to_discover_symptoms() -> None:
    machine = ConversationStateMachine()
    initial_state = machine.start()

    next_state = machine.process_message(initial_state, "Preciso agendar uma consulta para dor de cabeca")

    assert next_state.current_step == ConversationStep.DISCOVER_SYMPTOMS
    assert next_state.context["reason"] == "Preciso agendar uma consulta para dor de cabeca"


def test_greeting_does_not_become_symptom() -> None:
    machine = ConversationStateMachine()

    next_state = machine.process_message(machine.start(), "ola")

    assert next_state.current_step == ConversationStep.GREETING
    assert next_state.context["symptoms"] == []


def test_state_machine_accumulates_symptoms_before_confirming_appointment() -> None:
    machine = ConversationStateMachine()
    first = machine.process_message(machine.start(), "coceira nos dedos")
    second = machine.process_message(first, "incomodo nos dedos com essa coceira")

    assert second.current_step == ConversationStep.CONFIRM_APPOINTMENT
    assert second.context["symptoms"] == ["coceira nos dedos", "incomodo nos dedos com essa coceira"]


def test_state_machine_collects_patient_data_before_calendar_check() -> None:
    machine = ConversationStateMachine()
    state = machine.process_message(machine.start(), "coceira nos dedos")
    state = machine.process_message(state, "incomodo nos dedos com essa coceira")
    state = machine.process_message(state, "quero marcar consulta")

    next_state = machine.process_message(state, "Ana Silva, 11999999999, de manha")

    assert next_state.current_step == ConversationStep.CHECK_CALENDAR
    assert next_state.context["patient_details"] == "Ana Silva, 11999999999, de manha"
    assert next_state.context["available_slots"]


def test_state_machine_affirmative_confirmation_moves_to_collect_information() -> None:
    machine = ConversationStateMachine()
    state = machine.process_message(machine.start(), "coceira nos dedos")
    state = machine.process_message(state, "tem 3 dias e esta piorando")

    next_state = machine.process_message(state, "sim")

    assert next_state.current_step == ConversationStep.COLLECT_INFORMATION
    assert next_state.context["symptoms"] == ["coceira nos dedos", "tem 3 dias e esta piorando"]


def test_state_machine_selects_calendar_slot_by_period_before_booking() -> None:
    machine = ConversationStateMachine()
    state = machine.process_message(machine.start(), "coceira nos dedos")
    state = machine.process_message(state, "incomodo nos dedos com essa coceira")
    state = machine.process_message(state, "quero marcar consulta")
    state = machine.process_message(state, "Ana Silva, 11999999999, de manha")

    next_state = machine.process_message(state, "pode ser de tarde")

    assert next_state.current_step == ConversationStep.BOOK_APPOINTMENT
    assert next_state.context["selected_slot"] == "2026-08-10 14:00"


def test_state_machine_selects_calendar_slot_by_weekday_and_period_before_booking() -> None:
    machine = ConversationStateMachine()
    state = machine.process_message(machine.start(), "coceira nos dedos")
    state = machine.process_message(state, "incomodo nos dedos com essa coceira")
    state = machine.process_message(state, "quero marcar consulta")
    state = machine.process_message(state, "Ana Silva, 11999999999, de manha")

    next_state = machine.process_message(state, "prefiro segunda de manha")

    assert next_state.current_step == ConversationStep.BOOK_APPOINTMENT
    assert next_state.context["selected_slot"] == "2026-08-10 09:00"


def test_state_machine_returns_multiple_candidates_for_ambiguous_weekday() -> None:
    machine = ConversationStateMachine()

    candidates = machine.slot_candidates("segunda", machine.default_available_slots())

    assert candidates == ["2026-08-10 09:00", "2026-08-10 14:00"]
