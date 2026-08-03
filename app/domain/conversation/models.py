from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    EMERGENCY = "emergency"
    FINISHED = "finished"


class ConversationStep(str, Enum):
    GREETING = "greeting"
    DISCOVER_REASON = "discover_reason"
    DISCOVER_SYMPTOMS = "discover_symptoms"
    CONFIRM_APPOINTMENT = "confirm_appointment"
    COLLECT_INFORMATION = "collect_information"
    CHECK_CALENDAR = "check_calendar"
    BOOK_APPOINTMENT = "book_appointment"
    FINISHED = "finished"
    EMERGENCY = "emergency"


@dataclass(slots=True)
class ConversationState:
    current_step: ConversationStep
    status: ConversationStatus
    context: dict[str, Any] = field(default_factory=dict)
    conversation_id: str | None = None
