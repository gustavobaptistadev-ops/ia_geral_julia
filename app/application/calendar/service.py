from __future__ import annotations

import json
from typing import Any, Callable
from urllib import request


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


class GoogleCalendarService:
    def __init__(self, http_client: Callable[[Any], Any] | None = None) -> None:
        self.http_client = http_client or self._default_http_client

    def build_google_event(self, patient_name: str, scheduled_at: str, specialty: str) -> dict[str, Any] | None:
        if not patient_name.strip():
            return None

        start_time = self._to_google_datetime(scheduled_at)
        end_time = self._to_google_datetime(self._calculate_end_time(scheduled_at))

        return {
            "summary": f"Consulta {specialty} - {patient_name}",
            "description": f"Consulta de {specialty} para {patient_name}",
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }

    def create_event(self, payload: dict[str, Any], api_key: str) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events?key={api_key}"
        req = request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
        response = self.http_client(req)
        return json.loads(response.read().decode("utf-8"))

    def _default_http_client(self, request_obj: Any) -> Any:
        return request.urlopen(request_obj)

    def _to_google_datetime(self, scheduled_at: str) -> str:
        if " " in scheduled_at:
            date_part, time_part = scheduled_at.split(" ", 1)
            return f"{date_part}T{time_part}:00"
        return f"{scheduled_at}T00:00:00"

    def _calculate_end_time(self, scheduled_at: str) -> str:
        if "09:00" in scheduled_at:
            return scheduled_at.replace("09:00", "10:00")
        return scheduled_at
