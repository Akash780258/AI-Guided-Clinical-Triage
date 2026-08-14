"""
Pharmacy Model

Represents medicines available in the hospital pharmacy.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.database.base import Base
from app.database.mixins import TimestampMixin


# ==========================================================
# Medicine Category
# ==========================================================

class MedicineCategory(str, PyEnum):
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
# Medicine Model
# ==========================================================

class Medicine(Base, TimestampMixin):
    __tablename__ = "medicines"

    # ==========================================================
    # Primary Key
    # ==========================================================

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    # ==========================================================
    # Medicine Information
    # ==========================================================

    medicine_code: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        index=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    generic_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    category: Mapped[MedicineCategory] = mapped_column(
        Enum(MedicineCategory),
        nullable=False,
    )

    strength: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    dosage_form: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # ==========================================================
    # Inventory
    # ==========================================================

    unit_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
    )

    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    minimum_stock: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    expiry_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    batch_number: Mapped[str] = mapped_column(
        String(100),
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