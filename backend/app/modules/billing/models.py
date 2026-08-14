"""
Billing Model

Represents patient billing and payments.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base
from app.database.mixins import TimestampMixin


# ==========================================================
# Billing Status
# ==========================================================

class BillingStatus(str, PyEnum):
    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


# ==========================================================
# Payment Method
# ==========================================================

class PaymentMethod(str, PyEnum):
    CASH = "CASH"
    CARD = "CARD"
    UPI = "UPI"
    BANK_TRANSFER = "BANK_TRANSFER"
    INSURANCE = "INSURANCE"


# ==========================================================
# Billing Model
# ==========================================================

class Billing(Base, TimestampMixin):
    __tablename__ = "billings"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Bill Number
    # ==========================================================

    bill_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    # ==========================================================
    # Relationships
    # ==========================================================

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False,
    )

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("appointments.id"),
        nullable=False,
    )

    patient = relationship(
        "Patient",
        lazy="joined",
    )

    appointment = relationship(
        "Appointment",
        lazy="joined",
    )

    # ==========================================================
    # Billing Details
    # ==========================================================

    subtotal: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    tax: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    discount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    total: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    status: Mapped[BillingStatus] = mapped_column(
        Enum(BillingStatus),
        default=BillingStatus.PENDING,
        nullable=False,
    )

    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod),
        default=PaymentMethod.CASH,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ==========================================================
    # Audit
    # ==========================================================

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    created_by = relationship(
        "User",
        lazy="joined",
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )