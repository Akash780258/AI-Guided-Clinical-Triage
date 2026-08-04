"""
Patient Schemas

Pydantic models for Patient APIs.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from app.common.enums import (
    BloodGroup,
    Gender,
    MaritalStatus,
)


# ==========================================================
# Base
# ==========================================================

class PatientBase(BaseModel):
    first_name: str = Field(min_length=2, max_length=100)

    last_name: str = Field(min_length=2, max_length=100)

    date_of_birth: date

    gender: Gender

    phone: str = Field(
        min_length=8,
        max_length=20,
    )

    email: EmailStr | None = None

    address: str | None = None

    nationality: str | None = Field(
        default=None,
        max_length=100,
    )

    occupation: str | None = Field(
        default=None,
        max_length=100,
    )

    marital_status: MaritalStatus | None = None

    blood_group: BloodGroup | None = None

    height: float | None = Field(
        default=None,
        gt=0,
    )

    weight: float | None = Field(
        default=None,
        gt=0,
    )

    emergency_contact_name: str | None = Field(
        default=None,
        max_length=100,
    )

    emergency_contact_relationship: str | None = Field(
        default=None,
        max_length=50,
    )

    emergency_contact_phone: str | None = Field(
        default=None,
        max_length=20,
    )

    insurance_provider: str | None = Field(
        default=None,
        max_length=150,
    )

    insurance_policy_number: str | None = Field(
        default=None,
        max_length=100,
    )

    profile_image_url: str | None = None


# ==========================================================
# Create
# ==========================================================

class PatientCreate(PatientBase):
    pass


# ==========================================================
# Update
# ==========================================================

class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    nationality: str | None = None
    occupation: str | None = None
    marital_status: MaritalStatus | None = None
    blood_group: BloodGroup | None = None
    height: float | None = None
    weight: float | None = None
    emergency_contact_name: str | None = None
    emergency_contact_relationship: str | None = None
    emergency_contact_phone: str | None = None
    insurance_provider: str | None = None
    insurance_policy_number: str | None = None
    profile_image_url: str | None = None


# ==========================================================
# Response
# ==========================================================

class PatientResponse(PatientBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    patient_number: str

    created_by_id: uuid.UUID

    created_at: datetime

    updated_at: datetime

    deleted_at: datetime | None = None


# ==========================================================
# List Response
# ==========================================================

class PatientListResponse(BaseModel):
    total: int
    items: list[PatientResponse]


# ==========================================================
# Message Response
# ==========================================================

class PatientMessage(BaseModel):
    message: str