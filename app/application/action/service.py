from __future__ import annotations


class ActionEngine:
    def book_appointment(self, date: str, time: str, reason: str) -> dict[str, object]:
        if not date or not time or not reason:
            return {"scheduled": False, "reason": "Dados incompletos"}

        return {
            "scheduled": True,
            "slot": f"{date} {time}",
            "reason": reason,
            "provider": "local-action-engine",
        }
