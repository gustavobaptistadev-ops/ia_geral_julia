from app.application.booking import AppointmentBookingAgent
from app.application.persistence.service import PersistenceService
from app.domain.conversation.models import ConversationState, ConversationStatus, ConversationStep


class FakeAppointmentRepository:
    def __init__(self) -> None:
        self.appointments: list[dict[str, object]] = []

    def create_conversation(
        self,
        conversation_id: str,
        context: dict[str, object],
        status: str = "active",
        current_step: str = "greeting",
    ) -> None:
        return None

    def update_context(
        self,
        conversation_id: str,
        context: dict[str, object],
        status: str | None = None,
        current_step: str | None = None,
    ) -> None:
        return None

    def get_conversation(self, conversation_id: str) -> dict[str, object] | None:
        return None

    def reset_conversations(self) -> None:
        return None

    def create_appointment(
        self,
        conversation_id: str | None,
        patient_name: str,
        patient_phone: str,
        clinic_name: str,
        specialty: str,
        scheduled_at: str,
        context: dict[str, object],
    ) -> None:
        self.appointments.append(
            {
                "conversation_id": conversation_id,
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "clinic_name": clinic_name,
                "specialty": specialty,
                "scheduled_at": scheduled_at,
                "context": context,
            }
        )


def test_booking_agent_confirms_and_persists_appointment() -> None:
    repository = FakeAppointmentRepository()
    agent = AppointmentBookingAgent(persistence_service=PersistenceService(repository))
    state = ConversationState(
        current_step=ConversationStep.BOOK_APPOINTMENT,
        status=ConversationStatus.APPOINTMENT_BOOKED,
        context={
            "patient": {"name": "Ana Silva", "phone": "11999999999"},
            "selected_slot": "2026-08-10 09:00",
        },
        conversation_id="conv-1",
    )

    result = agent.confirm_appointment(state)

    assert result.context["appointment"]["patient_name"] == "Ana Silva"
    assert result.context["appointment"]["scheduled_at"] == "2026-08-10 09:00"
    assert repository.appointments[0]["conversation_id"] == "conv-1"
    assert repository.appointments[0]["patient_name"] == "Ana Silva"


def test_booking_agent_uses_patient_details_as_name_fallback() -> None:
    agent = AppointmentBookingAgent()
    state = ConversationState(
        current_step=ConversationStep.BOOK_APPOINTMENT,
        status=ConversationStatus.APPOINTMENT_BOOKED,
        context={"patient_details": "Gustavo Henrique, 61991773474", "selected_slot": "2026-08-10 14:00"},
        conversation_id="conv-1",
    )

    assert agent.patient_name_from_context(state) == "Gustavo Henrique"
