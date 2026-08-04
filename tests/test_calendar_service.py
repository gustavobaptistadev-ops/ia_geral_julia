from app.application.calendar.service import CalendarService, GoogleCalendarService


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


def test_google_calendar_service_builds_google_payload() -> None:
    service = GoogleCalendarService()
    payload = service.build_google_event("Ana", "2026-08-10 09:00", "Cardiologia")

    assert payload["summary"] == "Consulta Cardiologia - Ana"
    assert payload["start"]["dateTime"] == "2026-08-10T09:00:00"
    assert payload["end"]["dateTime"] == "2026-08-10T10:00:00"


def test_google_calendar_service_creates_event_via_http_client() -> None:
    class DummyResponse:
        def __init__(self) -> None:
            self._body = b'{"id": "event-123"}'

        def read(self) -> bytes:
            return self._body

    captured: dict[str, object] = {}

    def fake_client(request: object) -> DummyResponse:
        captured["url"] = request.full_url
        captured["method"] = request.method
        captured["body"] = request.data.decode("utf-8")
        return DummyResponse()

    service = GoogleCalendarService(http_client=fake_client)
    payload = service.create_event({"summary": "Consulta"}, api_key="abc123")

    assert payload["id"] == "event-123"
    assert captured["url"].startswith("https://www.googleapis.com/calendar/v3/calendars/primary/events?key=abc123")
    assert captured["method"] == "POST"
    assert "Consulta" in str(captured["body"])
