"""
Patient Model

Represents a patient in the AGCT system.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import (
    BloodGroup,
    Gender,
    MaritalStatus,
)
from app.database.base import Base
from app.database.mixins import TimestampMixin


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Basic Information
    # ==========================================================

    patient_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    gender: Mapped[Gender] = mapped_column(
        Enum(Gender),
        nullable=False,
    )

    # ==========================================================
    # Contact Information
    # ==========================================================

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    nationality: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    occupation: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    marital_status: Mapped[MaritalStatus | None] = mapped_column(
        Enum(MaritalStatus),
        nullable=True,
    )

    # ==========================================================
    # Medical Information
    # ==========================================================

    blood_group: Mapped[BloodGroup | None] = mapped_column(
        Enum(BloodGroup),
        nullable=True,
    )

    height: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    weight: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # ==========================================================
    # Emergency Contact
    # ==========================================================

    emergency_contact_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    emergency_contact_relationship: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    emergency_contact_phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    # ==========================================================
    # Insurance
    # ==========================================================

    insurance_provider: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    insurance_policy_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # ==========================================================
    # Profile
    # ==========================================================

    profile_image_url: Mapped[str | None] = mapped_column(
        String(500),
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