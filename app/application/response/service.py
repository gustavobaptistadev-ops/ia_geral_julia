from __future__ import annotations

from app.application.voice import VoiceAgent
from app.domain.conversation.models import ConversationState, ConversationStep, ConversationStatus


class ResponseAgent:
    def __init__(self, voice_agent: VoiceAgent | None = None) -> None:
        self.voice_agent = voice_agent or VoiceAgent()

    def generate_reply(self, state: ConversationState, message: str) -> dict[str, object]:
        if state.status == ConversationStatus.EMERGENCY:
            return {
                "message": state.context.get(
                    "safety_message",
                    self.voice_agent.emergency_fallback(),
                ),
                "next_step": ConversationStep.EMERGENCY,
                "should_handoff": True,
            }

        if state.context.get("safety_message"):
            return {
                "message": state.context["safety_message"],
                "next_step": state.current_step,
                "should_handoff": True,
            }

        if state.current_step == ConversationStep.GREETING:
            return {
                "message": self.voice_agent.greeting(),
                "next_step": ConversationStep.GREETING,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.DISCOVER_SYMPTOMS:
            return {
                "message": self.voice_agent.discover_symptoms(state, message),
                "next_step": ConversationStep.DISCOVER_SYMPTOMS,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.CONFIRM_APPOINTMENT:
            return {
                "message": self.voice_agent.confirm_appointment(state),
                "next_step": ConversationStep.CONFIRM_APPOINTMENT,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.COLLECT_INFORMATION:
            return {
                "message": self.voice_agent.collect_information(state),
                "next_step": ConversationStep.COLLECT_INFORMATION,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.CHECK_CALENDAR:
            return self._calendar_reply(state)

        if state.current_step == ConversationStep.BOOK_APPOINTMENT:
            return {
                "message": self.voice_agent.booked_appointment(state.context.get("selected_slot")),
                "next_step": ConversationStep.BOOK_APPOINTMENT,
                "should_handoff": False,
            }

        if state.current_step == ConversationStep.FINISHED:
            return {
                "message": self.voice_agent.appointment_already_booked(),
                "next_step": ConversationStep.FINISHED,
                "should_handoff": False,
            }

        return {
            "message": self.voice_agent.fallback(),
            "next_step": state.current_step,
            "should_handoff": False,
        }

    def _calendar_reply(self, state: ConversationState) -> dict[str, object]:
        slots = list(state.context.get("available_slots", []))
        if state.context.get("slot_confirmation_required"):
            pending_slot = state.context.get("pending_slot_confirmation")
            return {
                "message": self.voice_agent.calendar_slot_confirmation(pending_slot),
                "next_step": ConversationStep.CHECK_CALENDAR,
                "should_handoff": False,
            }

        if state.context.get("slot_confirmation_declined"):
            return {
                "message": self.voice_agent.calendar_slot_declined(slots),
                "next_step": ConversationStep.CHECK_CALENDAR,
                "should_handoff": False,
            }

        if state.context.get("calendar_selection_error"):
            return {
                "message": self.voice_agent.calendar_selection_error(slots),
                "next_step": ConversationStep.CHECK_CALENDAR,
                "should_handoff": False,
            }

        return {
            "message": self.voice_agent.calendar_options_intro(slots),
            "next_step": ConversationStep.CHECK_CALENDAR,
            "should_handoff": False,
        }
