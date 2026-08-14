"""
Medical Record Model

Represents a doctor's consultation record.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
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


class MedicalRecord(Base, TimestampMixin):
    __tablename__ = "medical_records"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Record Number
    # ==========================================================

    record_number: Mapped[str] = mapped_column(
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

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctors.id"),
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

    doctor = relationship(
        "Doctor",
        lazy="joined",
    )

    appointment = relationship(
        "Appointment",
        lazy="joined",
    )

    # ==========================================================
    # Clinical Information
    # ==========================================================

    chief_complaint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    history_present_illness: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    past_medical_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    family_history: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    allergies: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    current_medications: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    physical_examination: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    diagnosis: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    treatment_plan: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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