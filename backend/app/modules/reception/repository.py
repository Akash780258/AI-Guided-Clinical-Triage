"""
Reception Repository

Workflow queries used by the Reception module.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.models import (
    Appointment,
    AppointmentStatus,
)


class ReceptionRepository:
    """
    Repository for Reception workflow.
    Uses the Appointment table as the source of truth.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    # ==========================================================
    # Today's Queue
    # ==========================================================

    async def get_today_queue(
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

        return list(result.scalars().unique().all())

    # ==========================================================
    # Waiting Queue
    # ==========================================================

    async def get_waiting_queue(
        self,
        appointment_date: date,
    ) -> list[Appointment]:

        stmt = (
            select(Appointment)
            .where(
                Appointment.appointment_date == appointment_date,
                Appointment.status == AppointmentStatus.WAITING,
                Appointment.deleted_at.is_(None),
            )
            .order_by(
                Appointment.start_time.asc(),
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().unique().all())

    # ==========================================================
    # Appointment By ID
    # ==========================================================

    async def get_appointment(
        self,
        appointment_id,
    ) -> Appointment | None:

        stmt = (
            select(Appointment)
            .where(
                Appointment.id == appointment_id,
                Appointment.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    # ==========================================================
    # Update Status
    # ==========================================================

    async def update_status(
        self,
        appointment: Appointment,
        status: AppointmentStatus,
    ) -> Appointment:

        appointment.status = status

        await self.session.flush()
        await self.session.refresh(appointment)

        return appointment