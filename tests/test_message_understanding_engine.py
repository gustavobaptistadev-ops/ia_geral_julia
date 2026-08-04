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
