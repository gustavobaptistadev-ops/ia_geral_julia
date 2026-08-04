from app.application.voice import VoiceAgent
from app.domain.conversation.models import ConversationState, ConversationStatus, ConversationStep


def test_voice_agent_varies_discovery_acknowledgement_by_context_size() -> None:
    state = ConversationState(
        current_step=ConversationStep.DISCOVER_SYMPTOMS,
        status=ConversationStatus.ACTIVE,
        context={
            "messages": [{"role": "patient", "content": "alergia"}],
            "clinical_summary": {"main_complaint": "alergia", "missing_fields": ["duration"]},
        },
    )

    message = VoiceAgent().discover_symptoms(state, "alergia")

    assert message == "Entendi, ha quanto tempo isto esta ocorrendo?"


def test_voice_agent_formats_worsening_confirmation_with_empathy() -> None:
    state = ConversationState(
        current_step=ConversationStep.CONFIRM_APPOINTMENT,
        status=ConversationStatus.ACTIVE,
        context={"clinical_summary": {"progression": "piorando"}},
    )

    message = VoiceAgent().confirm_appointment(state)

    assert message.startswith("Poxa, sinto muito que esteja piorando.")
    assert "que tal olharmos um horario na agenda" in message


def test_voice_agent_formats_calendar_without_numbered_menu() -> None:
    message = VoiceAgent().calendar_options_intro(["2026-08-11 10:00", "2026-08-10 09:00"])

    assert "Tenho vaga segunda-feira as 9h ou terca-feira as 10h" in message
    assert "1." not in message
    assert "Escolha" not in message


def test_voice_agent_formats_booking_confirmation() -> None:
    message = VoiceAgent().booked_appointment("2026-08-10 14:00")

    assert "Horario: segunda-feira, 10/08/2026 as 14h" in message
    assert "Endereco: Clinica LifelineOne" in message
