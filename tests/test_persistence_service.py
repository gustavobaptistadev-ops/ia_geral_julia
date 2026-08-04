from app.application.persistence.service import PersistenceService
from app.domain.clinic.models import Appointment, Clinic, Patient
from app.domain.conversation.models import ConversationState, ConversationStatus, ConversationStep


class FakePersistenceRepository:
    def __init__(self) -> None:
        self.conversations: list[dict[str, object]] = []
        self.appointments: list[dict[str, object]] = []
        self.stored_conversations: dict[str, dict[str, object]] = {}

    def create_conversation(
        self,
        conversation_id: str,
        context: dict[str, object],
        status: str = "active",
        current_step: str = "greeting",
    ) -> None:
        self.conversations.append(
            {
                "conversation_id": conversation_id,
                "context": context,
                "status": status,
                "current_step": current_step,
            }
        )
        self.stored_conversations[conversation_id] = self.conversations[-1]

    def update_context(
        self,
        conversation_id: str,
        context: dict[str, object],
        status: str | None = None,
        current_step: str | None = None,
    ) -> None:
        self.conversations.append(
            {
                "conversation_id": conversation_id,
                "context": context,
                "status": status,
                "current_step": current_step,
            }
        )
        self.stored_conversations[conversation_id] = self.conversations[-1]

    def get_conversation(self, conversation_id: str) -> dict[str, object] | None:
        return self.stored_conversations.get(conversation_id)

    def reset_conversations(self) -> None:
        self.conversations.clear()
        self.appointments.clear()
        self.stored_conversations.clear()

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


def test_persistence_service_can_store_and_retrieve_appointment_context() -> None:
    service = PersistenceService()
    patient = Patient(name="Ana", phone="11999999999")
    clinic = Clinic(name="Clínica Vida", specialty="Cardiologia")
    appointment = Appointment(patient_name="Ana", scheduled_at="2026-08-10 09:00", specialty="Cardiologia")

    stored = service.save_appointment(patient, clinic, appointment)

    assert stored["patient_name"] == "Ana"
    assert stored["specialty"] == "Cardiologia"
    assert stored["scheduled_at"] == "2026-08-10 09:00"


def test_persistence_service_rejects_empty_patient_name() -> None:
    service = PersistenceService()
    patient = Patient(name="", phone="11999999999")
    clinic = Clinic(name="Clínica Vida", specialty="Cardiologia")
    appointment = Appointment(patient_name="", scheduled_at="2026-08-10 09:00", specialty="Cardiologia")

    stored = service.save_appointment(patient, clinic, appointment)

    assert stored is None


def test_persistence_service_saves_conversation_state_in_repository() -> None:
    repository = FakePersistenceRepository()
    service = PersistenceService(repository)
    state = ConversationState(
        current_step=ConversationStep.DISCOVER_SYMPTOMS,
        status=ConversationStatus.ACTIVE,
        context={"reason": "consulta"},
        conversation_id="conv-1",
    )

    service.save_conversation_state(state)

    assert repository.conversations[0]["conversation_id"] == "conv-1"
    assert repository.conversations[0]["current_step"] == "discover_symptoms"


def test_persistence_service_loads_conversation_state_from_repository() -> None:
    repository = FakePersistenceRepository()
    repository.stored_conversations["conv-1"] = {
        "conversation_id": "conv-1",
        "current_step": "discover_symptoms",
        "status": "active",
        "context": {"reason": "consulta"},
    }
    service = PersistenceService(repository)

    state = service.load_conversation_state("conv-1")

    assert state is not None
    assert state.conversation_id == "conv-1"
    assert state.current_step == ConversationStep.DISCOVER_SYMPTOMS
    assert state.context["reason"] == "consulta"


def test_persistence_service_uses_safe_defaults_for_invalid_conversation_state() -> None:
    repository = FakePersistenceRepository()
    repository.stored_conversations["conv-1"] = {
        "conversation_id": "conv-1",
        "current_step": "unknown",
        "status": "unknown",
        "context": {},
    }
    service = PersistenceService(repository)

    state = service.load_conversation_state("conv-1")

    assert state is not None
    assert state.current_step == ConversationStep.GREETING
    assert state.status == ConversationStatus.ACTIVE


def test_persistence_service_saves_appointment_in_repository() -> None:
    repository = FakePersistenceRepository()
    service = PersistenceService(repository)
    patient = Patient(name="Ana", phone="11999999999")
    clinic = Clinic(name="Clinica Vida", specialty="Cardiologia")
    appointment = Appointment(patient_name="Ana", scheduled_at="2026-08-10 09:00", specialty="Cardiologia")

    stored = service.save_appointment(
        patient,
        clinic,
        appointment,
        conversation_id="conv-1",
        context={"calendar_event": {"summary": "Consulta"}},
    )

    assert stored is not None
    assert repository.appointments[0]["conversation_id"] == "conv-1"
    assert repository.appointments[0]["specialty"] == "Cardiologia"


def test_persistence_service_resets_conversations_in_repository() -> None:
    repository = FakePersistenceRepository()
    service = PersistenceService(repository)
    repository.stored_conversations["conv-1"] = {"conversation_id": "conv-1"}

    result = service.reset_conversations()

    assert result["reset"] is True
    assert repository.stored_conversations == {}


def test_persistence_service_reset_is_safe_without_repository() -> None:
    result = PersistenceService().reset_conversations()

    assert result["reset"] is True
    assert result["provider"] == "none"
