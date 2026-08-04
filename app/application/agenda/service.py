from __future__ import annotations

from datetime import datetime
from unicodedata import combining, normalize


class AgendaAgent:
    def default_available_slots(self) -> list[str]:
        slots = [
            "2026-08-10 09:00",
            "2026-08-10 14:00",
            "2026-08-11 10:00",
        ]
        return self.order_slots(slots)

    def select_slot(self, message: str, slots: object) -> str | None:
        ordered_slots = self.order_slots(slots)
        if not ordered_slots:
            return None

        normalized = self._normalize(message)

        for slot in ordered_slots:
            if slot in message:
                return slot

        candidates = self.slot_candidates(message, ordered_slots)
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
            if f"{hour}h" in message or f"{hour}:00" in message:
                return hour
        return None

    def _normalize(self, message: str) -> str:
        return "".join(
            char for char in normalize("NFD", message.strip().lower()) if not combining(char)
        )
