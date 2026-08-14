"""
Medical Record Repository

Handles all database operations related to Medical Records.
"""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.medical_records.models import MedicalRecord


class MedicalRecordRepository(
    BaseRepository[MedicalRecord],
):
    """
    Repository for MedicalRecord model.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session,
            MedicalRecord,
        )

    # ==========================================================
    # Create
    # ==========================================================

    async def create_record(
        self,
        record: MedicalRecord,
    ) -> MedicalRecord:

        return await self.add(record)

    # ==========================================================
    # Read
    # ==========================================================

    async def get_by_uuid(
        self,
        record_id: uuid.UUID,
    ) -> MedicalRecord | None:

        stmt = (
            select(MedicalRecord)
            .where(
                MedicalRecord.id == record_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_record_number(
        self,
        record_number: str,
    ) -> MedicalRecord | None:

        stmt = (
            select(MedicalRecord)
            .where(
                MedicalRecord.record_number == record_number,
                MedicalRecord.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_last_record_number(
        self,
    ) -> str | None:

        stmt = (
            select(
                MedicalRecord.record_number,
            )
            .order_by(
                desc(
                    MedicalRecord.record_number,
                )
            )
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[MedicalRecord]:

        stmt = (
            select(MedicalRecord)
            .where(
                MedicalRecord.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(stmt)

        return list(
            result.scalars().all()
        )

    async def get_by_patient(
        self,
        patient_id: uuid.UUID,
    ) -> list[MedicalRecord]:

        stmt = (
            select(MedicalRecord)
            .where(
                MedicalRecord.patient_id == patient_id,
                MedicalRecord.deleted_at.is_(None),
            )
            .order_by(
                MedicalRecord.created_at.desc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(
            result.scalars().all()
        )

    async def total_count(
        self,
    ) -> int:

        stmt = (
            select(func.count())
            .select_from(
                MedicalRecord,
            )
            .where(
                MedicalRecord.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return int(
            result.scalar_one()
        )

    # ==========================================================
    # Update
    # ==========================================================

    async def update_record(
        self,
        record: MedicalRecord,
        **fields,
    ) -> MedicalRecord:

        for key, value in fields.items():
            if value is not None:
                setattr(
                    record,
                    key,
                    value,
                )

        await self.flush()
        await self.refresh(record)

        return record

    # ==========================================================
    # Soft Delete
    # ==========================================================

    async def soft_delete(
        self,
        record: MedicalRecord,
    ) -> MedicalRecord:

        from datetime import UTC, datetime

        record.deleted_at = datetime.now(
            UTC,
        )

        await self.flush()
        await self.refresh(record)

        return record