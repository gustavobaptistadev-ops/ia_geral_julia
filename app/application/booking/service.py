from __future__ import annotations

from app.application.action.service import ActionEngine
from app.application.appointment.service import AppointmentService
from app.application.persistence.service import PersistenceService
from app.domain.clinic.models import Clinic, Patient
from app.domain.conversation.context import ConversationContext
from app.domain.conversation.models import ConversationState


class AppointmentBookingAgent:
    def __init__(
        self,
        appointment_service: AppointmentService | None = None,
        action_engine: ActionEngine | None = None,
        persistence_service: PersistenceService | None = None,
    ) -> None:
        self.appointment_service = appointment_service or AppointmentService()
        self.action_engine = action_engine or ActionEngine()
        self.persistence_service = persistence_service or PersistenceService()

    def confirm_appointment(self, state: ConversationState) -> ConversationState:
        patient = Patient(name=self.patient_name_from_context(state), phone="")
        clinic = Clinic(name="Clinica", specialty="Geral")
        selected_slot = str(state.context.get("selected_slot", "2026-08-10 09:00"))
        appointment = self.appointment_service.create_appointment(patient, clinic, selected_slot)
        if appointment is None:
            return state

        action_result = self.action_engine.book_appointment(
            appointment.scheduled_at.split(" ", 1)[0],
            appointment.scheduled_at.split(" ", 1)[1],
            "Consulta agendada",
            patient_name=appointment.patient_name,
            specialty=appointment.specialty,
        )
        appointment_context = {
            "patient_name": appointment.patient_name,
            "scheduled_at": appointment.scheduled_at,
            "specialty": appointment.specialty,
            "calendar_event": action_result.get("calendar_event"),
            "clinic_name": clinic.name,
        }
        self.persistence_service.save_appointment(
            patient,
            clinic,
            appointment,
            conversation_id=state.conversation_id,
            context=appointment_context,
        )
        return ConversationState(
            current_step=state.current_step,
            status=state.status,
            context={**state.context, "appointment": appointment_context},
            conversation_id=state.conversation_id,
        )

    def patient_name_from_context(self, state: ConversationState) -> str:
        conversation_context = ConversationContext.from_dict(state.context)
        if conversation_context.patient.name:
            return conversation_context.patient.name

        details = (conversation_context.patient_details or "").strip()
        if not details:
            return "Paciente"

        first_part = details.split(",", 1)[0].strip()
        return first_part or "Paciente"
