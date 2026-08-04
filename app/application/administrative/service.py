from __future__ import annotations

from dataclasses import dataclass
from unicodedata import combining, normalize


@dataclass(frozen=True, slots=True)
class AdministrativeResponse:
    intent: str
    message: str


class AdministrativeAgent:
    def handle(self, message: str) -> AdministrativeResponse | None:
        if self._is_exam_request(message):
            return AdministrativeResponse(
                intent="exam_referral",
                message=(
                    "A LifelineOne realiza consultas e acompanhamento medico. "
                    "Para exames, voce pode falar com nosso laboratorio parceiro, o Laboratorio Life.\n\n"
                    "Telefone/WhatsApp: 61999999999\n"
                    "Endereco: Connect Tower\n\n"
                    "Posso te auxiliar em algo mais?"
                ),
            )
        return None

    def _is_exam_request(self, message: str) -> bool:
        normalized = self._normalize(message)
        return any(term in normalized for term in ["exame", "exames", "laboratorio", "laboratorial"])

    def _normalize(self, message: str) -> str:
        without_accents = "".join(
            char for char in normalize("NFD", message.strip().lower()) if not combining(char)
        )
        return " ".join(without_accents.split())
