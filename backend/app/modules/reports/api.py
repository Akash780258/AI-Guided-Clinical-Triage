"""
Reports API
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.modules.reports.dependencies import (
    get_reports_service,
)
from app.modules.reports.schemas import DashboardReport
from app.modules.reports.service import ReportsService

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get(
    "/dashboard",
    response_model=DashboardReport,
)
async def dashboard_report(
    service: ReportsService = Depends(
        get_reports_service,
    ),
):
    return await service.dashboard_report()