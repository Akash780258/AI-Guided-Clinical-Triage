"""
Patient Repository

Handles all database operations related to Patient.
"""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.patients.models import Patient


class PatientRepository(BaseRepository[Patient]):
    """
    Repository for Patient model.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(session, Patient)

    # ==========================================================
    # Create
    # ==========================================================

    async def create_patient(
        self,
        patient: Patient,
    ) -> Patient:
        return await self.add(patient)

    # ==========================================================
    # Read
    # ==========================================================

    async def get_by_uuid(
        self,
        patient_id: uuid.UUID,
    ) -> Patient | None:

        stmt = (
            select(Patient)
            .where(
                Patient.id == patient_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_patient_number(
        self,
        patient_number: str,
    ) -> Patient | None:

        stmt = (
            select(Patient)
            .where(
                Patient.patient_number == patient_number,
                Patient.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_last_patient_number(
        self,
    ) -> str | None:
        """
        Returns the highest patient number,
        including soft-deleted patients.
        """

        stmt = (
            select(Patient.patient_number)
            .order_by(desc(Patient.patient_number))
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

    async def search(
        self,
        *,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Patient]:

        stmt = (
            select(Patient)
            .where(
                Patient.deleted_at.is_(None),
                or_(
                    Patient.patient_number.ilike(f"%{query}%"),
                    Patient.first_name.ilike(f"%{query}%"),
                    Patient.last_name.ilike(f"%{query}%"),
                    Patient.phone.ilike(f"%{query}%"),
                    Patient.email.ilike(f"%{query}%"),
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
    ) -> list[Patient]:

        stmt = (
            select(Patient)
            .where(
                Patient.deleted_at.is_(None),
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
            .select_from(Patient)
            .where(
                Patient.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return int(result.scalar_one())

    # ==========================================================
    # Update
    # ==========================================================

    async def update_patient(
        self,
        patient: Patient,
        **fields,
    ) -> Patient:
        """
        Update patient fields and refresh the ORM object.
        """

        for key, value in fields.items():
            if value is not None:
                setattr(patient, key, value)

        await self.flush()
        await self.refresh(patient)

        return patient

    # ==========================================================
    # Soft Delete
    # ==========================================================

    async def soft_delete(
        self,
        patient: Patient,
    ) -> Patient:

        from datetime import UTC, datetime

        patient.deleted_at = datetime.now(UTC)

        await self.flush()
        await self.refresh(patient)

        return patient