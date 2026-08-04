from app.application.calendar.service import CalendarService


def test_calendar_service_builds_event_payload() -> None:
    service = CalendarService()
    payload = service.build_event("Ana", "2026-08-10 09:00", "Cardiologia")

    assert payload["summary"] == "Consulta Cardiologia - Ana"
    assert payload["start"] == "2026-08-10 09:00"
    assert payload["end"] == "2026-08-10 10:00"


def test_calendar_service_rejects_missing_name() -> None:
    service = CalendarService()
    payload = service.build_event("", "2026-08-10 09:00", "Cardiologia")

    assert payload is None
