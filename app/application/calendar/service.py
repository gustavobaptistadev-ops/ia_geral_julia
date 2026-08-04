from __future__ import annotations


class CalendarService:
    def build_event(self, patient_name: str, scheduled_at: str, specialty: str) -> dict[str, str] | None:
        if not patient_name.strip():
            return None

        return {
            "summary": f"Consulta {specialty} - {patient_name}",
            "start": scheduled_at,
            "end": self._calculate_end_time(scheduled_at),
            "description": f"Consulta de {specialty} para {patient_name}",
        }

    def _calculate_end_time(self, scheduled_at: str) -> str:
        return scheduled_at.replace("09:00", "10:00") if "09:00" in scheduled_at else scheduled_at
