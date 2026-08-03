from app.domain.clinic.models import Appointment, Clinic, Patient


def test_clinic_can_be_created() -> None:
    clinic = Clinic(name="Clínica Vida", specialty="Cardiologia")

    assert clinic.name == "Clínica Vida"
    assert clinic.specialty == "Cardiologia"


def test_patient_can_be_created() -> None:
    patient = Patient(name="Ana", phone="11999999999")

    assert patient.name == "Ana"
    assert patient.phone == "11999999999"


def test_appointment_can_be_created() -> None:
    appointment = Appointment(patient_name="Ana", scheduled_at="2026-08-10 09:00", specialty="Cardiologia")

    assert appointment.patient_name == "Ana"
    assert appointment.scheduled_at == "2026-08-10 09:00"
