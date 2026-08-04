from app.application.orchestrator.service import ConversationOrchestrator
from app.application.persistence.service import PersistenceService
from app.domain.conversation.state_machine import ConversationStateMachine


class FakePersistenceRepository:
    def __init__(self) -> None:
        self.conversations: list[dict[str, object]] = []
        self.appointments: list[dict[str, object]] = []
        self.stored_conversations: dict[str, dict[str, object]] = {}

    def create_conversation(
        self,
        conversation_id: str,
        context: dict[str, object],
        status: str = "active",
        current_step: str = "greeting",
    ) -> None:
        self.conversations.append(
            {
                "conversation_id": conversation_id,
                "context": context,
                "status": status,
                "current_step": current_step,
            }
        )
        self.stored_conversations[conversation_id] = self.conversations[-1]

    def update_context(
        self,
        conversation_id: str,
        context: dict[str, object],
        status: str | None = None,
        current_step: str | None = None,
    ) -> None:
        self.conversations.append(
            {
                "conversation_id": conversation_id,
                "context": context,
                "status": status,
                "current_step": current_step,
            }
        )
        self.stored_conversations[conversation_id] = self.conversations[-1]

    def get_conversation(self, conversation_id: str) -> dict[str, object] | None:
        return self.stored_conversations.get(conversation_id)

    def create_appointment(
        self,
        conversation_id: str | None,
        patient_name: str,
        patient_phone: str,
        clinic_name: str,
        specialty: str,
        scheduled_at: str,
        context: dict[str, object],
    ) -> None:
        self.appointments.append(
            {
                "conversation_id": conversation_id,
                "patient_name": patient_name,
                "patient_phone": patient_phone,
                "clinic_name": clinic_name,
                "specialty": specialty,
                "scheduled_at": scheduled_at,
                "context": context,
            }
        )


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


def test_orchestrator_interrupts_puncture_injury() -> None:
    orchestrator = ConversationOrchestrator()
    result = orchestrator.handle_message("tenho um prego no pe", None)

    assert result["reply"]["next_step"] == "emergency"
    assert result["reply"]["should_handoff"] is True
    assert "lesao perfurante" in result["reply"]["message"]


def test_orchestrator_detects_appointment_intent() -> None:
    orchestrator = ConversationOrchestrator()
    result = orchestrator.handle_message("Quero agendar uma consulta", None)

    assert result["reply"]["next_step"] == "discover_symptoms"
    assert result["reply"]["message"] == "Certo, me conta qual sintoma ou motivo principal da consulta."


def test_orchestrator_does_not_book_before_slot_confirmation() -> None:
    orchestrator = ConversationOrchestrator()
    result = orchestrator.handle_message("Quero agendar uma consulta", None)

    appointment_context = result["state"].context.get("appointment", {})

    assert appointment_context == {}
    assert result["reply"]["next_step"] == "discover_symptoms"


def test_orchestrator_persists_conversation_and_appointment_with_conversation_id() -> None:
    repository = FakePersistenceRepository()
    orchestrator = ConversationOrchestrator(PersistenceService(repository))

    first = orchestrator.handle_message("coceira nos dedos", None, conversation_id="conv-1")
    second = orchestrator.handle_message("tem 3 dias e esta incomodando muito", first["state"], conversation_id="conv-1")
    third = orchestrator.handle_message("quero marcar consulta", second["state"], conversation_id="conv-1")
    fourth = orchestrator.handle_message("Ana Silva, 11999999999, de manha", third["state"], conversation_id="conv-1")
    result = orchestrator.handle_message("prefiro segunda de manha", fourth["state"], conversation_id="conv-1")

    assert result["state"].conversation_id == "conv-1"
    assert first["state"].context["symptoms"] == ["coceira nos dedos"]
    assert repository.appointments[0]["conversation_id"] == "conv-1"
    assert repository.appointments[0]["patient_name"] == "Ana Silva"
    assert repository.appointments[0]["scheduled_at"] == "2026-08-10 09:00"


def test_orchestrator_restores_persisted_conversation_state() -> None:
    repository = FakePersistenceRepository()
    repository.stored_conversations["conv-1"] = {
        "conversation_id": "conv-1",
        "current_step": "discover_symptoms",
        "status": "active",
        "context": {"reason": "coceira nos dedos", "symptoms": ["coceira nos dedos"]},
    }
    orchestrator = ConversationOrchestrator(PersistenceService(repository))

    result = orchestrator.handle_message("Sinto dor nas costas", None, conversation_id="conv-1")

    assert result["state"].conversation_id == "conv-1"
    assert result["state"].context["reason"] == "coceira nos dedos"
    assert result["state"].context["last_message"] == "Sinto dor nas costas"


