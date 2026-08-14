"""
Appointment Model

Represents an appointment between a patient and a doctor.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.mixins import TimestampMixin


# ==========================================================
# Appointment Status
# ==========================================================

from enum import Enum as PyEnum


class AppointmentStatus(str, PyEnum):
    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    IN_CONSULTATION = "IN_CONSULTATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


# ==========================================================
# Appointment Model
# ==========================================================


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"

    # ======================================================
    # Primary Key
    # ======================================================

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ======================================================
    # Appointment Number
    # ======================================================

    appointment_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    # ======================================================
    # Relationships
    # ======================================================

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False,
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False,
    )

    patient = relationship(
        "Patient",
        lazy="joined",
    )

    doctor = relationship(
        "Doctor",
        lazy="joined",
    )

    # ======================================================
    # Appointment Details
    # ======================================================

    appointment_date: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
    )

    start_time: Mapped[datetime.time] = mapped_column(
        Time,
        nullable=False,
    )

    end_time: Mapped[datetime.time] = mapped_column(
        Time,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ======================================================
    # Audit
    # ======================================================

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
    __all__ = [
    "User",
    "Patient",
    "Doctor",
    "Appointment",
]