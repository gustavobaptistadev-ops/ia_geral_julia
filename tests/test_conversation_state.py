from app.domain.conversation.models import ConversationStatus, ConversationStep
from app.domain.conversation.state_machine import ConversationStateMachine


def test_state_machine_starts_in_greeting() -> None:
    state = ConversationStateMachine().start()

    assert state.current_step == ConversationStep.GREETING
    assert state.status == ConversationStatus.ACTIVE


def test_emergency_message_transitions_to_emergency() -> None:
    machine = ConversationStateMachine()
    initial_state = machine.start()

    next_state = machine.process_message(initial_state, "Estou com falta de ar grave e não consigo respirar")

    assert next_state.current_step == ConversationStep.EMERGENCY
    assert next_state.status == ConversationStatus.EMERGENCY


def test_reason_message_advances_to_discover_symptoms() -> None:
    machine = ConversationStateMachine()
    initial_state = machine.start()

    next_state = machine.process_message(initial_state, "Preciso agendar uma consulta para dor de cabeça")

    assert next_state.current_step == ConversationStep.DISCOVER_SYMPTOMS
    assert next_state.context["reason"] == "Preciso agendar uma consulta para dor de cabeça"
