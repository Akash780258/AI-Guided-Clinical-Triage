"""
Pharmacy Dependencies

Dependency injection for Pharmacy module.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.pharmacy.repository import (
    PharmacyRepository,
)
from app.modules.pharmacy.service import (
    PharmacyService,
)


# ==========================================================
# Repository
# ==========================================================

def get_pharmacy_repository(
    db: AsyncSession = Depends(get_db),
) -> PharmacyRepository:
    return PharmacyRepository(db)


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

def get_pharmacy_service(
    repository: PharmacyRepository = Depends(
        get_pharmacy_repository,
    ),
    uow: UnitOfWork = Depends(get_uow),
) -> PharmacyService:

    return PharmacyService(
        repository=repository,
        uow=uow,
    )