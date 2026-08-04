from __future__ import annotations

import re
from typing import Any
from unicodedata import combining, normalize


class MessageUnderstandingEngine:
    def enrich_context(self, context: dict[str, Any], message: str) -> dict[str, Any]:
        summary = self._default_summary(context.get("clinical_summary"))
        normalized = self._normalize(message)

        patient_goal = self._extract_patient_goal(normalized)
        if patient_goal:
            summary["patient_goal"] = patient_goal

        requested_specialty = self._extract_requested_specialty(normalized)
        if requested_specialty:
            summary["requested_specialty"] = requested_specialty

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
        context_memory = self._updated_context_memory(context, message, summary)

        return {
            **context,
            "clinical_summary": summary,
            "symptoms": symptoms,
            "context_memory": context_memory,
        }

    def _default_summary(self, current: object) -> dict[str, Any]:
        if isinstance(current, dict):
            return {
                "main_complaint": current.get("main_complaint"),
                "patient_goal": current.get("patient_goal"),
                "requested_specialty": current.get("requested_specialty"),
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
            "patient_goal": None,
            "requested_specialty": None,
            "body_location": None,
            "duration": None,
            "severity": None,
            "progression": None,
            "associated_symptoms": [],
            "red_flags": [],
            "missing_fields": [],
            "appointment_readiness": "unknown",
        }

    def _extract_patient_goal(self, normalized: str) -> str | None:
        if self._has_appointment_intent(normalized):
            return "schedule_appointment"
        return None

    def _extract_requested_specialty(self, normalized: str) -> str | None:
        specialties = {
            "alergista": "alergista",
            "dermatologista": "dermatologista",
            "cardiologista": "cardiologista",
            "ortopedista": "ortopedista",
            "clinico geral": "clinico geral",
            "clinica geral": "clinico geral",
        }
        for marker, specialty in specialties.items():
            if marker in normalized:
                return specialty
        return None

    def _extract_main_complaint(self, message: str, normalized: str) -> str | None:
        complaint_terms = [
            "alergia",
            "alergico",
            "alergica",
            "cabelo",
            "cabelos",
            "queda",
            "caindo",
            "coceira",
            "incomodo",
            "irritacao",
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

        cleaned = self._clinical_clause(message, normalized, complaint_terms)
        cleaned = re.sub(
            r"^\s*(oi+|ola|olá|bom dia|boa tarde|boa noite)[,!.\s]*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"^\s*(eu\s+)?(estou sentindo|to sentindo|tou sentindo|estou com|to com|tou com|estou|to|tou|tenho|sinto|sentindo|com)\b",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()
        cleaned = re.sub(
            r"\b(quero|gostaria|preciso)\s+(de\s+)?(agendar|marcar)\s+(uma\s+)?consulta\b",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\b(quero|gostaria|preciso)\s+(de\s+)?(agendar|marcar)\b.*$",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\b(com|para)\s+(um\s+|uma\s+|o\s+|a\s+)?\w*ista\b", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.split(
            r"\b(tem|ha|há|desde|comecou|comecou|esta|está|e foi)\b",
            cleaned,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        cleaned = re.sub(
            r"\b\d+\s+(?:dias|dia|horas|hora|semanas|semana|meses|mes)\b",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\b(?:a|ha|hÃ¡|tem|desde)\s+(?:alguns|algumas|uns|umas)\s+(?:dias|horas|semanas|meses)\b",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"^\s*com\b", "", cleaned, flags=re.IGNORECASE)
        return " ".join(cleaned.split()).strip(" ,.;") or message.strip()

    def _clinical_clause(self, message: str, normalized: str, complaint_terms: list[str]) -> str:
        raw_clauses = re.split(r"[,.;]|\s+e\s+|\s+mas\s+", message, flags=re.IGNORECASE)
        normalized_clauses = re.split(r"[,.;]|\s+e\s+|\s+mas\s+", normalized, flags=re.IGNORECASE)
        for raw_clause, normalized_clause in zip(raw_clauses, normalized_clauses, strict=False):
            if any(term in normalized_clause for term in complaint_terms):
                return raw_clause.strip()
        return message

    def _extract_body_location(self, normalized: str) -> str | None:
        locations = ["dedos", "mao", "maos", "pele", "cabeca", "costas", "peito", "barriga", "perna", "braco"]
        for location in locations:
            if location in normalized:
                return location
        return None

    def _extract_duration(self, message: str, normalized: str) -> str | None:
        duration_match = re.search(
            r"\b(?:tem|ha|há|desde)\s+(?:uns?\s+|mais ou menos\s+)?(\d+\s+(?:dias|dia|horas|hora|semanas|semana|meses|mes))",
            message,
            re.IGNORECASE,
        )
        if duration_match:
            return duration_match.group(1)

        simple_match = re.search(r"\b(\d+\s+(?:dias|dia|horas|hora|semanas|semana|meses|mes))\b", normalized)
        if simple_match:
            return simple_match.group(1)

        vague_match = re.search(
            r"\b(?:a|ha|hÃ¡|tem|desde)\s+(alguns|algumas|uns|umas)\s+(dias|horas|semanas|meses)\b",
            normalized,
        )
        if vague_match:
            return f"{vague_match.group(1)} {vague_match.group(2)}"

        bare_vague_match = re.search(r"\b(alguns|algumas|uns|umas)\s+(dias|horas|semanas|meses)\b", normalized)
        if bare_vague_match:
            return f"{bare_vague_match.group(1)} {bare_vague_match.group(2)}"

        if "desde ontem" in normalized:
            return "desde ontem"
        if "hoje" in normalized:
            return "hoje"
        return None

    def _extract_severity(self, normalized: str) -> str | None:
        if "muito" in normalized or "forte" in normalized or "intensa" in normalized or "intenso" in normalized:
            return "incomoda muito"
        if "incomodo" in normalized or "incomoda" in normalized or "incomodando" in normalized or "bastante" in normalized:
            return "incomoda"
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
            "alergia",
            "alergico",
            "alergica",
            "cabelo",
            "cabelos",
            "queda",
            "caindo",
            "coceira",
            "incomodo",
            "incomoda",
            "irritacao",
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
            "mes",
            "meses",
        ]
        return any(marker in normalized for marker in clinical_markers)

    def _updated_context_memory(
        self,
        context: dict[str, Any],
        message: str,
        summary: dict[str, Any],
    ) -> dict[str, Any]:
        memory = dict(context.get("context_memory", {})) if isinstance(context.get("context_memory"), dict) else {}
        facts = list(memory.get("facts", [])) if isinstance(memory.get("facts"), list) else []
        patient_message = " ".join(message.split()).strip()
        if patient_message and patient_message not in facts:
            facts.append(patient_message)

        return {
            "patient_goal": summary.get("patient_goal"),
            "requested_specialty": summary.get("requested_specialty"),
            "main_complaint": summary.get("main_complaint"),
            "duration": summary.get("duration"),
            "severity": summary.get("severity"),
            "progression": summary.get("progression"),
            "missing_fields": summary.get("missing_fields", []),
            "facts": facts[-10:],
        }

    def _has_appointment_intent(self, normalized: str) -> bool:
        appointment_keywords = ["agendar", "agenda", "consulta", "marcar", "atendimento"]
        return any(keyword in normalized for keyword in appointment_keywords)

    def _normalize(self, message: str) -> str:
        without_accents = "".join(
            char for char in normalize("NFD", message.strip().lower())
            if not combining(char)
        )
        return without_accents
