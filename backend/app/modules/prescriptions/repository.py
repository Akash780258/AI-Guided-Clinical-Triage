"""
Prescription Repository

Handles all database operations related to Prescriptions.
"""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.prescriptions.models import (
    Prescription,
    PrescriptionItem,
)


class PrescriptionRepository(
    BaseRepository[Prescription],
):
    """
    Repository for Prescription model.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session,
            Prescription,
        )

    # ==========================================================
    # Create
    # ==========================================================

    async def create_prescription(
        self,
        prescription: Prescription,
    ) -> Prescription:

        return await self.add(
            prescription,
        )

    async def add_item(
        self,
        item: PrescriptionItem,
    ) -> PrescriptionItem:

        self.session.add(item)

        await self.session.flush()

        return item

    # ==========================================================
    # Read
    # ==========================================================

    async def get_by_uuid(
        self,
        prescription_id: uuid.UUID,
    ) -> Prescription | None:

        stmt = (
            select(Prescription)
            .where(
                Prescription.id == prescription_id,
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def get_by_prescription_number(
        self,
        prescription_number: str,
    ) -> Prescription | None:

        stmt = (
            select(Prescription)
            .where(
                Prescription.prescription_number
                == prescription_number,
                Prescription.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def get_last_prescription_number(
        self,
    ) -> str | None:

        stmt = (
            select(
                Prescription.prescription_number,
            )
            .order_by(
                desc(
                    Prescription.prescription_number,
                )
            )
            .limit(1)
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Prescription]:

        stmt = (
            select(Prescription)
            .where(
                Prescription.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(
            stmt,
        )

        return list(
            result.scalars().unique().all()
        )

    async def get_by_patient(
        self,
        patient_id: uuid.UUID,
    ) -> list[Prescription]:

        stmt = (
            select(Prescription)
            .where(
                Prescription.patient_id == patient_id,
                Prescription.deleted_at.is_(None),
            )
            .order_by(
                Prescription.created_at.desc(),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return list(
            result.scalars().unique().all()
        )

    async def total_count(
        self,
    ) -> int:

        stmt = (
            select(func.count())
            .select_from(
                Prescription,
            )
            .where(
                Prescription.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return int(
            result.scalar_one()
        )

    # ==========================================================
    # Update
    # ==========================================================

    async def update_prescription(
        self,
        prescription: Prescription,
        **fields,
    ) -> Prescription:

        for key, value in fields.items():
            if value is not None:
                setattr(
                    prescription,
                    key,
                    value,
                )

        await self.flush()
        await self.refresh(
            prescription,
        )

        return prescription

    # ==========================================================
    # Soft Delete
    # ==========================================================

    async def soft_delete(
        self,
        prescription: Prescription,
    ) -> Prescription:

        from datetime import UTC, datetime

        prescription.deleted_at = datetime.now(
            UTC,
        )

        await self.flush()
        await self.refresh(
            prescription,
        )

        return prescription