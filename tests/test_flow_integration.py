from app.application.orchestrator.service import ConversationOrchestrator
from app.domain.clinic.models import Clinic, Patient
from app.application.appointment.service import AppointmentService


def test_orchestrator_can_create_appointment_payload() -> None:
    orchestrator = ConversationOrchestrator()
    service = AppointmentService()

    patient = Patient(name="Ana", phone="11999999999")
    clinic = Clinic(name="Clínica Vida", specialty="Cardiologia")
    appointment = service.create_appointment(patient, clinic, "2026-08-10 09:00")

    result = orchestrator.handle_message("Quero agendar uma consulta", None)

    assert result["reply"]["next_step"] == "discover_symptoms"
    assert appointment is not None
    assert appointment.specialty == "Cardiologia"
