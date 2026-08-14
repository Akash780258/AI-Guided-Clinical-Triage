"""
Medical Record Schemas

Pydantic models for Medical Record APIs.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Base
# ==========================================================

class MedicalRecordBase(BaseModel):

    patient_id: uuid.UUID

    doctor_id: uuid.UUID

    appointment_id: uuid.UUID

    chief_complaint: str = Field(
        min_length=2,
        max_length=5000,
    )

    history_present_illness: str | None = None

    past_medical_history: str | None = None

    family_history: str | None = None

    allergies: str | None = None

    current_medications: str | None = None

    physical_examination: str | None = None

    diagnosis: str = Field(
        min_length=2,
        max_length=5000,
    )

    treatment_plan: str | None = None

    notes: str | None = None


# ==========================================================
# Create
# ==========================================================

class MedicalRecordCreate(MedicalRecordBase):
    pass


# ==========================================================
# Update
# ==========================================================

class MedicalRecordUpdate(BaseModel):

    chief_complaint: str | None = None

    history_present_illness: str | None = None

    past_medical_history: str | None = None

    family_history: str | None = None

    allergies: str | None = None

    current_medications: str | None = None

    physical_examination: str | None = None

    diagnosis: str | None = None

    treatment_plan: str | None = None

    notes: str | None = None


# ==========================================================
# Response
# ==========================================================

class MedicalRecordResponse(MedicalRecordBase):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    record_number: str

    created_by_id: uuid.UUID

    created_at: datetime

    updated_at: datetime

    deleted_at: datetime | None = None


# ==========================================================
# List Response
# ==========================================================

class MedicalRecordListResponse(BaseModel):

    total: int

    items: list[MedicalRecordResponse]


# ==========================================================
# Message
# ==========================================================

class MedicalRecordMessage(BaseModel):

    message: str