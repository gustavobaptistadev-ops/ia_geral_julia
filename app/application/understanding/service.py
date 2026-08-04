from __future__ import annotations

import re
from typing import Any
from unicodedata import combining, normalize


class MessageUnderstandingEngine:
    def enrich_context(self, context: dict[str, Any], message: str) -> dict[str, Any]:
        summary = self._default_summary(context.get("clinical_summary"))
        normalized = self._normalize(message)

        main_complaint = self._extract_main_complaint(message, normalized)
        if main_complaint and summary.get("main_complaint") is None:
            summary["main_complaint"] = main_complaint

        body_location = self._extract_body_location(normalized)
        if body_location and summary.get("body_location") is None:
            summary["body_location"] = body_location

        duration = self._extract_duration(message, normalized)
        if duration:
            summary["duration"] = duration

        severity = self._extract_severity(normalized)
        if severity:
            summary["severity"] = severity

        progression = self._extract_progression(normalized)
        if progression:
            summary["progression"] = progression

        summary["missing_fields"] = self._missing_fields(summary)
        summary["appointment_readiness"] = (
            "enough_context" if self._has_enough_context(summary) else "needs_more_context"
        )

        symptoms = self._updated_symptoms(context, message, normalized, main_complaint)

        return {**context, "clinical_summary": summary, "symptoms": symptoms}

    def _default_summary(self, current: object) -> dict[str, Any]:
        if isinstance(current, dict):
            return {
                "main_complaint": current.get("main_complaint"),
                "body_location": current.get("body_location"),
                "duration": current.get("duration"),
                "severity": current.get("severity"),
                "progression": current.get("progression"),
                "associated_symptoms": list(current.get("associated_symptoms", [])),
                "red_flags": list(current.get("red_flags", [])),
                "missing_fields": list(current.get("missing_fields", [])),
                "appointment_readiness": current.get("appointment_readiness", "unknown"),
            }

        return {
            "main_complaint": None,
            "body_location": None,
            "duration": None,
            "severity": None,
            "progression": None,
            "associated_symptoms": [],
            "red_flags": [],
            "missing_fields": [],
            "appointment_readiness": "unknown",
        }

    def _extract_main_complaint(self, message: str, normalized: str) -> str | None:
        complaint_terms = [
            "coceira",
            "incomodo",
            "dor",
            "mancha",
            "manchas",
            "febre",
            "enjoo",
            "nausea",
            "tontura",
            "ardencia",
            "formigamento",
            "bolha",
            "bolhas",
            "vermelha",
            "vermelhas",
        ]
        if not any(term in normalized for term in complaint_terms):
            return None

        cleaned = re.sub(r"^\s*(estou com|tenho|sinto|sentindo|com)\b", "", message, flags=re.IGNORECASE).strip()
        cleaned = re.split(r"\b(tem|ha|há|desde|começou|comecou|esta|está|e foi)\b", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
        return " ".join(cleaned.split()).strip(" ,.;") or message.strip()

    def _extract_body_location(self, normalized: str) -> str | None:
        locations = ["dedos", "mao", "maos", "pele", "cabeca", "costas", "peito", "barriga", "perna", "braco"]
        for location in locations:
            if location in normalized:
                return location
        return None

    def _extract_duration(self, message: str, normalized: str) -> str | None:
        duration_match = re.search(r"\b(?:tem|ha|há|desde)\s+(\d+\s+(?:dias|dia|horas|hora|semanas|semana|meses|mes))", message, re.IGNORECASE)
        if duration_match:
            return duration_match.group(1)

        simple_match = re.search(r"\b(\d+\s+(?:dias|dia|horas|hora|semanas|semana|meses|mes))\b", normalized)
        if simple_match:
            return simple_match.group(1)

        if "desde ontem" in normalized:
            return "desde ontem"
        if "hoje" in normalized:
            return "hoje"
        return None

    def _extract_severity(self, normalized: str) -> str | None:
        if "muito" in normalized or "forte" in normalized or "intensa" in normalized or "intenso" in normalized:
            return "incomoda muito"
        if "leve" in normalized:
            return "leve"
        return None

    def _extract_progression(self, normalized: str) -> str | None:
        if "piorando" in normalized or "piorou" in normalized:
            return "piorando"
        if "melhorou" in normalized or "melhorando" in normalized:
            return "melhorando"
        return None

    def _missing_fields(self, summary: dict[str, Any]) -> list[str]:
        missing = []
        for field in ["main_complaint", "duration"]:
            if not summary.get(field):
                missing.append(field)
        if not summary.get("severity") and not summary.get("progression"):
            missing.append("severity_or_progression")
        return missing

    def _has_enough_context(self, summary: dict[str, Any]) -> bool:
        return (
            bool(summary.get("main_complaint"))
            and bool(summary.get("duration"))
            and (bool(summary.get("severity")) or bool(summary.get("progression")))
        )

    def _updated_symptoms(
        self,
        context: dict[str, Any],
        message: str,
        normalized: str,
        main_complaint: str | None,
    ) -> list[str]:
        symptoms = list(context.get("symptoms", []))

        if main_complaint and main_complaint not in symptoms:
            symptoms.append(main_complaint)
            return symptoms

        if self._is_clinical_detail(normalized):
            detail = " ".join(message.split()).strip()
            if detail and detail not in symptoms:
                symptoms.append(detail)

        return symptoms

    def _is_clinical_detail(self, normalized: str) -> bool:
        clinical_markers = [
            "coceira",
            "incomodo",
            "incomoda",
            "dor",
            "bolha",
            "bolhas",
            "vermelha",
            "vermelhas",
            "piorando",
            "piorou",
            "dia",
            "dias",
            "semana",
            "semanas",
        ]
        return any(marker in normalized for marker in clinical_markers)

    def _normalize(self, message: str) -> str:
        without_accents = "".join(
            char for char in normalize("NFD", message.strip().lower())
            if not combining(char)
        )
        return without_accents
