from __future__ import annotations

from dataclasses import dataclass
from unicodedata import combining, normalize


@dataclass(frozen=True, slots=True)
class SafetyDecision:
    category: str
    should_interrupt: bool
    message: str | None = None


class SafetyEngine:
    def evaluate(self, message: str) -> SafetyDecision:
        normalized = self._normalize(message)

        if self._is_emergency(normalized):
            return SafetyDecision(
                category="emergency",
                should_interrupt=True,
                message=(
                    "Estou vendo sinais que podem indicar urgencia. Procure atendimento de emergencia agora "
                    "e, se estiver no Brasil, acione o Samu pelo 192."
                ),
            )

        if self._is_mental_health_risk(normalized):
            return SafetyDecision(
                category="mental_health_risk",
                should_interrupt=True,
                message=(
                    "Sinto muito que voce esteja passando por isso. Voce nao precisa lidar com isso sozinho. "
                    "Procure ajuda imediata com alguem de confianca ou um servico de emergencia. No Brasil, "
                    "voce tambem pode ligar para o CVV pelo 188."
                ),
            )

        if self._asks_for_diagnosis_or_prescription(normalized):
            return SafetyDecision(
                category="unsafe_prescription_or_diagnosis",
                should_interrupt=True,
                message=(
                    "Eu nao posso diagnosticar, prescrever remedios ou orientar dosagens por aqui. "
                    "Posso te ajudar a organizar os sintomas e encaminhar para um atendimento com seguranca."
                ),
            )

        if self._is_administrative(normalized):
            return SafetyDecision(category="administrative", should_interrupt=False)

        if self._is_clinical_context(normalized):
            return SafetyDecision(category="safe_clinical_context", should_interrupt=False)

        return SafetyDecision(category="safe", should_interrupt=False)

    def _is_emergency(self, message: str) -> bool:
        emergency_keywords = [
            "falta de ar grave",
            "nao consigo respirar",
            "convulsao",
            "dor intensa no peito",
            "perda de consciencia",
            "choque anafilatico",
            "sangramento intenso",
            "reacao alergica grave",
        ]
        return any(keyword in message for keyword in emergency_keywords)

    def _is_mental_health_risk(self, message: str) -> bool:
        mental_health_keywords = [
            "quero morrer",
            "me matar",
            "tirar minha vida",
            "nao aguento mais viver",
            "nao quero mais viver",
            "penso em suicidio",
            "pensando em suicidio",
        ]
        return any(keyword in message for keyword in mental_health_keywords)

    def _asks_for_diagnosis_or_prescription(self, message: str) -> bool:
        restricted_terms = [
            "qual remedio",
            "posso tomar",
            "que dose",
            "dosagem",
            "me diagnostique",
            "qual diagnostico",
            "prescreva",
            "receita medica",
            "antibiotico",
        ]
        return any(term in message for term in restricted_terms)

    def _is_clinical_context(self, message: str) -> bool:
        clinical_terms = [
            "dor",
            "febre",
            "enjoo",
            "nausea",
            "tontura",
            "sintoma",
            "consulta",
            "exame",
            "agendar",
            "marcar",
        ]
        return any(term in message for term in clinical_terms)

    def _is_administrative(self, message: str) -> bool:
        administrative_terms = [
            "preco",
            "valor",
            "convenio",
            "endereco",
            "horario",
            "cancelar",
            "remarcar",
        ]
        return any(term in message for term in administrative_terms)

    def _normalize(self, message: str) -> str:
        without_accents = "".join(
            char for char in normalize("NFD", message.strip().lower())
            if not combining(char)
        )
        return without_accents
