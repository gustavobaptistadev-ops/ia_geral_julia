from app.application.persistence.service import PersistenceService
from app.domain.clinic.models import Appointment, Clinic, Patient


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
