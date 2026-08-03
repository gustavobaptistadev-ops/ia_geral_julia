from __future__ import annotations

from app.domain.clinic.models import Appointment, Clinic, Patient


class AppointmentService:
    def create_appointment(self, patient: Patient, clinic: Clinic, scheduled_at: str) -> Appointment | None:
        if not patient.name.strip():
            return None

        return Appointment(
            patient_name=patient.name,
            scheduled_at=scheduled_at,
            specialty=clinic.specialty,
        )
