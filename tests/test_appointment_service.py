from app.application.appointment.service import AppointmentService
from app.domain.clinic.models import Appointment, Clinic, Patient


def test_appointment_service_creates_appointment_from_domain_data() -> None:
    service = AppointmentService()
    patient = Patient(name="Ana", phone="11999999999")
    clinic = Clinic(name="Clínica Vida", specialty="Cardiologia")

    appointment = service.create_appointment(patient, clinic, "2026-08-10 09:00")

    assert isinstance(appointment, Appointment)
    assert appointment.patient_name == "Ana"
    assert appointment.scheduled_at == "2026-08-10 09:00"
    assert appointment.specialty == "Cardiologia"


def test_appointment_service_rejects_missing_patient_name() -> None:
    service = AppointmentService()
    patient = Patient(name="", phone="11999999999")
    clinic = Clinic(name="Clínica Vida", specialty="Cardiologia")

    appointment = service.create_appointment(patient, clinic, "2026-08-10 09:00")

    assert appointment is None