def test_orchestrator_uses_context_before_suggesting_appointment() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("coceira nos dedos", None, conversation_id="conv-1")
    second = orchestrator.handle_message("tem 3 dias e esta incomodando muito", first["state"], conversation_id="conv-1")

    assert second["state"].context["symptoms"] == ["coceira nos dedos", "tem 3 dias e esta incomodando muito"]
    assert second["reply"]["next_step"] == "confirm_appointment"
    assert second["reply"]["message"] == (
        "Pelo o que foi relatado, faz sentido organizar um atendimento para avaliar isso com seguranca. "
        "Vamos agendar sua consulta?"
    )


def test_orchestrator_uses_rich_single_message_context_before_suggesting_appointment() -> None:
    orchestrator = ConversationOrchestrator()

    result = orchestrator.handle_message(
        "estou com coceira nos dedos tem 3 dias esta incomodando muito",
        None,
        conversation_id="conv-1",
    )

    summary = result["state"].context["clinical_summary"]

    assert result["reply"]["next_step"] == "confirm_appointment"
    assert "Vamos agendar sua consulta?" in result["reply"]["message"]
    assert "contexto" not in result["reply"]["message"].lower()
    assert summary["duration"] == "3 dias"
    assert summary["appointment_readiness"] == "enough_context"


def test_orchestrator_uses_mixed_hair_loss_message_before_asking_next_missing_detail() -> None:
    orchestrator = ConversationOrchestrator()

    result = orchestrator.handle_message(
        "estou com cabelo caindo a alguns dias quero marcar uma consulta",
        None,
        conversation_id="conv-1",
    )

    summary = result["state"].context["clinical_summary"]

    assert result["reply"]["next_step"] == "discover_symptoms"
    assert result["reply"]["message"] == "Entendi, isso esta leve, incomodando bastante ou piorando?"
    assert summary["main_complaint"] == "cabelo caindo"
    assert summary["duration"] == "alguns dias"
    assert summary["patient_goal"] == "schedule_appointment"


def test_orchestrator_uses_bare_vague_duration_before_asking_next_missing_detail() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("estou com cabelo caindo", None, conversation_id="conv-1")
    result = orchestrator.handle_message("alguns dias", first["state"], conversation_id="conv-1")

    summary = result["state"].context["clinical_summary"]

    assert result["reply"]["next_step"] == "discover_symptoms"
    assert result["reply"]["message"] == "Certo, isso esta leve, incomodando bastante ou piorando?"
    assert summary["main_complaint"] == "cabelo caindo"
    assert summary["duration"] == "alguns dias"


def test_orchestrator_understands_skin_blisters_as_clinical_context() -> None:
    orchestrator = ConversationOrchestrator()

    result = orchestrator.handle_message(
        "estou com bolhas vermelhas nas costas",
        None,
        conversation_id="conv-1",
    )

    assert result["reply"]["next_step"] == "discover_symptoms"
    assert result["reply"]["message"] == "Entendi, ha quanto tempo isto esta ocorrendo?"
    assert result["state"].context["clinical_summary"]["main_complaint"] == "bolhas vermelhas nas costas"


def test_orchestrator_collects_data_and_offers_calendar_slots() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("coceira nos dedos", None, conversation_id="conv-1")
    second = orchestrator.handle_message("tem 3 dias e esta incomodando muito", first["state"], conversation_id="conv-1")
    third = orchestrator.handle_message("quero marcar consulta", second["state"], conversation_id="conv-1")
    fourth = orchestrator.handle_message("Ana Silva, 11999999999, de manha", third["state"], conversation_id="conv-1")

    assert third["reply"]["next_step"] == "collect_information"
    assert "Nome completo" in third["reply"]["message"]
    assert "WhatsApp/Telefone" in third["reply"]["message"]
    assert fourth["reply"]["next_step"] == "check_calendar"
    assert "Escolha" not in fourth["reply"]["message"]
    assert "1." not in fourth["reply"]["message"]
    assert "Tenho vaga segunda-feira as 9h" in fourth["reply"]["message"]
    assert "segunda-feira as 14h" in fourth["reply"]["message"]
    assert "terca-feira as 10h" in fourth["reply"]["message"]


def test_orchestrator_confirms_name_and_requests_only_missing_phone() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("coceira nos dedos", None, conversation_id="conv-1")
    second = orchestrator.handle_message("tem 3 dias e esta incomodando muito", first["state"], conversation_id="conv-1")
    third = orchestrator.handle_message("sim", second["state"], conversation_id="conv-1")
    result = orchestrator.handle_message("gustavo henrique baptista santana", third["state"], conversation_id="conv-1")

    assert result["reply"]["next_step"] == "collect_information"
    assert result["state"].context["patient"]["name"] == "gustavo henrique baptista santana"
    assert result["state"].context["missing_patient_fields"] == ["phone"]
    assert result["reply"]["message"] == (
        "Perfeito, gustavo henrique baptista santana. Agora falta so o WhatsApp/Telefone para eu seguir com o agendamento."
    )


