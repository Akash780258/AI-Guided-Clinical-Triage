"""
Doctor Schemas

Pydantic models for Doctor APIs.
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

from app.common.enums import Gender


# ==========================================================
# Base
# ==========================================================

class DoctorBase(BaseModel):
    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    date_of_birth: date

    gender: Gender

    phone: str = Field(
        min_length=8,
        max_length=20,
    )

    email: EmailStr

    department: str = Field(
        min_length=2,
        max_length=100,
    )

    specialization: str = Field(
        min_length=2,
        max_length=150,
    )

    qualification: str = Field(
        min_length=2,
        max_length=200,
    )

    experience_years: int = Field(
        ge=0,
    )

    license_number: str = Field(
        min_length=2,
        max_length=100,
    )

    consultation_fee: float = Field(
        ge=0,
    )

    profile_image_url: str | None = None

    is_available: bool = True


# ==========================================================
# Create
# ==========================================================

class DoctorCreate(DoctorBase):
    pass


# ==========================================================
# Update
# ==========================================================

class DoctorUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = None
    email: EmailStr | None = None
    department: str | None = None
    specialization: str | None = None
    qualification: str | None = None
    experience_years: int | None = None
    license_number: str | None = None
    consultation_fee: float | None = None
    profile_image_url: str | None = None
    is_available: bool | None = None


# ==========================================================
# Response
# ==========================================================

class DoctorResponse(DoctorBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    doctor_number: str

    created_by_id: uuid.UUID

    created_at: datetime

    updated_at: datetime

    deleted_at: datetime | None = None


# ==========================================================
# List Response
# ==========================================================

class DoctorListResponse(BaseModel):
    total: int
    items: list[DoctorResponse]


# ==========================================================
# Message Response
# ==========================================================

class DoctorMessage(BaseModel):
    message: str