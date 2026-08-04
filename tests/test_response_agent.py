from app.application.response import ResponseAgent
from app.domain.conversation.models import ConversationState, ConversationStatus, ConversationStep


def test_response_agent_formats_worsening_symptom_with_empathy() -> None:
    state = ConversationState(
        current_step=ConversationStep.CONFIRM_APPOINTMENT,
        status=ConversationStatus.ACTIVE,
        context={"clinical_summary": {"progression": "piorando"}},
    )

    response = ResponseAgent().generate_reply(state, "esta piorando")

    assert response["message"].startswith("Poxa, sinto muito que esteja piorando.")
    assert "que tal olharmos um horario na agenda" in response["message"]


def test_response_agent_formats_calendar_slots_naturally() -> None:
    state = ConversationState(
        current_step=ConversationStep.CHECK_CALENDAR,
        status=ConversationStatus.ACTIVE,
        context={"available_slots": ["2026-08-11 10:00", "2026-08-10 09:00"]},
    )

    response = ResponseAgent().generate_reply(state, "")

    assert "Tenho vaga segunda-feira as 9h ou terca-feira as 10h" in response["message"]
    assert "1." not in response["message"]


def test_response_agent_formats_confirmed_slot_in_brazilian_date() -> None:
    state = ConversationState(
        current_step=ConversationStep.BOOK_APPOINTMENT,
        status=ConversationStatus.APPOINTMENT_BOOKED,
        context={"selected_slot": "2026-08-11 10:00"},
    )

    response = ResponseAgent().generate_reply(state, "terca")

    assert "Horario: terca-feira, 11/08/2026 as 10h" in response["message"]
