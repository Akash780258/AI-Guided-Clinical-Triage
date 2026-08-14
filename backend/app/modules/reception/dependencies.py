"""
Reception Dependencies

Dependency injection for the Reception module.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.reception.repository import ReceptionRepository
from app.modules.reception.service import ReceptionService


# ==========================================================
# Repository
# ==========================================================

def get_reception_repository(
    db: AsyncSession = Depends(get_db),
) -> ReceptionRepository:
    """
    Returns ReceptionRepository.
    """
    return ReceptionRepository(db)


# ==========================================================
# Unit Of Work
# ==========================================================

def get_uow(
    db: AsyncSession = Depends(get_db),
) -> UnitOfWork:
    """
    Returns UnitOfWork.
    """
    return UnitOfWork(db)


# ==========================================================
# Service
# ==========================================================

def get_reception_service(
    repository: ReceptionRepository = Depends(
        get_reception_repository,
    ),
    uow: UnitOfWork = Depends(get_uow),
) -> ReceptionService:
    """
    Returns ReceptionService.
    """
    return ReceptionService(
        repository=repository,
        uow=uow,
    )