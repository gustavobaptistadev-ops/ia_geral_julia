from app.domain.conversation.context import ConversationContext


def test_conversation_context_loads_existing_dict_shape() -> None:
    context = ConversationContext.from_dict(
        {
            "messages": [{"role": "patient", "content": "alergia"}],
            "symptoms": ["alergia"],
            "clinical_summary": {
                "main_complaint": "alergia",
                "duration": "2 meses",
                "duration_risk": "long_duration",
                "appointment_readiness": "enough_context",
            },
            "patient": {"name": "Ana Silva", "phone": "11999999999"},
            "available_slots": ["2026-08-10 09:00"],
            "pending_slot_confirmation": "2026-08-10 09:00",
            "last_administrative_intent": "exam_referral",
        }
    )

    assert context.messages == [{"role": "patient", "content": "alergia"}]
    assert context.symptoms == ["alergia"]
    assert context.clinical.main_complaint == "alergia"
    assert context.clinical.duration_risk == "long_duration"
    assert context.clinical.is_ready_for_appointment() is True
    assert context.patient.name == "Ana Silva"
    assert context.patient_is_complete() is True
    assert context.calendar.available_slots == ["2026-08-10 09:00"]
    assert context.calendar.pending_slot_confirmation == "2026-08-10 09:00"
    assert context.last_administrative_intent == "exam_referral"


def test_conversation_context_exports_legacy_dict_shape() -> None:
    context = ConversationContext.from_dict(
        {
            "clinical_summary": {"main_complaint": "coceira", "appointment_readiness": "needs_more_context"},
            "patient": {"name": "Gustavo Henrique"},
            "available_slots": ["2026-08-10 14:00"],
            "calendar_selection_error": True,
        }
    )

    exported = context.to_dict()

    assert exported["clinical_summary"]["main_complaint"] == "coceira"
    assert exported["patient"] == {"name": "Gustavo Henrique"}
    assert exported["available_slots"] == ["2026-08-10 14:00"]
    assert exported["calendar_selection_error"] is True
    assert "selected_slot" not in exported
