from __future__ import annotations

import re
from unicodedata import combining, normalize
from uuid import uuid4

from app.application.action.service import ActionEngine
from app.application.appointment.service import AppointmentService
from app.application.conversation.service import ConversationEngine
from app.application.decision.service import DecisionEngine
from app.application.persistence.service import PersistenceService
from app.application.safety.service import SafetyEngine
from app.application.understanding.service import MessageUnderstandingEngine
from app.domain.clinic.models import Clinic, Patient
from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus
from app.domain.conversation.state_machine import ConversationStateMachine


class ConversationOrchestrator:
    def __init__(self, persistence_service: PersistenceService | None = None) -> None:
        self.state_machine = ConversationStateMachine()
        self.conversation_engine = ConversationEngine()
        self.decision_engine = DecisionEngine()
        self.appointment_service = AppointmentService()
        self.persistence_service = persistence_service or PersistenceService()
        self.safety_engine = SafetyEngine()
        self.understanding_engine = MessageUnderstandingEngine()
        self.action_engine = ActionEngine()

    def handle_message(
        self,
        message: str,
        state: ConversationState | None,
        conversation_id: str | None = None,
    ) -> dict[str, object]:
        current_state = self._resolve_initial_state(state, conversation_id)

        if not message.strip():
            reply = self.conversation_engine.generate_reply(current_state, message)
            self.persistence_service.save_conversation_state(current_state)
            return {"state": current_state, "reply": reply}

        safety_decision = self.safety_engine.evaluate(message)
        if safety_decision.should_interrupt:
            next_state = self._build_safety_state(current_state, message, safety_decision.category, safety_decision.message)
            reply = self.conversation_engine.generate_reply(next_state, message)
            self.persistence_service.save_conversation_state(next_state)
            return {"state": next_state, "reply": reply}

        current_state = self._enrich_state_context(current_state, message)
        current_state = self._enrich_patient_context(current_state, message)
        decision = self.decision_engine.decide(current_state, message)

        next_state = self._apply_decision(current_state, message, decision)

        if next_state.current_step == ConversationStep.BOOK_APPOINTMENT and not next_state.context.get("appointment"):
            next_state = self._confirm_appointment(next_state)

        reply = self.conversation_engine.generate_reply(next_state, message)
        self.persistence_service.save_conversation_state(next_state)

        return {"state": next_state, "reply": reply}

    def _apply_decision(
        self,
        state: ConversationState,
        message: str,
        decision: dict[str, object],
    ) -> ConversationState:
        next_step = decision["next_step"]
        context = self.state_machine.append_message(state.context, message)

        if next_step == ConversationStep.EMERGENCY:
            return ConversationState(
                current_step=ConversationStep.EMERGENCY,
                status=ConversationStatus.EMERGENCY,
                context={**context, "last_message": message},
                conversation_id=state.conversation_id,
            )

        if next_step == ConversationStep.CHECK_CALENDAR:
            return ConversationState(
                current_step=ConversationStep.CHECK_CALENDAR,
                status=state.status,
                context={**context, "available_slots": self.state_machine.default_available_slots()},
                conversation_id=state.conversation_id,
            )

        if next_step == ConversationStep.BOOK_APPOINTMENT:
            pending_slot = context.get("pending_slot_confirmation")
            if pending_slot and self._is_affirmative(message):
                selected_slot = str(pending_slot)
                return ConversationState(
                    current_step=ConversationStep.BOOK_APPOINTMENT,
                    status=ConversationStatus.APPOINTMENT_BOOKED,
                    context=self._booking_context(context, selected_slot),
                    conversation_id=state.conversation_id,
                )

            if pending_slot and self._is_negative(message):
                clarification_options = context.get("slot_clarification_options") or context.get("available_slots", [])
                return ConversationState(
                    current_step=ConversationStep.CHECK_CALENDAR,
                    status=state.status,
                    context=self._calendar_context(
                        context,
                        available_slots=clarification_options,
                        slot_confirmation_declined=True,
                    ),
                    conversation_id=state.conversation_id,
                )

            selected_slot = self.state_machine.select_slot(message, context.get("available_slots", []))
            if selected_slot is None:
                candidates = self.state_machine.slot_candidates(message, context.get("available_slots", []))
                if len(candidates) > 1:
                    return ConversationState(
                        current_step=ConversationStep.CHECK_CALENDAR,
                        status=state.status,
                        context=self._calendar_context(
                            context,
                            available_slots=context.get("available_slots", []),
                            pending_slot_confirmation=candidates[0],
                            slot_clarification_options=candidates,
                            slot_confirmation_required=True,
                        ),
                        conversation_id=state.conversation_id,
                    )

                return ConversationState(
                    current_step=ConversationStep.CHECK_CALENDAR,
                    status=state.status,
                    context={**context, "calendar_selection_error": True},
                    conversation_id=state.conversation_id,
                )

            return ConversationState(
                current_step=ConversationStep.BOOK_APPOINTMENT,
                status=ConversationStatus.APPOINTMENT_BOOKED,
                context=self._booking_context(context, selected_slot),
                conversation_id=state.conversation_id,
            )

        if next_step == ConversationStep.COLLECT_INFORMATION:
            return ConversationState(
                current_step=ConversationStep.COLLECT_INFORMATION,
                status=state.status,
                context={**context, "appointment_intent": True},
                conversation_id=state.conversation_id,
            )

        if next_step == ConversationStep.CONFIRM_APPOINTMENT:
            return ConversationState(
                current_step=ConversationStep.CONFIRM_APPOINTMENT,
                status=state.status,
                context={**context, "reason": context.get("reason") or self._reason_from_context(context)},
                conversation_id=state.conversation_id,
            )

        if next_step == ConversationStep.DISCOVER_SYMPTOMS:
            return ConversationState(
                current_step=ConversationStep.DISCOVER_SYMPTOMS,
                status=state.status,
                context={**context, "reason": context.get("reason") or self._reason_from_context(context) or message},
                conversation_id=state.conversation_id,
            )

        if next_step == ConversationStep.FINISHED:
            return ConversationState(
                current_step=ConversationStep.FINISHED,
                status=state.status,
                context=context,
                conversation_id=state.conversation_id,
            )

        return ConversationState(
            current_step=state.current_step,
            status=state.status,
            context=context,
            conversation_id=state.conversation_id,
        )

    def _reason_from_context(self, context: dict[str, object]) -> str | None:
        summary = context.get("clinical_summary")
        if isinstance(summary, dict) and summary.get("main_complaint"):
            return str(summary["main_complaint"])

        symptoms = context.get("symptoms")
        if isinstance(symptoms, list) and symptoms:
            return str(symptoms[0])
        return None

    def _calendar_context(self, context: dict[str, object], **updates: object) -> dict[str, object]:
        next_context = {
            key: value
            for key, value in context.items()
            if key
            not in {
                "calendar_selection_error",
                "pending_slot_confirmation",
                "slot_clarification_options",
                "slot_confirmation_required",
                "slot_confirmation_declined",
            }
        }
        return {**next_context, **updates}

    def _booking_context(self, context: dict[str, object], selected_slot: str) -> dict[str, object]:
        return self._calendar_context(context, selected_slot=selected_slot)

    def _is_affirmative(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        return normalized in {"sim", "pode", "pode sim", "pode confirmar", "confirmar", "confirmo", "isso", "isso mesmo", "ok", "certo"}

    def _is_negative(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        return normalized in {"nao", "nao pode", "prefiro outro", "outro horario", "nao quero", "melhor nao"}

    def _normalize_text(self, message: str) -> str:
        without_accents = "".join(
            char for char in normalize("NFD", message.strip().lower()) if not combining(char)
        )
        return " ".join(without_accents.split())

    def _enrich_state_context(self, state: ConversationState, message: str) -> ConversationState:
        return ConversationState(
            current_step=state.current_step,
            status=state.status,
            context=self.understanding_engine.enrich_context(state.context, message),
            conversation_id=state.conversation_id,
        )

    def _enrich_patient_context(self, state: ConversationState, message: str) -> ConversationState:
        if state.current_step != ConversationStep.COLLECT_INFORMATION:
            return state

        patient = dict(state.context.get("patient", {})) if isinstance(state.context.get("patient"), dict) else {}
        name = self._extract_patient_name(message)
        phone = self._extract_phone(message)

        if name:
            patient["name"] = name
        if phone:
            patient["phone"] = phone

        missing = []
        if not patient.get("name"):
            missing.append("name")
        if not patient.get("phone"):
            missing.append("phone")

        return ConversationState(
            current_step=state.current_step,
            status=state.status,
            context={**state.context, "patient": patient, "missing_patient_fields": missing},
            conversation_id=state.conversation_id,
        )

    def _extract_patient_name(self, message: str) -> str | None:
        without_phone = re.sub(r"[\d\s()+-]{8,}", " ", message)
        without_phone = without_phone.split(",", 1)[0]
        without_phone = re.sub(r"\b(de manha|de tarde|de noite|manha|tarde|noite)\b", " ", without_phone, flags=re.IGNORECASE)
        words = [word for word in without_phone.strip().split() if any(char.isalpha() for char in word)]
        if len(words) < 2:
            return None
        return " ".join(words).strip(" ,.;")

    def _extract_phone(self, message: str) -> str | None:
        digits = "".join(char for char in message if char.isdigit())
        return digits if len(digits) >= 8 else None

    def reset_conversations(self) -> dict[str, object]:
        return self.persistence_service.reset_conversations()

    def _ensure_conversation_id(
        self,
        state: ConversationState,
        conversation_id: str | None,
    ) -> ConversationState:
        if state.conversation_id is not None:
            return state

        return ConversationState(
            current_step=state.current_step,
            status=state.status,
            context=state.context,
            conversation_id=conversation_id or str(uuid4()),
        )

    def _confirm_appointment(self, state: ConversationState) -> ConversationState:
        patient = Patient(name=self._patient_name_from_context(state), phone="")
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

    def _patient_name_from_context(self, state: ConversationState) -> str:
        patient = state.context.get("patient")
        if isinstance(patient, dict) and patient.get("name"):
            return str(patient["name"])

        details = str(state.context.get("patient_details", "")).strip()
        if not details:
            return "Paciente"

        first_part = details.split(",", 1)[0].strip()
        return first_part or "Paciente"

    def _resolve_initial_state(
        self,
        state: ConversationState | None,
        conversation_id: str | None,
    ) -> ConversationState:
        if state is not None:
            return self._ensure_conversation_id(state, conversation_id)

        stored_state = self.persistence_service.load_conversation_state(conversation_id)
        if stored_state is not None:
            return stored_state

        return self._ensure_conversation_id(self.state_machine.start(), conversation_id)

    def _build_safety_state(
        self,
        state: ConversationState,
        message: str,
        category: str,
        safety_message: str | None,
    ) -> ConversationState:
        if category == "emergency":
            return ConversationState(
                current_step=ConversationStep.EMERGENCY,
                status=ConversationStatus.EMERGENCY,
                context={
                    **state.context,
                    "last_message": message,
                    "safety_category": category,
                    "safety_message": safety_message,
                },
                conversation_id=state.conversation_id,
            )

        return ConversationState(
            current_step=state.current_step,
            status=state.status,
            context={
                **state.context,
                "last_message": message,
                "safety_category": category,
                "safety_message": safety_message,
            },
            conversation_id=state.conversation_id,
        )
