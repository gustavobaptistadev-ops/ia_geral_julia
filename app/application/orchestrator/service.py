from __future__ import annotations

from unicodedata import combining, normalize
from uuid import uuid4

from app.application.administrative import AdministrativeAgent
from app.application.booking import AppointmentBookingAgent
from app.application.conversation.service import ConversationEngine
from app.application.decision.service import DecisionEngine
from app.application.patient import PatientAgent
from app.application.persistence.service import PersistenceService
from app.application.safety.service import SafetyEngine
from app.application.understanding.service import MessageUnderstandingEngine
from app.domain.conversation.context import ConversationContext
from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus
from app.domain.conversation.state_machine import ConversationStateMachine


class ConversationOrchestrator:
    def __init__(self, persistence_service: PersistenceService | None = None) -> None:
        self.state_machine = ConversationStateMachine()
        self.conversation_engine = ConversationEngine()
        self.decision_engine = DecisionEngine()
        self.persistence_service = persistence_service or PersistenceService()
        self.safety_engine = SafetyEngine()
        self.understanding_engine = MessageUnderstandingEngine()
        self.administrative_agent = AdministrativeAgent()
        self.patient_agent = PatientAgent()
        self.booking_agent = AppointmentBookingAgent(persistence_service=self.persistence_service)

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

        administrative_response = self.administrative_agent.handle(message)
        if administrative_response is not None:
            next_state = self._build_administrative_state(
                current_state,
                message,
                administrative_response.intent,
            )
            reply = {
                "message": administrative_response.message,
                "next_step": next_state.current_step,
                "should_handoff": False,
            }
            self.persistence_service.save_conversation_state(next_state)
            return {"state": next_state, "reply": reply}

        current_state = self._enrich_state_context(current_state, message)
        current_state = self._enrich_patient_context(current_state, message)
        decision = self.decision_engine.decide(current_state, message)

        next_state = self._apply_decision(current_state, message, decision)

        if next_state.current_step == ConversationStep.BOOK_APPOINTMENT and not next_state.context.get("appointment"):
            next_state = self.booking_agent.confirm_appointment(next_state)

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
        conversation_context = ConversationContext.from_dict(context)
        return conversation_context.clinical.main_complaint or next(iter(conversation_context.symptoms), None)

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
        affirmative_phrases = {
            "sim",
            "pode",
            "pode sim",
            "pode ser",
            "pode ser esse",
            "pode ser este",
            "pode ser essa",
            "pode ser esta",
            "pode ser isso",
            "pode ser esse mesmo",
            "pode ser este mesmo",
            "pode ser essa mesmo",
            "pode ser esta mesmo",
            "pode confirmar",
            "confirmar",
            "confirmo",
            "esse mesmo",
            "este mesmo",
            "essa mesmo",
            "esta mesmo",
            "isso",
            "isso mesmo",
            "ok",
            "certo",
        }
        if normalized in affirmative_phrases:
            return True

        return any(
            phrase in normalized
            for phrase in [
                "pode ser esse",
                "pode ser este",
                "esse mesmo",
                "este mesmo",
                "isso mesmo",
                "pode confirmar",
            ]
        )

    def _is_negative(self, message: str) -> bool:
        normalized = self._normalize_text(message)
        return normalized in {"nao", "nao pode", "prefiro outro", "outro horario", "nao quero", "melhor nao"}

    def _normalize_text(self, message: str) -> str:
        without_accents = "".join(
            char for char in normalize("NFD", message.strip().lower()) if not combining(char)
        )
        return " ".join(without_accents.split())

    def _build_administrative_state(self, state: ConversationState, message: str, intent: str) -> ConversationState:
        context = self.state_machine.append_message(state.context, message)
        return ConversationState(
            current_step=state.current_step,
            status=state.status,
            context={**context, "last_administrative_intent": intent},
            conversation_id=state.conversation_id,
        )

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

        return ConversationState(
            current_step=state.current_step,
            status=state.status,
            context=self.patient_agent.enrich_context(state.context, message),
            conversation_id=state.conversation_id,
        )

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
