"""
Prescription Schemas

Pydantic models for Prescription APIs.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Prescription Item
# ==========================================================

class PrescriptionItemBase(BaseModel):

    medicine_name: str = Field(
        min_length=2,
        max_length=200,
    )

    dosage: str

    frequency: str

    duration: str

    route: str

    instructions: str | None = None

    quantity: int = Field(
        ge=1,
    )


class PrescriptionItemCreate(
    PrescriptionItemBase,
):
    pass


class PrescriptionItemResponse(
    PrescriptionItemBase,
):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID


# ==========================================================
# Prescription
# ==========================================================

class PrescriptionBase(BaseModel):

    medical_record_id: uuid.UUID

    patient_id: uuid.UUID

    doctor_id: uuid.UUID

    notes: str | None = None


class PrescriptionCreate(
    PrescriptionBase,
):

    items: list[
        PrescriptionItemCreate
    ]


class PrescriptionUpdate(BaseModel):

    notes: str | None = None


class PrescriptionResponse(
    PrescriptionBase,
):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    prescription_number: str

    created_by_id: uuid.UUID

    created_at: datetime

    updated_at: datetime

    deleted_at: datetime | None = None

    items: list[
        PrescriptionItemResponse
    ]


# ==========================================================
# List Response
# ==========================================================

class PrescriptionListResponse(
    BaseModel,
):

    total: int

    items: list[
        PrescriptionResponse
    ]


# ==========================================================
# Message
# ==========================================================

class PrescriptionMessage(
    BaseModel,
):

    message: str