def test_orchestrator_confirms_after_slot_choice() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("coceira nos dedos", None, conversation_id="conv-1")
    second = orchestrator.handle_message("tem 3 dias e esta incomodando muito", first["state"], conversation_id="conv-1")
    third = orchestrator.handle_message("quero marcar consulta", second["state"], conversation_id="conv-1")
    fourth = orchestrator.handle_message("Ana Silva, 11999999999, de manha", third["state"], conversation_id="conv-1")
    result = orchestrator.handle_message("pode ser de tarde", fourth["state"], conversation_id="conv-1")

    assert result["reply"]["next_step"] == "book_appointment"
    assert result["state"].context["appointment"]["scheduled_at"] == "2026-08-10 14:00"
    assert "Av. Paulista" in result["reply"]["message"]


def test_orchestrator_asks_confirmation_when_weekday_has_multiple_slots() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("coceira tem 3 dias e incomoda muito", None, conversation_id="conv-1")
    second = orchestrator.handle_message("sim", first["state"], conversation_id="conv-1")
    third = orchestrator.handle_message("Ana Silva 11999999999", second["state"], conversation_id="conv-1")
    result = orchestrator.handle_message("segunda", third["state"], conversation_id="conv-1")

    assert result["reply"]["next_step"] == "check_calendar"
    assert result["state"].context["pending_slot_confirmation"] == "2026-08-10 09:00"
    assert "Tenho mais de um horario nesse dia" in result["reply"]["message"]
    assert "segunda-feira, 10/08/2026 as 9h" in result["reply"]["message"]


def test_orchestrator_books_pending_slot_after_affirmative_confirmation() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("coceira tem 3 dias e incomoda muito", None, conversation_id="conv-1")
    second = orchestrator.handle_message("sim", first["state"], conversation_id="conv-1")
    third = orchestrator.handle_message("Ana Silva 11999999999", second["state"], conversation_id="conv-1")
    fourth = orchestrator.handle_message("segunda", third["state"], conversation_id="conv-1")
    result = orchestrator.handle_message("sim", fourth["state"], conversation_id="conv-1")

    assert result["reply"]["next_step"] == "book_appointment"
    assert result["state"].context["appointment"]["scheduled_at"] == "2026-08-10 09:00"
    assert "Horario: segunda-feira, 10/08/2026 as 9h" in result["reply"]["message"]


def test_orchestrator_reoffers_day_slots_after_negative_confirmation() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("coceira tem 3 dias e incomoda muito", None, conversation_id="conv-1")
    second = orchestrator.handle_message("sim", first["state"], conversation_id="conv-1")
    third = orchestrator.handle_message("Ana Silva 11999999999", second["state"], conversation_id="conv-1")
    fourth = orchestrator.handle_message("segunda", third["state"], conversation_id="conv-1")
    result = orchestrator.handle_message("nao", fourth["state"], conversation_id="conv-1")

    assert result["reply"]["next_step"] == "check_calendar"
    assert "Sem problema" in result["reply"]["message"]
    assert "segunda-feira as 9h" in result["reply"]["message"]
    assert "segunda-feira as 14h" in result["reply"]["message"]
    assert "terca-feira" not in result["reply"]["message"]


def test_orchestrator_keeps_appointment_finished_after_patient_acknowledges() -> None:
    orchestrator = ConversationOrchestrator()

    first = orchestrator.handle_message("coceira nos dedos", None, conversation_id="conv-1")
    second = orchestrator.handle_message("tem 3 dias e esta incomodando muito", first["state"], conversation_id="conv-1")
    third = orchestrator.handle_message("sim", second["state"], conversation_id="conv-1")
    fourth = orchestrator.handle_message("gustavo henrique baptista santana 61991773474", third["state"], conversation_id="conv-1")
    fifth = orchestrator.handle_message("prefiro segunda de tarde", fourth["state"], conversation_id="conv-1")
    result = orchestrator.handle_message("ok", fifth["state"], conversation_id="conv-1")

    assert result["reply"]["next_step"] == "finished"
    assert result["reply"]["message"] == "Perfeito. Sua consulta ja esta confirmada. Qualquer ajuste, estou por aqui para te ajudar."


def test_orchestrator_interrupts_unsafe_medical_advice_request() -> None:
    repository = FakePersistenceRepository()
    orchestrator = ConversationOrchestrator(PersistenceService(repository))

    result = orchestrator.handle_message("Qual remedio posso tomar?", None, conversation_id="conv-1")

    assert result["state"].context["safety_category"] == "unsafe_prescription_or_diagnosis"
    assert result["reply"]["should_handoff"] is True
    assert repository.appointments == []
