"""
Dashboard Dependencies
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.dashboard.repository import DashboardRepository
from app.modules.dashboard.service import DashboardService


def get_dashboard_repository(
    db: AsyncSession = Depends(get_db),
) -> DashboardRepository:
    return DashboardRepository(db)


def get_dashboard_service(
    repository: DashboardRepository = Depends(
        get_dashboard_repository,
    ),
    uow: UnitOfWork = Depends(
        lambda db=Depends(get_db): UnitOfWork(db)
    ),
) -> DashboardService:
    return DashboardService(
        repository,
        uow,
    )