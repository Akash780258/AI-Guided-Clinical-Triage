"""
Dashboard Repository

Handles dashboard database queries.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.models import Appointment
from app.modules.doctors.models import Doctor
from app.modules.patients.models import Patient


class DashboardRepository:
    """
    Repository for dashboard statistics.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_active_patients(self) -> int:
        stmt = (
            select(func.count())
            .select_from(Patient)
            .where(Patient.deleted_at.is_(None))
        )

        result = await self.session.execute(stmt)

        return int(result.scalar() or 0)

    async def get_doctors_available(self) -> int:
        stmt = (
            select(func.count())
            .select_from(Doctor)
        )

        result = await self.session.execute(stmt)

        return int(result.scalar() or 0)

    async def get_today_appointments(self) -> int:
        today = datetime.now(UTC).date()

        stmt = (
            select(func.count())
            .select_from(Appointment)
            .where(func.date(Appointment.appointment_date) == today)
        )

        result = await self.session.execute(stmt)

        return int(result.scalar() or 0)