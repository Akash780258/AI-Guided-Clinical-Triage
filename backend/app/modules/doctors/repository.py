"""
Doctor Repository

Handles all database operations related to Doctor.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.doctors.models import Doctor


class DoctorRepository(BaseRepository[Doctor]):
    """
    Repository for Doctor model.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(session, Doctor)

    # ==========================================================
    # Create
    # ==========================================================

    async def create_doctor(
        self,
        doctor: Doctor,
    ) -> Doctor:
        return await self.add(doctor)

    # ==========================================================
    # Read
    # ==========================================================

    async def get_by_uuid(
        self,
        doctor_id: uuid.UUID,
    ) -> Doctor | None:

        stmt = (
            select(Doctor)
            .where(
                Doctor.id == doctor_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_doctor_number(
        self,
        doctor_number: str,
    ) -> Doctor | None:

        stmt = (
            select(Doctor)
            .where(
                Doctor.doctor_number == doctor_number,
                Doctor.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_last_doctor_number(
        self,
    ) -> str | None:

        stmt = (
            select(Doctor.doctor_number)
            .order_by(Doctor.doctor_number.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def exists_by_phone(
        self,
        phone: str,
    ) -> bool:

        return await self.exists(
            phone=phone,
            deleted_at=None,
        )

    async def exists_by_email(
        self,
        email: str,
    ) -> bool:

        return await self.exists(
            email=email,
            deleted_at=None,
        )

    async def exists_by_license(
        self,
        license_number: str,
    ) -> bool:

        return await self.exists(
            license_number=license_number,
            deleted_at=None,
        )

    async def search(
        self,
        *,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Doctor]:

        stmt = (
            select(Doctor)
            .where(
                Doctor.deleted_at.is_(None),
                or_(
                    Doctor.doctor_number.ilike(f"%{query}%"),
                    Doctor.first_name.ilike(f"%{query}%"),
                    Doctor.last_name.ilike(f"%{query}%"),
                    Doctor.department.ilike(f"%{query}%"),
                    Doctor.specialization.ilike(f"%{query}%"),
                    Doctor.phone.ilike(f"%{query}%"),
                    Doctor.email.ilike(f"%{query}%"),
                ),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Doctor]:

        stmt = (
            select(Doctor)
            .where(
                Doctor.deleted_at.is_(None),
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
            .select_from(Doctor)
            .where(
                Doctor.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return int(result.scalar_one())

    # ==========================================================
    # Update
    # ==========================================================

    async def update_doctor(
        self,
        doctor: Doctor,
        **fields,
    ) -> Doctor:

        for key, value in fields.items():
            if value is not None:
                setattr(doctor, key, value)

        await self.flush()
        await self.refresh(doctor)

        return doctor

    # ==========================================================
    # Soft Delete
    # ==========================================================

    async def soft_delete(
        self,
        doctor: Doctor,
    ) -> Doctor:

        from datetime import UTC, datetime

        doctor.deleted_at = datetime.now(UTC)

        await self.flush()
        await self.refresh(doctor)

        return doctor