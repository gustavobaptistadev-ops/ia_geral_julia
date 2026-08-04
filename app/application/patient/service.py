from __future__ import annotations

import re

from app.domain.conversation.context import ConversationContext


class PatientAgent:
    def enrich_context(self, context: dict[str, object], message: str) -> dict[str, object]:
        conversation_context = ConversationContext.from_dict(context)
        name = self.extract_name(message)
        phone = self.extract_phone(message)

        if name:
            conversation_context.patient.name = name
        if phone:
            conversation_context.patient.phone = phone

        return {
            **context,
            "patient": conversation_context.patient.to_dict(),
            "missing_patient_fields": self.missing_fields(conversation_context),
        }

    def missing_fields(self, context: ConversationContext) -> list[str]:
        missing = []
        if not context.patient.name:
            missing.append("name")
        if not context.patient.phone:
            missing.append("phone")
        return missing

    def extract_name(self, message: str) -> str | None:
        without_phone = re.sub(r"[\d\s()+-]{8,}", " ", message)
        without_phone = without_phone.split(",", 1)[0]
        without_phone = re.sub(
            r"\b(de manha|de tarde|de noite|manha|tarde|noite)\b",
            " ",
            without_phone,
            flags=re.IGNORECASE,
        )
        words = [word for word in without_phone.strip().split() if any(char.isalpha() for char in word)]
        if len(words) < 2:
            return None
        return " ".join(words).strip(" ,.;")

    def extract_phone(self, message: str) -> str | None:
        digits = "".join(char for char in message if char.isdigit())
        return digits if len(digits) >= 8 else None
