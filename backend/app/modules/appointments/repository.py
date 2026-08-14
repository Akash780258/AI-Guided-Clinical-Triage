"""
Appointment Repository

Handles all database operations related to Appointment.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.appointments.models import Appointment


class AppointmentRepository(BaseRepository[Appointment]):
    """
    Repository for Appointment model.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(session, Appointment)

    # ==========================================================
    # Create
    # ==========================================================

    async def create_appointment(
        self,
        appointment: Appointment,
    ) -> Appointment:
        return await self.add(appointment)

    # ==========================================================
    # Read
    # ==========================================================

    async def get_by_uuid(
        self,
        appointment_id: uuid.UUID,
    ) -> Appointment | None:

        stmt = (
            select(Appointment)
            .where(
                Appointment.id == appointment_id,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_appointment_number(
        self,
        appointment_number: str,
    ) -> Appointment | None:

        stmt = (
            select(Appointment)
            .where(
                Appointment.appointment_number == appointment_number,
                Appointment.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_last_appointment_number(
        self,
    ) -> str | None:
        """
        Returns the latest appointment number,
        including soft deleted appointments.
        """

        stmt = (
            select(Appointment.appointment_number)
            .order_by(desc(Appointment.appointment_number))
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Appointment]:

        stmt = (
            select(Appointment)
            .where(
                Appointment.deleted_at.is_(None),
            )
            .order_by(
                Appointment.appointment_date.desc(),
                Appointment.start_time.asc(),
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
            .select_from(Appointment)
            .where(
                Appointment.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return int(result.scalar_one())

    async def get_by_doctor(
        self,
        doctor_id: uuid.UUID,
    ) -> list[Appointment]:

        stmt = (
            select(Appointment)
            .where(
                Appointment.doctor_id == doctor_id,
                Appointment.deleted_at.is_(None),
            )
            .order_by(
                Appointment.appointment_date.desc(),
                Appointment.start_time.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_by_patient(
        self,
        patient_id: uuid.UUID,
    ) -> list[Appointment]:

        stmt = (
            select(Appointment)
            .where(
                Appointment.patient_id == patient_id,
                Appointment.deleted_at.is_(None),
            )
            .order_by(
                Appointment.appointment_date.desc(),
                Appointment.start_time.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_today(
        self,
        appointment_date: date,
    ) -> list[Appointment]:

        stmt = (
            select(Appointment)
            .where(
                Appointment.appointment_date == appointment_date,
                Appointment.deleted_at.is_(None),
            )
            .order_by(
                Appointment.start_time.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    # ==========================================================
    # Update
    # ==========================================================

    async def update_appointment(
        self,
        appointment: Appointment,
        **fields,
    ) -> Appointment:
        """
        Update appointment fields and refresh ORM object.
        """

        for key, value in fields.items():
            if value is not None:
                setattr(appointment, key, value)

        await self.flush()
        await self.refresh(appointment)

        return appointment

    # ==========================================================
    # Soft Delete
    # ==========================================================

    async def soft_delete(
        self,
        appointment: Appointment,
    ) -> Appointment:

        from datetime import UTC, datetime

        appointment.deleted_at = datetime.now(UTC)

        await self.flush()
        await self.refresh(appointment)

        return appointment