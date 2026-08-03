from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Clinic:
    name: str
    specialty: str


@dataclass(slots=True)
class Patient:
    name: str
    phone: str


@dataclass(slots=True)
class Appointment:
    patient_name: str
    scheduled_at: str
    specialty: str
