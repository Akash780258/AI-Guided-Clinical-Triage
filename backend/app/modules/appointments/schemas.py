"""
Appointment Schemas

Pydantic models for Appointment APIs.
"""

from __future__ import annotations

import uuid
from datetime import date, time, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Appointment Status
# ==========================================================

class AppointmentStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


# ==========================================================
# Base
# ==========================================================

class AppointmentBase(BaseModel):
    patient_id: uuid.UUID

    doctor_id: uuid.UUID

    appointment_date: date

    start_time: time

    end_time: time

    reason: str = Field(
        min_length=2,
        max_length=1000,
    )

    notes: str | None = None


# ==========================================================
# Create
# ==========================================================

class AppointmentCreate(AppointmentBase):
    pass


# ==========================================================
# Update
# ==========================================================

class AppointmentUpdate(BaseModel):
    appointment_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = None
    notes: str | None = None
    status: AppointmentStatus | None = None


# ==========================================================
# Response
# ==========================================================

class AppointmentResponse(AppointmentBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    appointment_number: str

    status: AppointmentStatus

    created_by_id: uuid.UUID

    created_at: datetime

    updated_at: datetime

    deleted_at: datetime | None = None


# ==========================================================
# List Response
# ==========================================================

class AppointmentListResponse(BaseModel):
    total: int
    items: list[AppointmentResponse]


# ==========================================================
# Message Response
# ==========================================================

class AppointmentMessage(BaseModel):
    message: str