"""
Reports Repository
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.models import Appointment
from app.modules.billing.models import Billing
from app.modules.doctors.models import Doctor
from app.modules.patients.models import Patient
from app.modules.prescriptions.models import Prescription


class ReportsRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def dashboard_report(self):

        patients = await self.db.scalar(
            select(func.count(Patient.id))
        ) or 0

        doctors = await self.db.scalar(
            select(func.count(Doctor.id))
        ) or 0

        appointments = await self.db.scalar(
            select(func.count(Appointment.id))
        ) or 0

        prescriptions = await self.db.scalar(
            select(func.count(Prescription.id))
        ) or 0

        bills = await self.db.scalar(
            select(func.count(Billing.id))
        ) or 0

        revenue = await self.db.scalar(
            select(func.coalesce(func.sum(Billing.total), 0))
        ) or 0

        return {
            "total_patients": patients,
            "total_doctors": doctors,
            "total_appointments": appointments,
            "total_prescriptions": prescriptions,
            "total_bills": bills,
            "total_revenue": float(revenue),
        }