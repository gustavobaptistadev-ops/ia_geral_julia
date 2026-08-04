from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from unicodedata import combining, normalize


@dataclass(slots=True)
class AgendaSelectionResult:
    intent: str
    selected_slot: str | None = None
    candidates: list[str] | None = None
    requested_hour: int | None = None
    requested_weekday: str | None = None
    requested_period: str | None = None


class AgendaAgent:
    def default_available_slots(self) -> list[str]:
        slots = [
            "2026-08-10 09:00",
            "2026-08-10 14:00",
            "2026-08-11 10:00",
        ]
        return self.order_slots(slots)

    def select_slot(self, message: str, slots: object) -> str | None:
        result = self.interpret_selection(message, slots)
        if result.intent == "slot_selected":
            return result.selected_slot
        return None

    def interpret_selection(self, message: str, slots: object, scoped_slots: object | None = None) -> AgendaSelectionResult:
        ordered_slots = self.order_slots(slots)
        scoped_ordered_slots = self.order_slots(scoped_slots) if scoped_slots is not None else ordered_slots
        if not ordered_slots:
            return AgendaSelectionResult(intent="no_slots", candidates=[])

        normalized = self._normalize(message)
        requested_hour = self._requested_hour(normalized)
        requested_weekday = self._requested_weekday(normalized)
        requested_period = self._requested_period(normalized)
        contextual_weekday = requested_weekday or self._common_weekday(scoped_ordered_slots)

        for slot in ordered_slots:
            if slot in message:
                return AgendaSelectionResult(
                    intent="slot_selected",
                    selected_slot=slot,
                    candidates=[slot],
                    requested_hour=requested_hour,
                    requested_weekday=requested_weekday,
                    requested_period=requested_period,
                )

        if normalized in {"1", "primeiro", "primeira"}:
            return self._numbered_selection(ordered_slots, 0)
        if normalized in {"2", "segundo"}:
            return self._numbered_selection(ordered_slots, 1)
        if normalized in {"3", "terceiro", "terceira"}:
            return self._numbered_selection(ordered_slots, 2)

        candidates = self.slot_candidates(message, scoped_ordered_slots)
        if len(candidates) == 1:
            return AgendaSelectionResult(
                intent="slot_selected",
                selected_slot=candidates[0],
                candidates=candidates,
                requested_hour=requested_hour,
                requested_weekday=requested_weekday,
                requested_period=requested_period,
            )

        if len(candidates) > 1:
            return AgendaSelectionResult(
                intent="slot_needs_confirmation",
                candidates=candidates,
                requested_hour=requested_hour,
                requested_weekday=requested_weekday,
                requested_period=requested_period,
            )

        if requested_hour is not None:
            return AgendaSelectionResult(
                intent="slot_unavailable",
                candidates=scoped_ordered_slots,
                requested_hour=requested_hour,
                requested_weekday=contextual_weekday,
                requested_period=requested_period,
            )

        if requested_weekday is not None or requested_period is not None:
            return AgendaSelectionResult(
                intent="slot_unavailable",
                candidates=scoped_ordered_slots,
                requested_hour=requested_hour,
                requested_weekday=contextual_weekday,
                requested_period=requested_period,
            )

        return AgendaSelectionResult(
            intent="unknown",
            candidates=[],
            requested_hour=requested_hour,
            requested_weekday=requested_weekday,
            requested_period=requested_period,
        )

    def slot_candidates(self, message: str, slots: object) -> list[str]:
        ordered_slots = self.order_slots(slots)
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

    def order_slots(self, slots: object) -> list[str]:
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
            if re.search(rf"\b{hour}\s*h\b", message):
                return hour
            if re.search(rf"\b{hour}:00\b", message):
                return hour
            if re.search(rf"\b{hour}\s*horas?\b", message):
                return hour
        return None

    def _common_weekday(self, slots: list[str]) -> str | None:
        weekdays = {self._weekday_name(slot) for slot in slots}
        if len(weekdays) == 1:
            return next(iter(weekdays))
        return None

    def _numbered_selection(self, ordered_slots: list[str], index: int) -> AgendaSelectionResult:
        if len(ordered_slots) > index:
            return AgendaSelectionResult(
                intent="slot_selected",
                selected_slot=ordered_slots[index],
                candidates=[ordered_slots[index]],
            )
        return AgendaSelectionResult(intent="unknown", candidates=[])

    def _normalize(self, message: str) -> str:
        return "".join(
            char for char in normalize("NFD", message.strip().lower()) if not combining(char)
        )
