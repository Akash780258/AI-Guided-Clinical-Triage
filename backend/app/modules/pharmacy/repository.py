"""
Pharmacy Repository

Handles all database operations related to Medicines.
"""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.pharmacy.models import Medicine


class PharmacyRepository(BaseRepository[Medicine]):
    """
    Repository for Medicine model.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session,
            Medicine,
        )

    # ==========================================================
    # Create
    # ==========================================================

    async def create_medicine(
        self,
        medicine: Medicine,
    ) -> Medicine:

        return await self.add(
            medicine,
        )

    # ==========================================================
    # Read
    # ==========================================================

    async def get_by_uuid(
        self,
        medicine_id: uuid.UUID,
    ) -> Medicine | None:

        stmt = (
            select(Medicine)
            .where(
                Medicine.id == medicine_id,
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def get_by_code(
        self,
        medicine_code: str,
    ) -> Medicine | None:

        stmt = (
            select(Medicine)
            .where(
                Medicine.medicine_code == medicine_code,
                Medicine.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def get_last_medicine_code(
        self,
    ) -> str | None:

        stmt = (
            select(
                Medicine.medicine_code,
            )
            .order_by(
                desc(
                    Medicine.medicine_code,
                )
            )
            .limit(1)
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def search(
        self,
        *,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Medicine]:

        stmt = (
            select(Medicine)
            .where(
                Medicine.deleted_at.is_(None),
                or_(
                    Medicine.medicine_code.ilike(f"%{query}%"),
                    Medicine.name.ilike(f"%{query}%"),
                    Medicine.generic_name.ilike(f"%{query}%"),
                    Medicine.manufacturer.ilike(f"%{query}%"),
                ),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(
            stmt,
        )

        return list(
            result.scalars().all()
        )

    async def get_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Medicine]:

        stmt = (
            select(Medicine)
            .where(
                Medicine.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(
            stmt,
        )

        return list(
            result.scalars().all()
        )

    async def total_count(
        self,
    ) -> int:

        stmt = (
            select(func.count())
            .select_from(Medicine)
            .where(
                Medicine.deleted_at.is_(None),
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

    async def update_medicine(
        self,
        medicine: Medicine,
        **fields,
    ) -> Medicine:

        for key, value in fields.items():
            if value is not None:
                setattr(
                    medicine,
                    key,
                    value,
                )

        await self.flush()
        await self.refresh(
            medicine,
        )

        return medicine

    # ==========================================================
    # Soft Delete
    # ==========================================================

    async def soft_delete(
        self,
        medicine: Medicine,
    ) -> Medicine:

        from datetime import UTC, datetime

        medicine.deleted_at = datetime.now(
            UTC,
        )

        await self.flush()
        await self.refresh(
            medicine,
        )

        return medicine