from app.application.orchestrator.service import ConversationOrchestrator
from app.domain.conversation.state_machine import ConversationStateMachine


def test_orchestrator_starts_with_greeting() -> None:
    orchestrator = ConversationOrchestrator()
    result = orchestrator.handle_message("", None)

    assert result["reply"]["next_step"] == "greeting"
    assert result["state"].current_step == "greeting"


def test_orchestrator_detects_emergency() -> None:
    orchestrator = ConversationOrchestrator()
    result = orchestrator.handle_message("Estou com falta de ar grave", None)

    assert result["reply"]["next_step"] == "emergency"
    assert result["state"].status == "emergency"


def test_orchestrator_detects_appointment_intent() -> None:
    orchestrator = ConversationOrchestrator()
    result = orchestrator.handle_message("Quero agendar uma consulta", None)

    assert result["reply"]["next_step"] == "discover_symptoms"
    assert result["reply"]["message"].startswith("Entendi")


def test_orchestrator_attaches_calendar_event_to_appointment_context() -> None:
    orchestrator = ConversationOrchestrator()
    result = orchestrator.handle_message("Quero agendar uma consulta", None)

    appointment_context = result["state"].context.get("appointment", {})

    assert appointment_context["calendar_event"]["summary"] == "Consulta Geral - Paciente"
    assert appointment_context["calendar_event"]["start"] == "2026-08-10 09:00"
