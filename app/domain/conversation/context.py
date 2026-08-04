from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PatientContext:
    name: str | None = None
    phone: str | None = None

    @classmethod
    def from_dict(cls, data: object) -> PatientContext:
        if not isinstance(data, dict):
            return cls()
        return cls(
            name=_optional_str(data.get("name")),
            phone=_optional_str(data.get("phone")),
        )

    def to_dict(self) -> dict[str, str]:
        result: dict[str, str] = {}
        if self.name:
            result["name"] = self.name
        if self.phone:
            result["phone"] = self.phone
        return result

    def is_complete(self) -> bool:
        return bool(self.name and self.phone)


@dataclass(slots=True)
class ClinicalContext:
    main_complaint: str | None = None
    patient_goal: str | None = None
    requested_specialty: str | None = None
    body_location: str | None = None
    duration: str | None = None
    duration_risk: str | None = None
    severity: str | None = None
    progression: str | None = None
    associated_symptoms: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    appointment_readiness: str = "unknown"

    @classmethod
    def from_dict(cls, data: object) -> ClinicalContext:
        if not isinstance(data, dict):
            return cls()
        return cls(
            main_complaint=_optional_str(data.get("main_complaint")),
            patient_goal=_optional_str(data.get("patient_goal")),
            requested_specialty=_optional_str(data.get("requested_specialty")),
            body_location=_optional_str(data.get("body_location")),
            duration=_optional_str(data.get("duration")),
            duration_risk=_optional_str(data.get("duration_risk")),
            severity=_optional_str(data.get("severity")),
            progression=_optional_str(data.get("progression")),
            associated_symptoms=_string_list(data.get("associated_symptoms")),
            red_flags=_string_list(data.get("red_flags")),
            missing_fields=_string_list(data.get("missing_fields")),
            appointment_readiness=_optional_str(data.get("appointment_readiness")) or "unknown",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "main_complaint": self.main_complaint,
            "patient_goal": self.patient_goal,
            "requested_specialty": self.requested_specialty,
            "body_location": self.body_location,
            "duration": self.duration,
            "duration_risk": self.duration_risk,
            "severity": self.severity,
            "progression": self.progression,
            "associated_symptoms": self.associated_symptoms,
            "red_flags": self.red_flags,
            "missing_fields": self.missing_fields,
            "appointment_readiness": self.appointment_readiness,
        }

    def has_main_complaint(self) -> bool:
        return bool(self.main_complaint)

    def is_ready_for_appointment(self) -> bool:
        return self.appointment_readiness == "enough_context"

    def is_worsening(self) -> bool:
        return self.progression == "piorando"


@dataclass(slots=True)
class CalendarContext:
    available_slots: list[str] = field(default_factory=list)
    selected_slot: str | None = None
    pending_slot_confirmation: str | None = None
    slot_clarification_options: list[str] = field(default_factory=list)
    calendar_selection_error: bool = False
    slot_confirmation_required: bool = False
    slot_confirmation_declined: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalendarContext:
        return cls(
            available_slots=_string_list(data.get("available_slots")),
            selected_slot=_optional_str(data.get("selected_slot")),
            pending_slot_confirmation=_optional_str(data.get("pending_slot_confirmation")),
            slot_clarification_options=_string_list(data.get("slot_clarification_options")),
            calendar_selection_error=bool(data.get("calendar_selection_error")),
            slot_confirmation_required=bool(data.get("slot_confirmation_required")),
            slot_confirmation_declined=bool(data.get("slot_confirmation_declined")),
        )


@dataclass(slots=True)
class ConversationContext:
    messages: list[dict[str, str]] = field(default_factory=list)
    symptoms: list[str] = field(default_factory=list)
    clinical: ClinicalContext = field(default_factory=ClinicalContext)
    patient: PatientContext = field(default_factory=PatientContext)
    calendar: CalendarContext = field(default_factory=CalendarContext)
    reason: str | None = None
    appointment_intent: bool = False
    patient_details: str | None = None
    missing_patient_fields: list[str] = field(default_factory=list)
    last_message: str | None = None
    last_administrative_intent: str | None = None
    safety_category: str | None = None
    safety_message: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: object) -> ConversationContext:
        if not isinstance(data, dict):
            return cls()

        return cls(
            messages=_message_list(data.get("messages")),
            symptoms=_string_list(data.get("symptoms")),
            clinical=ClinicalContext.from_dict(data.get("clinical_summary")),
            patient=PatientContext.from_dict(data.get("patient")),
            calendar=CalendarContext.from_dict(data),
            reason=_optional_str(data.get("reason")),
            appointment_intent=bool(data.get("appointment_intent")),
            patient_details=_optional_str(data.get("patient_details")),
            missing_patient_fields=_string_list(data.get("missing_patient_fields")),
            last_message=_optional_str(data.get("last_message")),
            last_administrative_intent=_optional_str(data.get("last_administrative_intent")),
            safety_category=_optional_str(data.get("safety_category")),
            safety_message=_optional_str(data.get("safety_message")),
            raw=dict(data),
        )

    def to_dict(self) -> dict[str, Any]:
        data = dict(self.raw)
        data.update(
            {
                "messages": self.messages,
                "symptoms": self.symptoms,
                "clinical_summary": self.clinical.to_dict(),
                "patient": self.patient.to_dict(),
                "appointment_intent": self.appointment_intent,
            }
        )

        self._set_optional(data, "reason", self.reason)
        self._set_optional(data, "patient_details", self.patient_details)
        self._set_optional(data, "missing_patient_fields", self.missing_patient_fields)
        self._set_optional(data, "last_message", self.last_message)
        self._set_optional(data, "last_administrative_intent", self.last_administrative_intent)
        self._set_optional(data, "safety_category", self.safety_category)
        self._set_optional(data, "safety_message", self.safety_message)
        self._set_optional(data, "available_slots", self.calendar.available_slots)
        self._set_optional(data, "selected_slot", self.calendar.selected_slot)
        self._set_optional(data, "pending_slot_confirmation", self.calendar.pending_slot_confirmation)
        self._set_optional(data, "slot_clarification_options", self.calendar.slot_clarification_options)
        self._set_optional(data, "calendar_selection_error", self.calendar.calendar_selection_error)
        self._set_optional(data, "slot_confirmation_required", self.calendar.slot_confirmation_required)
        self._set_optional(data, "slot_confirmation_declined", self.calendar.slot_confirmation_declined)
        return data

    def patient_is_complete(self) -> bool:
        return self.patient.is_complete()

    def has_partial_clinical_context(self) -> bool:
        return any(
            [
                self.clinical.main_complaint,
                self.clinical.duration,
                self.clinical.severity,
                self.clinical.progression,
            ]
        )

    @staticmethod
    def _set_optional(data: dict[str, Any], key: str, value: object) -> None:
        if value in (None, [], {}, False):
            data.pop(key, None)
            return
        data[key] = value


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _message_list(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    messages: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict):
            role = str(item.get("role", ""))
            content = str(item.get("content", ""))
            messages.append({"role": role, "content": content})
    return messages
