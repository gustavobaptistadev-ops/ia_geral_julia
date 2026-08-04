from app.application.action.service import ActionEngine


def test_action_engine_creates_appointment_payload() -> None:
    engine = ActionEngine()

    result = engine.book_appointment("2026-08-10", "09:00", "Consulta inicial")

    assert result["scheduled"] is True
    assert result["slot"] == "2026-08-10 09:00"
    assert result["reason"] == "Consulta inicial"


def test_action_engine_returns_false_for_missing_inputs() -> None:
    engine = ActionEngine()

    result = engine.book_appointment("", "", "")

    assert result["scheduled"] is False
    assert result["reason"] == "Dados incompletos"


def test_action_engine_builds_calendar_event_payload() -> None:
    engine = ActionEngine()

    result = engine.book_appointment("2026-08-10", "09:00", "Consulta inicial", patient_name="Ana", specialty="Cardiologia")

    assert result["scheduled"] is True
    assert result["calendar_event"]["summary"] == "Consulta Cardiologia - Ana"
    assert result["calendar_event"]["start"] == "2026-08-10 09:00"
    assert result["calendar_event"]["end"] == "2026-08-10 10:00"
