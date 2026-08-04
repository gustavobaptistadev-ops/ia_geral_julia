from app.application.safety.service import SafetyEngine


def test_safety_engine_allows_safe_message() -> None:
    decision = SafetyEngine().evaluate("Ola")

    assert decision.category == "safe"
    assert decision.should_interrupt is False


def test_safety_engine_detects_emergency() -> None:
    decision = SafetyEngine().evaluate("Estou com dor intensa no peito")

    assert decision.category == "emergency"
    assert decision.should_interrupt is True
    assert decision.message is not None
    assert "emergencia" in decision.message


def test_safety_engine_blocks_diagnosis_or_prescription_request() -> None:
    decision = SafetyEngine().evaluate("Qual remedio posso tomar e qual dosagem?")

    assert decision.category == "unsafe_prescription_or_diagnosis"
    assert decision.should_interrupt is True
    assert decision.message is not None
    assert "nao posso diagnosticar" in decision.message.lower()


def test_safety_engine_detects_mental_health_risk() -> None:
    decision = SafetyEngine().evaluate("Eu quero morrer e nao aguento mais viver")

    assert decision.category == "mental_health_risk"
    assert decision.should_interrupt is True
    assert decision.message is not None
    assert "CVV" in decision.message


def test_safety_engine_classifies_safe_clinical_context() -> None:
    decision = SafetyEngine().evaluate("Quero agendar consulta por dor nas costas")

    assert decision.category == "safe_clinical_context"
    assert decision.should_interrupt is False


def test_safety_engine_classifies_administrative_context() -> None:
    decision = SafetyEngine().evaluate("Qual o endereco e o valor da consulta?")

    assert decision.category == "administrative"
    assert decision.should_interrupt is False
