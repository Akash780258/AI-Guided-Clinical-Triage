"""
Laboratory Dependencies
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.laboratory.repository import LaboratoryRepository
from app.modules.laboratory.service import LaboratoryService


# ==========================================================
# Repository
# ==========================================================

def get_laboratory_repository(
    db: AsyncSession = Depends(get_db),
) -> LaboratoryRepository:

    return LaboratoryRepository(db)


# ==========================================================
# Unit Of Work
# ==========================================================

def get_uow(
    db: AsyncSession = Depends(get_db),
) -> UnitOfWork:

    return UnitOfWork(db)


# ==========================================================
# Service
# ==========================================================

def get_laboratory_service(
    repository: LaboratoryRepository = Depends(
        get_laboratory_repository,
    ),
    uow: UnitOfWork = Depends(get_uow),
) -> LaboratoryService:

    return LaboratoryService(
        repository=repository,
        uow=uow,
    )