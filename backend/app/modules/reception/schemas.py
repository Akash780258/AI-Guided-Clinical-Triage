"""
Reception Schemas

Pydantic models for Reception workflows.
"""

from __future__ import annotations

import uuid
from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict


# ==========================================================
# Queue Status
# ==========================================================

class QueueStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    CHECKED_IN = "CHECKED_IN"
    WAITING = "WAITING"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ==========================================================
# Patient Search
# ==========================================================

class PatientSearchRequest(BaseModel):
    query: str


# ==========================================================
# Appointment Booking
# ==========================================================

class BookAppointmentRequest(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_date: date
    reason: str


# ==========================================================
# Check-In
# ==========================================================

class CheckInRequest(BaseModel):
    appointment_id: uuid.UUID


# ==========================================================
# Queue Item
# ==========================================================

class QueueItem(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    appointment_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID

    patient_name: str
    doctor_name: str

    appointment_number: str

    status: QueueStatus


# ==========================================================
# Queue Response
# ==========================================================

class QueueResponse(BaseModel):
    total: int
    items: list[QueueItem]


# ==========================================================
# Generic Message
# ==========================================================

class ReceptionMessage(BaseModel):
    message: str