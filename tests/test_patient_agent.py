from app.application.patient import PatientAgent


def test_patient_agent_extracts_name_and_phone() -> None:
    agent = PatientAgent()

    context = agent.enrich_context({}, "Ana Silva, 11999999999, de manha")

    assert context["patient"] == {"name": "Ana Silva", "phone": "11999999999"}
    assert context["missing_patient_fields"] == []


def test_patient_agent_keeps_name_and_requests_missing_phone() -> None:
    agent = PatientAgent()

    context = agent.enrich_context(
        {"patient": {"name": "gustavo henrique baptista santana"}},
        "de tarde",
    )

    assert context["patient"] == {"name": "gustavo henrique baptista santana"}
    assert context["missing_patient_fields"] == ["phone"]


def test_patient_agent_adds_phone_to_existing_name() -> None:
    agent = PatientAgent()

    context = agent.enrich_context(
        {"patient": {"name": "Gustavo Henrique"}, "missing_patient_fields": ["phone"]},
        "61991773474",
    )

    assert context["patient"] == {"name": "Gustavo Henrique", "phone": "61991773474"}
    assert context["missing_patient_fields"] == []
