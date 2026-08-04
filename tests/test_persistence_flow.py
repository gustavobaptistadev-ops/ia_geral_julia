from app.application.orchestrator.service import ConversationOrchestrator
from app.application.persistence.service import PersistenceService
from app.domain.clinic.models import Appointment, Clinic, Patient


def test_orchestrator_persists_appointment_context() -> None:
    orchestrator = ConversationOrchestrator()
    persistence = PersistenceService()

    result = orchestrator.handle_message("Quero agendar uma consulta", None)
    patient = Patient(name="Ana", phone="11999999999")
    clinic = Clinic(name="Clínica Vida", specialty="Cardiologia")
    appointment = Appointment(patient_name="Ana", scheduled_at="2026-08-10 09:00", specialty="Cardiologia")

    persisted = persistence.save_appointment(patient, clinic, appointment)

    assert result["reply"]["next_step"] == "discover_symptoms"
    assert persisted is not None
    assert persisted["specialty"] == "Cardiologia"
