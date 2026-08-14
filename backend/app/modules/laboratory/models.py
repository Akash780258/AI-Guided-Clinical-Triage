"""
Laboratory Models

Represents laboratory tests and results.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime,
    Enum,
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
# Lab Status
# ==========================================================

class LabStatus(str, PyEnum):
    ORDERED = "ORDERED"
    SAMPLE_COLLECTED = "SAMPLE_COLLECTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ==========================================================
# Laboratory Test
# ==========================================================

class LabTest(Base, TimestampMixin):
    __tablename__ = "lab_tests"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    test_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id"),
        nullable=False,
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("doctors.id"),
        nullable=False,
    )

    medical_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medical_records.id"),
        nullable=False,
    )

    test_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    status: Mapped[LabStatus] = mapped_column(
        Enum(LabStatus),
        default=LabStatus.ORDERED,
        nullable=False,
    )

    requested_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
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

    medical_record = relationship(
        "MedicalRecord",
        lazy="joined",
    )

    created_by = relationship(
        "User",
        lazy="joined",
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# ==========================================================
# Laboratory Result
# ==========================================================

class LabResult(Base, TimestampMixin):
    __tablename__ = "lab_results"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    lab_test_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_tests.id"),
        nullable=False,
    )

    result: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    reference_range: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    attachment_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    lab_test = relationship(
        "LabTest",
        lazy="joined",
    )