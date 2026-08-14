"""
Laboratory Repository
"""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.laboratory.models import LabResult, LabTest


class LaboratoryRepository(BaseRepository[LabTest]):

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session,
            LabTest,
        )

    # ==========================================================
    # Lab Tests
    # ==========================================================

    async def create_test(
        self,
        test: LabTest,
    ) -> LabTest:

        return await self.add(test)

    async def get_test(
        self,
        test_id: uuid.UUID,
    ) -> LabTest | None:

        stmt = (
            select(LabTest)
            .where(
                LabTest.id == test_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_last_test_number(
        self,
    ) -> str | None:

        stmt = (
            select(
                LabTest.test_number,
            )
            .order_by(
                desc(
                    LabTest.test_number,
                )
            )
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> list[LabTest]:

        stmt = (
            select(LabTest)
            .where(
                LabTest.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def total_count(
        self,
    ) -> int:

        stmt = (
            select(func.count())
            .select_from(LabTest)
            .where(
                LabTest.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return int(result.scalar_one())

    async def update_test(
        self,
        test: LabTest,
        **fields,
    ) -> LabTest:

        for key, value in fields.items():
            if value is not None:
                setattr(test, key, value)

        await self.flush()
        await self.refresh(test)

        return test

    # ==========================================================
    # Results
    # ==========================================================

    async def create_result(
        self,
        result_model: LabResult,
    ) -> LabResult:

        self.session.add(result_model)

        await self.flush()

        await self.refresh(result_model)

        return result_model

    async def get_result(
        self,
        test_id: uuid.UUID,
    ) -> LabResult | None:

        stmt = (
            select(LabResult)
            .where(
                LabResult.lab_test_id == test_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def soft_delete(
        self,
        test: LabTest,
    ):

        from datetime import UTC, datetime

        test.deleted_at = datetime.now(UTC)

        await self.flush()

        await self.refresh(test)