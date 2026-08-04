from app.application.administrative import AdministrativeAgent


def test_administrative_agent_refers_exam_request_to_partner_laboratory() -> None:
    response = AdministrativeAgent().handle("preciso fazer exame")

    assert response is not None
    assert response.intent == "exam_referral"
    assert "Laboratorio Life" in response.message
    assert "61999999999" in response.message
    assert "Connect Tower" in response.message


def test_administrative_agent_ignores_clinical_message() -> None:
    response = AdministrativeAgent().handle("estou com alergia")

    assert response is None
