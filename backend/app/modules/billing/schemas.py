"""
Billing Schemas

Pydantic models for Billing APIs.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ==========================================================
# Billing Status
# ==========================================================

class BillingStatus(str, Enum):
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


# ==========================================================
# Payment Method
# ==========================================================

class PaymentMethod(str, Enum):
    CASH = "CASH"
    CARD = "CARD"
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"
    INSURANCE = "INSURANCE"


# ==========================================================
# Base
# ==========================================================

class BillingBase(BaseModel):

    patient_id: uuid.UUID

    appointment_id: uuid.UUID

    subtotal: float = Field(ge=0)

    tax: float = Field(default=0, ge=0)

    discount: float = Field(default=0, ge=0)

    payment_method: PaymentMethod = PaymentMethod.CASH

    notes: str | None = None


# ==========================================================
# Create
# ==========================================================

class BillingCreate(BillingBase):
    pass


# ==========================================================
# Update
# ==========================================================

class BillingUpdate(BaseModel):

    subtotal: float | None = Field(default=None, ge=0)

    tax: float | None = Field(default=None, ge=0)

    discount: float | None = Field(default=None, ge=0)

    payment_method: PaymentMethod | None = None

    status: BillingStatus | None = None

    notes: str | None = None


# ==========================================================
# Response
# ==========================================================

class BillingResponse(BillingBase):

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID

    bill_number: str

    total: float

    status: BillingStatus

    created_by_id: uuid.UUID

    created_at: datetime

    updated_at: datetime

    deleted_at: datetime | None = None


# ==========================================================
# List Response
# ==========================================================

class BillingListResponse(BaseModel):

    total: int

    items: list[BillingResponse]


# ==========================================================
# Message
# ==========================================================

class BillingMessage(BaseModel):

    message: str