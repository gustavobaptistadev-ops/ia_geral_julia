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
