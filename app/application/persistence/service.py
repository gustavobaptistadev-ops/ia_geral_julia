from __future__ import annotations

from app.domain.clinic.models import Appointment, Clinic, Patient


class PersistenceService:
    def save_appointment(self, patient: Patient, clinic: Clinic, appointment: Appointment) -> dict[str, str] | None:
        if not patient.name.strip() or not appointment.patient_name.strip():
            return None

        return {
            "patient_name": appointment.patient_name,
            "specialty": appointment.specialty,
            "scheduled_at": appointment.scheduled_at,
            "clinic_name": clinic.name,
        }
