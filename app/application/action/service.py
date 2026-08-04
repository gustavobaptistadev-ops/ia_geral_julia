from __future__ import annotations

from app.application.calendar.service import CalendarService


class ActionEngine:
    def __init__(self) -> None:
        self.calendar_service = CalendarService()

    def book_appointment(
        self,
        date: str,
        time: str,
        reason: str,
        patient_name: str | None = None,
        specialty: str | None = None,
    ) -> dict[str, object]:
        if not date or not time or not reason:
            return {"scheduled": False, "reason": "Dados incompletos"}

        slot = f"{date} {time}"
        payload: dict[str, object] = {
            "scheduled": True,
            "slot": slot,
            "reason": reason,
            "provider": "local-action-engine",
        }

        if patient_name and specialty:
            payload["calendar_event"] = self.calendar_service.build_event(patient_name, slot, specialty)

        return payload
