"""
Dashboard API

Provides dashboard endpoints for:
- Admin
- Doctor
- Reception
- Laboratory
- Billing
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.core.security import AdminDoctorReception, DoctorOnly
from app.modules.auth.models import User
from app.modules.dashboard.dependencies import get_dashboard_service
from app.modules.dashboard.schemas import (
    AdminDashboardResponse,
    BillingDashboardResponse,
    DoctorDashboardResponse,
    LaboratoryDashboardResponse,
    ReceptionDashboardResponse,
)
from app.modules.dashboard.service import DashboardService


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(AdminDoctorReception)],
)


# ==========================================================
# Admin Dashboard
# ==========================================================


@router.get(
    "/admin",
    response_model=AdminDashboardResponse,
)
async def admin_dashboard(
    service: DashboardService = Depends(
        get_dashboard_service,
    ),
):
    return await service.admin_dashboard()


# ==========================================================
# Doctor Dashboard — Authenticated Doctor
# ==========================================================
#
# IMPORTANT:
# This route MUST appear before /doctor/{doctor_id}.
#
# Otherwise FastAPI may try to interpret "me" as a UUID.
#
# ==========================================================


@router.get(
    "/doctor/me",
    response_model=DoctorDashboardResponse,
)
async def doctor_dashboard_me(
    current_user: User = Depends(DoctorOnly),
    service: DashboardService = Depends(
        get_dashboard_service,
    ),
):
    """
    Return dashboard statistics for the currently
    authenticated Doctor.

    The frontend does NOT provide a Doctor ID.

    The backend resolves the Doctor using:

        current_user.email
            ↓
        Doctor.email
            ↓
        Doctor.id
    """

    return await service.doctor_dashboard_me(
        current_user.email,
    )


# ==========================================================
# Doctor Dashboard — Explicit Doctor ID
# ==========================================================


@router.get(
    "/doctor/{doctor_id}",
    response_model=DoctorDashboardResponse,
)
async def doctor_dashboard(
    doctor_id: uuid.UUID,
    service: DashboardService = Depends(
        get_dashboard_service,
    ),
):
    return await service.doctor_dashboard(
        doctor_id,
    )


# ==========================================================
# Reception Dashboard
# ==========================================================


@router.get(
    "/reception",
    response_model=ReceptionDashboardResponse,
)
async def reception_dashboard(
    service: DashboardService = Depends(
        get_dashboard_service,
    ),
):
    return await service.reception_dashboard()


# ==========================================================
# Laboratory Dashboard
# ==========================================================


@router.get(
    "/laboratory",
    response_model=LaboratoryDashboardResponse,
)
async def laboratory_dashboard(
    service: DashboardService = Depends(
        get_dashboard_service,
    ),
):
    return await service.laboratory_dashboard()


# ==========================================================
# Billing Dashboard
# ==========================================================


@router.get(
    "/billing",
    response_model=BillingDashboardResponse,
)
async def billing_dashboard(
    service: DashboardService = Depends(
        get_dashboard_service,
    ),
):
    return await service.billing_dashboard()