"""
Doctor Model

Represents a doctor in the AGCT system.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import Gender
from app.database.base import Base
from app.database.mixins import TimestampMixin


class Doctor(Base, TimestampMixin):
    __tablename__ = "doctors"

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

    doctor_number: Mapped[str] = mapped_column(
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
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    # ==========================================================
    # Professional Information
    # ==========================================================

    department: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    specialization: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    qualification: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    experience_years: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    license_number: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    consultation_fee: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    # ==========================================================
    # Profile
    # ==========================================================

    profile_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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