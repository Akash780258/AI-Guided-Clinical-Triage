"""
Dashboard Repository

Provides dashboard statistics from multiple modules.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointments.models import Appointment
from app.modules.auth.models import User
from app.modules.billing.models import Billing, BillingStatus
from app.modules.doctors.models import Doctor
from app.modules.laboratory.models import LabStatus, LabTest
from app.modules.patients.models import Patient
from app.modules.prescriptions.models import Prescription


class DashboardRepository:
    """
    Repository for dashboard analytics.
    """

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    # ==========================================================
    # Patients
    # ==========================================================

    async def total_patients(self) -> int:
        """
        Return the total number of active patients.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Patient.id)
                ).where(
                    Patient.deleted_at.is_(None),
                )
            )
        ) or 0

    # ==========================================================
    # Doctors
    # ==========================================================

    async def total_doctors(self) -> int:
        """
        Return the total number of active doctors.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Doctor.id)
                ).where(
                    Doctor.deleted_at.is_(None),
                )
            )
        ) or 0

    async def get_doctor_id_by_email(
        self,
        email: str,
    ) -> uuid.UUID | None:
        """
        Resolve the Doctor ID from the authenticated
        user's email address.
        """

        return await self.db.scalar(
            select(Doctor.id).where(
                Doctor.email == email,
                Doctor.deleted_at.is_(None),
            )
        )

    # ==========================================================
    # Appointments
    # ==========================================================

    async def total_appointments(self) -> int:
        """
        Return the total number of appointments.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Appointment.id)
                )
            )
        ) or 0

    async def today_appointments(self) -> int:
        """
        Return the total number of appointments scheduled
        for today.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Appointment.id)
                ).where(
                    Appointment.appointment_date
                    == date.today(),
                )
            )
        ) or 0

    async def doctor_today_appointments(
        self,
        doctor_id: uuid.UUID,
    ) -> int:
        """
        Count today's appointments belonging to one Doctor.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Appointment.id)
                ).where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.appointment_date
                    == date.today(),
                )
            )
        ) or 0

    async def doctor_total_patients(
        self,
        doctor_id: uuid.UUID,
    ) -> int:
        """
        Count active patients created by the authenticated
        doctor.

        Patient.created_by_id points to User.id.

        Doctor.email corresponds to User.email, so we join:

            Patient
                -> User
                -> Doctor

        This means the dashboard reflects actual patients
        created by the doctor rather than requiring an
        appointment to exist first.
        """

        result = await self.db.scalar(
            select(
                func.count(
                    func.distinct(
                        Patient.id,
                    )
                )
            )
            .select_from(Patient)
            .join(
                User,
                Patient.created_by_id == User.id,
            )
            .join(
                Doctor,
                Doctor.email == User.email,
            )
            .where(
                Doctor.id == doctor_id,
                Patient.deleted_at.is_(None),
                Doctor.deleted_at.is_(None),
            )
        )

        return int(result or 0)

    # ==========================================================
    # Laboratory
    # ==========================================================

    async def pending_lab_tests(self) -> int:
        """
        Return the total number of pending laboratory tests.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(LabTest.id)
                ).where(
                    LabTest.status == LabStatus.PENDING,
                )
            )
        ) or 0

    async def completed_lab_today(self) -> int:
        """
        Return the number of laboratory tests completed today.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(LabTest.id)
                ).where(
                    LabTest.status == LabStatus.COMPLETED,
                    func.date(
                        LabTest.completed_date,
                    ) == date.today(),
                )
            )
        ) or 0

    async def doctor_pending_lab_results(
        self,
        doctor_id: uuid.UUID,
    ) -> int:
        """
        Count pending/non-completed laboratory tests
        belonging to one Doctor.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(LabTest.id)
                ).where(
                    LabTest.doctor_id == doctor_id,
                    LabTest.status != LabStatus.COMPLETED,
                )
            )
        ) or 0

    # ==========================================================
    # Prescriptions
    # ==========================================================

    async def active_prescriptions(self) -> int:
        """
        Global prescription count used by the Admin dashboard.

        The current Prescription model does not contain a
        status field, so this counts all prescriptions.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Prescription.id)
                )
            )
        ) or 0

    async def doctor_active_prescriptions(
        self,
        doctor_id: uuid.UUID,
    ) -> int:
        """
        Count prescriptions belonging to one Doctor.

        The current Prescription model does not contain a
        status field, so this counts all prescriptions written
        by the specified Doctor.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Prescription.id)
                ).where(
                    Prescription.doctor_id == doctor_id,
                )
            )
        ) or 0

    # ==========================================================
    # Billing
    # ==========================================================

    async def pending_bills(self) -> int:
        """
        Return the total number of pending bills.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Billing.id)
                ).where(
                    Billing.status == BillingStatus.PENDING,
                )
            )
        ) or 0

    async def paid_bills(self) -> int:
        """
        Return the total number of paid bills.
        """

        return (
            await self.db.scalar(
                select(
                    func.count(Billing.id)
                ).where(
                    Billing.status == BillingStatus.PAID,
                )
            )
        ) or 0

    async def total_revenue(self) -> float:
        """
        Return total revenue from paid bills.
        """

        value = await self.db.scalar(
            select(
                func.coalesce(
                    func.sum(Billing.total),
                    0,
                )
            ).where(
                Billing.status == BillingStatus.PAID,
            )
        )

        return float(value or 0)