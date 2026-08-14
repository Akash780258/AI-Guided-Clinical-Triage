"""
Reports Service
"""

from __future__ import annotations

from app.modules.reports.repository import ReportsRepository
from app.modules.reports.schemas import DashboardReport


class ReportsService:

    def __init__(
        self,
        repository: ReportsRepository,
    ):
        self.repository = repository

    async def dashboard_report(
        self,
    ) -> DashboardReport:

        data = await self.repository.dashboard_report()

        return DashboardReport(**data)