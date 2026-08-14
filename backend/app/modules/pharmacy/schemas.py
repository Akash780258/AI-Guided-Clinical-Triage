"""
Pharmacy Schemas

Pydantic models for Pharmacy APIs.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Medicine Category
# ==========================================================

class MedicineCategory(str, Enum):
    TABLET = "TABLET"
    CAPSULE = "CAPSULE"
    SYRUP = "SYRUP"
    INJECTION = "INJECTION"
    OINTMENT = "OINTMENT"
    DROPS = "DROPS"
    INHALER = "INHALER"
    POWDER = "POWDER"
    OTHER = "OTHER"


# ==========================================================
# Base
# ==========================================================

class MedicineBase(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=200,
    )

    generic_name: str | None = None

    manufacturer: str | None = None

    category: MedicineCategory

    strength: str

    dosage_form: str

    unit_price: float = Field(
        ge=0,
    )

    stock_quantity: int = Field(
        ge=0,
    )

    minimum_stock: int = Field(
        ge=0,
    )

    expiry_date: date

    batch_number: str


# ==========================================================
# Create
# ==========================================================

class MedicineCreate(
    MedicineBase,
):
    pass


# ==========================================================
# Update
# ==========================================================

class MedicineUpdate(BaseModel):

    generic_name: str | None = None

    manufacturer: str | None = None

    category: MedicineCategory | None = None

    strength: str | None = None

    dosage_form: str | None = None

    unit_price: float | None = Field(
        default=None,
        ge=0,
    )

    stock_quantity: int | None = Field(
        default=None,
        ge=0,
    )

    minimum_stock: int | None = Field(
        default=None,
        ge=0,
    )

    expiry_date: date | None = None

    batch_number: str | None = None


# ==========================================================
# Response
# ==========================================================

class MedicineResponse(
    MedicineBase,
):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    medicine_code: str

    created_by_id: uuid.UUID

    created_at: datetime

    updated_at: datetime

    deleted_at: datetime | None = None


# ==========================================================
# List Response
# ==========================================================

class MedicineListResponse(
    BaseModel,
):

    total: int

    items: list[
        MedicineResponse
    ]


# ==========================================================
# Message
# ==========================================================

class MedicineMessage(
    BaseModel,
):

    message: str