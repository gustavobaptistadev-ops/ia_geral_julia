from app.application.understanding.service import MessageUnderstandingEngine


def test_understanding_extracts_complaint_duration_and_severity() -> None:
    context = MessageUnderstandingEngine().enrich_context(
        {},
        "estou com coceira nos dedos tem 3 dias esta incomodando muito",
    )

    summary = context["clinical_summary"]

    assert summary["main_complaint"] == "coceira nos dedos"
    assert summary["body_location"] == "dedos"
    assert summary["duration"] == "3 dias"
    assert summary["severity"] == "incomoda muito"
    assert summary["appointment_readiness"] == "enough_context"


def test_understanding_preserves_existing_summary_and_fills_missing_fields() -> None:
    context = {
        "clinical_summary": {
            "main_complaint": "coceira nos dedos",
            "duration": None,
            "severity": None,
            "progression": None,
        }
    }

    updated = MessageUnderstandingEngine().enrich_context(context, "tem 3 dias e foi piorando")

    summary = updated["clinical_summary"]

    assert summary["main_complaint"] == "coceira nos dedos"
    assert summary["duration"] == "3 dias"
    assert summary["progression"] == "piorando"
    assert summary["appointment_readiness"] == "enough_context"


def test_understanding_builds_context_memory_from_mixed_appointment_and_allergy_message() -> None:
    context = MessageUnderstandingEngine().enrich_context(
        {},
        "quero agendar com alergista, estou 2 meses com alergia",
    )

    summary = context["clinical_summary"]
    memory = context["context_memory"]

    assert summary["patient_goal"] == "schedule_appointment"
    assert summary["requested_specialty"] == "alergista"
    assert summary["main_complaint"] == "alergia"
    assert summary["duration"] == "2 meses"
    assert summary["duration_risk"] == "long_duration"
    assert summary["missing_fields"] == []
    assert summary["appointment_readiness"] == "enough_context"
    assert memory["facts"] == ["quero agendar com alergista, estou 2 meses com alergia"]


def test_understanding_treats_months_of_symptom_as_enough_context() -> None:
    context = {
        "clinical_summary": {
            "main_complaint": "alergia",
            "duration": None,
            "severity": None,
            "progression": None,
        }
    }

    updated = MessageUnderstandingEngine().enrich_context(context, "uns 2 meses")

    summary = updated["clinical_summary"]

    assert summary["main_complaint"] == "alergia"
    assert summary["duration"] == "2 meses"
    assert summary["duration_risk"] == "long_duration"
    assert summary["missing_fields"] == []
    assert summary["appointment_readiness"] == "enough_context"


def test_understanding_extracts_hair_loss_duration_and_appointment_intent() -> None:
    context = MessageUnderstandingEngine().enrich_context(
        {},
        "estou com cabelo caindo a alguns dias quero marcar uma consulta",
    )

    summary = context["clinical_summary"]

    assert summary["patient_goal"] == "schedule_appointment"
    assert summary["main_complaint"] == "cabelo caindo"
    assert summary["duration"] == "alguns dias"
    assert summary["missing_fields"] == ["severity_or_progression"]


def test_understanding_uses_bare_vague_duration_with_existing_complaint() -> None:
    context = {
        "clinical_summary": {
            "main_complaint": "cabelo caindo",
            "duration": None,
            "severity": None,
            "progression": None,
        }
    }

    updated = MessageUnderstandingEngine().enrich_context(context, "alguns dias")

    summary = updated["clinical_summary"]

    assert summary["main_complaint"] == "cabelo caindo"
    assert summary["duration"] == "alguns dias"
    assert summary["missing_fields"] == ["severity_or_progression"]


def test_understanding_removes_greeting_before_complaint() -> None:
    context = MessageUnderstandingEngine().enrich_context(
        {},
        "oi estou sentindo cabelo caindo",
    )

    summary = context["clinical_summary"]

    assert summary["main_complaint"] == "cabelo caindo"
