from __future__ import annotations

from datetime import datetime
from unicodedata import combining, normalize

from app.domain.conversation.models import (
    ConversationState,
    ConversationStatus,
    ConversationStep,
)


class ConversationStateMachine:
    def start(self) -> ConversationState:
        return ConversationState(
            current_step=ConversationStep.GREETING,
            status=ConversationStatus.ACTIVE,
            context={"messages": [], "symptoms": [], "clinical_summary": {}},
            conversation_id=None,
        )

    def process_message(self, state: ConversationState, message: str) -> ConversationState:
        normalized = message.strip().lower()
        context = self._append_message(state.context, message)

        if self._is_emergency(normalized):
            return ConversationState(
                current_step=ConversationStep.EMERGENCY,
                status=ConversationStatus.EMERGENCY,
                context={**context, "last_message": message},
                conversation_id=state.conversation_id,
            )

        if self._is_greeting(normalized) and not context.get("symptoms"):
            return ConversationState(
                current_step=ConversationStep.GREETING,
                status=state.status,
                context=context,
                conversation_id=state.conversation_id,
            )

        if state.current_step == ConversationStep.COLLECT_INFORMATION:
            return ConversationState(
                current_step=ConversationStep.CHECK_CALENDAR,
                status=state.status,
                context={**context, "patient_details": message, "available_slots": self.default_available_slots()},
                conversation_id=state.conversation_id,
            )

        if state.current_step == ConversationStep.CHECK_CALENDAR:
            selected_slot = self._select_slot(message, context.get("available_slots", []))
            if selected_slot is not None:
                return ConversationState(
                    current_step=ConversationStep.BOOK_APPOINTMENT,
                    status=state.status,
                    context={**context, "selected_slot": selected_slot},
                    conversation_id=state.conversation_id,
                )

            return ConversationState(
                current_step=ConversationStep.CHECK_CALENDAR,
                status=state.status,
                context={**context, "calendar_selection_error": True},
                conversation_id=state.conversation_id,
            )

        if state.current_step == ConversationStep.CONFIRM_APPOINTMENT:
            if self._is_affirmative(normalized) or self._is_appointment_intent(normalized):
                return ConversationState(
                    current_step=ConversationStep.COLLECT_INFORMATION,
                    status=state.status,
                    context={**context, "appointment_intent": True},
                    conversation_id=state.conversation_id,
                )

            if self._is_negative(normalized):
                return ConversationState(
                    current_step=ConversationStep.DISCOVER_SYMPTOMS,
                    status=state.status,
                    context={**context, "appointment_intent": False},
                    conversation_id=state.conversation_id,
                )

        appointment_intent = self._is_appointment_intent(normalized)
        symptoms = self._updated_symptoms(context, message, appointment_intent)
        context = {**context, "symptoms": symptoms}
        has_enough_context = self._has_enough_clinical_context(context)

        if appointment_intent and (symptoms or has_enough_context):
            return ConversationState(
                current_step=ConversationStep.COLLECT_INFORMATION,
                status=state.status,
                context={**context, "appointment_intent": True},
                conversation_id=state.conversation_id,
            )

        if appointment_intent:
            return ConversationState(
                current_step=ConversationStep.DISCOVER_SYMPTOMS,
                status=state.status,
                context={**context, "appointment_intent": True, "reason": context.get("reason", message)},
                conversation_id=state.conversation_id,
            )

        if has_enough_context or len(symptoms) >= 2:
            return ConversationState(
                current_step=ConversationStep.CONFIRM_APPOINTMENT,
                status=state.status,
                context={**context, "reason": context.get("reason", symptoms[0])},
                conversation_id=state.conversation_id,
            )

        return ConversationState(
            current_step=ConversationStep.DISCOVER_SYMPTOMS,
            status=state.status,
            context={**context, "reason": context.get("reason", message)},
            conversation_id=state.conversation_id,
        )

    def default_available_slots(self) -> list[str]:
        slots = [
            "2026-08-10 09:00",
            "2026-08-10 14:00",
            "2026-08-11 10:00",
        ]
        return sorted(slots, key=self._slot_datetime)

    def append_message(self, context: dict[str, object], message: str) -> dict[str, object]:
        return self._append_message(context, message)

    def select_slot(self, message: str, slots: object) -> str | None:
        return self._select_slot(message, slots)

    def slot_candidates(self, message: str, slots: object) -> list[str]:
        return self._slot_candidates(message, slots)

    def _append_message(self, context: dict[str, object], message: str) -> dict[str, object]:
        messages = list(context.get("messages", []))
        messages.append({"role": "patient", "content": message})
        return {**context, "messages": messages, "last_message": message}

    def _updated_symptoms(self, context: dict[str, object], message: str, appointment_intent: bool) -> list[str]:
        symptoms = list(context.get("symptoms", []))
        normalized = message.strip().lower()
        summary = context.get("clinical_summary")
        main_complaint = summary.get("main_complaint") if isinstance(summary, dict) else None
        if main_complaint:
            return symptoms

        if not appointment_intent and not self._is_affirmative(normalized) and not self._is_negative(normalized) and message.strip():
            symptoms.append(message)
        return symptoms

    def _select_slot(self, message: str, slots: object) -> str | None:
        ordered_slots = self._ordered_slots(slots)
        if not ordered_slots:
            return None

        normalized = self._normalize(message)

        for slot in ordered_slots:
            if slot in message:
                return slot

        candidates = self._slot_candidates(message, ordered_slots)
        if len(candidates) == 1:
            return candidates[0]

        requested_hour = self._requested_hour(normalized)
        if requested_hour is not None:
            for slot in ordered_slots:
                if self._slot_datetime(slot).hour == requested_hour:
                    return slot

        if normalized in {"1", "primeiro", "primeira"}:
            return ordered_slots[0]
        if normalized in {"2", "segundo"} and len(ordered_slots) > 1:
            return ordered_slots[1]
        if normalized in {"3", "terceiro", "terceira"} and len(ordered_slots) > 2:
            return ordered_slots[2]
        return None

    def _slot_candidates(self, message: str, slots: object) -> list[str]:
        ordered_slots = self._ordered_slots(slots)
        if not ordered_slots:
            return []

        normalized = self._normalize(message)
        period = self._requested_period(normalized)
        weekday = self._requested_weekday(normalized)
        requested_hour = self._requested_hour(normalized)

        candidates = ordered_slots
        if weekday is not None:
            candidates = [slot for slot in candidates if self._weekday_name(slot) == weekday]
        if period is not None:
            candidates = [slot for slot in candidates if self._slot_period(slot) == period]
        if requested_hour is not None:
            candidates = [slot for slot in candidates if self._slot_datetime(slot).hour == requested_hour]

        if weekday is None and period is None and requested_hour is None:
            return []
        return candidates

    def _ordered_slots(self, slots: object) -> list[str]:
        if not isinstance(slots, list) or not slots:
            return []
        return sorted([str(slot) for slot in slots], key=self._slot_datetime)

    def _slot_datetime(self, slot: str) -> datetime:
        return datetime.strptime(slot, "%Y-%m-%d %H:%M")

    def _weekday_name(self, slot: str) -> str:
        names = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
        return names[self._slot_datetime(slot).weekday()]

    def _slot_period(self, slot: str) -> str:
        hour = self._slot_datetime(slot).hour
        if hour < 12:
            return "manha"
        if hour < 18:
            return "tarde"
        return "noite"

    def _requested_period(self, message: str) -> str | None:
        if "manha" in message:
            return "manha"
        if "tarde" in message:
            return "tarde"
        if "noite" in message:
            return "noite"
        return None

    def _requested_weekday(self, message: str) -> str | None:
        weekdays = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
        for weekday in weekdays:
            if weekday in message:
                return weekday
        return None

    def _requested_hour(self, message: str) -> int | None:
        for hour in range(24):
            if f"{hour}h" in message or f"{hour}:00" in message:
                return hour
        return None

    def _normalize(self, message: str) -> str:
        return "".join(
            char for char in normalize("NFD", message.strip().lower()) if not combining(char)
        )

    def _is_emergency(self, message: str) -> bool:
        emergency_keywords = [
            "falta de ar grave",
            "convulsao",
            "dor intensa no peito",
            "perda de consciencia",
            "choque anafilatico",
            "sangramento intenso",
            "reacao alergica grave",
        ]
        return any(keyword in message for keyword in emergency_keywords)

    def _is_appointment_intent(self, message: str) -> bool:
        appointment_keywords = ["agendar", "consulta", "marcar", "atendimento"]
        return any(keyword in message for keyword in appointment_keywords)

    def _has_enough_clinical_context(self, context: dict[str, object]) -> bool:
        summary = context.get("clinical_summary")
        return isinstance(summary, dict) and summary.get("appointment_readiness") == "enough_context"

    def _is_greeting(self, message: str) -> bool:
        greetings = {"oi", "ola", "olá", "bom dia", "boa tarde", "boa noite"}
        return message in greetings

    def _is_affirmative(self, message: str) -> bool:
        affirmatives = {
            "sim",
            "quero",
            "pode ser",
            "vamos",
            "vamos sim",
            "por favor",
            "me ajuda",
            "quero marcar",
            "quero agendar",
        }
        return message in affirmatives

    def _is_negative(self, message: str) -> bool:
        negatives = {"nao", "não", "agora nao", "agora não", "nao quero", "não quero"}
        return message in negatives
