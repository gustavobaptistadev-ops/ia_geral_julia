from __future__ import annotations

from app.application.appointment.service import AppointmentService
from app.application.conversation.service import ConversationEngine
from app.application.decision.service import DecisionEngine
from app.domain.clinic.models import Clinic, Patient
from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus
from app.domain.conversation.state_machine import ConversationStateMachine


class ConversationOrchestrator:
    def __init__(self) -> None:
        self.state_machine = ConversationStateMachine()
        self.conversation_engine = ConversationEngine()
        self.decision_engine = DecisionEngine()
        self.appointment_service = AppointmentService()

    def handle_message(self, message: str, state: ConversationState | None) -> dict[str, object]:
        current_state = state or self.state_machine.start()

        if not message.strip():
            next_state = current_state
            reply = self.conversation_engine.generate_reply(next_state, message)
            return {"state": next_state, "reply": reply}

        if self.decision_engine._is_appointment_intent(message.lower()):
            patient = Patient(name="Paciente", phone="")
            clinic = Clinic(name="Clínica", specialty="Geral")
            appointment = self.appointment_service.create_appointment(patient, clinic, "2026-08-10 09:00")
            if appointment is not None:
                current_state.context["appointment"] = {
                    "patient_name": appointment.patient_name,
                    "scheduled_at": appointment.scheduled_at,
                    "specialty": appointment.specialty,
                }

        decision = self.decision_engine.decide(current_state, message)

        if decision["next_step"] == ConversationStep.EMERGENCY:
            next_state = ConversationState(
                current_step=ConversationStep.EMERGENCY,
                status=ConversationStatus.EMERGENCY,
                context={**current_state.context, "last_message": message},
                conversation_id=current_state.conversation_id,
            )
        else:
            next_state = self.state_machine.process_message(current_state, message)

        reply = self.conversation_engine.generate_reply(next_state, message)

        return {"state": next_state, "reply": reply}
