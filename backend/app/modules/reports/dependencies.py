"""
Reports Dependencies
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.reports.repository import ReportsRepository
from app.modules.reports.service import ReportsService


def get_reports_service(
    db: AsyncSession = Depends(get_db),
):
    repository = ReportsRepository(db)

    return ReportsService(repository)