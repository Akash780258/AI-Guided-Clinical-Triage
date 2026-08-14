"""
Dashboard Service

Business logic for dashboard analytics.
"""

from __future__ import annotations

import uuid

from app.core.exceptions import ResourceNotFoundException
from app.database.unit_of_work import UnitOfWork
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.schemas import (
    AdminDashboardResponse,
    BillingDashboardResponse,
    DoctorDashboardResponse,
    LaboratoryDashboardResponse,
    ReceptionDashboardResponse,
)


class DashboardService:
    """
    Dashboard business logic.
    """

    def __init__(
        self,
        repository: DashboardRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Admin Dashboard
    # ==========================================================

    async def admin_dashboard(
        self,
    ) -> AdminDashboardResponse:

        return AdminDashboardResponse(
            total_patients=await self.repository.total_patients(),
            total_doctors=await self.repository.total_doctors(),
            total_appointments=await self.repository.total_appointments(),
            today_appointments=await self.repository.today_appointments(),
            pending_lab_tests=await self.repository.pending_lab_tests(),
            active_prescriptions=await self.repository.active_prescriptions(),
            pending_bills=await self.repository.pending_bills(),
            total_revenue=await self.repository.total_revenue(),
        )

    # ==========================================================
    # Doctor Dashboard
    # ==========================================================

    async def doctor_dashboard(
        self,
        doctor_id: uuid.UUID,
    ) -> DoctorDashboardResponse:

        return DoctorDashboardResponse(
            today_appointments=(
                await self.repository.doctor_today_appointments(
                    doctor_id,
                )
            ),
            total_patients=(
                await self.repository.doctor_total_patients(
                    doctor_id,
                )
            ),
            pending_lab_results=(
                await self.repository.doctor_pending_lab_results(
                    doctor_id,
                )
            ),
            active_prescriptions=(
                await self.repository.doctor_active_prescriptions(
                    doctor_id,
                )
            ),
        )

    # ==========================================================
    # Doctor Dashboard — Authenticated Doctor
    # ==========================================================

    async def doctor_dashboard_me(
        self,
        email: str,
    ) -> DoctorDashboardResponse:
        """
        Resolve the Doctor using the authenticated user's email
        and return that Doctor's dashboard statistics.

        The frontend does not provide a Doctor ID.
        """

        doctor_id = (
            await self.repository.get_doctor_id_by_email(
                email,
            )
        )

        if doctor_id is None:
            raise ResourceNotFoundException(
                "Doctor",
            )

        return await self.doctor_dashboard(
            doctor_id,
        )

    # ==========================================================
    # Reception Dashboard
    # ==========================================================

    async def reception_dashboard(
        self,
    ) -> ReceptionDashboardResponse:

        today = await self.repository.today_appointments()

        return ReceptionDashboardResponse(
            today_queue=today,
            waiting=today,
            completed=0,
        )

    # ==========================================================
    # Laboratory Dashboard
    # ==========================================================

    async def laboratory_dashboard(
        self,
    ) -> LaboratoryDashboardResponse:

        return LaboratoryDashboardResponse(
            pending_tests=(
                await self.repository.pending_lab_tests()
            ),
            completed_today=(
                await self.repository.completed_lab_today()
            ),
        )

    # ==========================================================
    # Billing Dashboard
    # ==========================================================

    async def billing_dashboard(
        self,
    ) -> BillingDashboardResponse:

        return BillingDashboardResponse(
            pending_bills=(
                await self.repository.pending_bills()
            ),
            paid_bills=(
                await self.repository.paid_bills()
            ),
            total_revenue=(
                await self.repository.total_revenue()
            ),
        )