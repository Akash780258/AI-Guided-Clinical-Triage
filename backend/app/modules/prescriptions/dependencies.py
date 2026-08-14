"""
Prescription Dependencies

Dependency injection for Prescription module.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.prescriptions.repository import (
    PrescriptionRepository,
)
from app.modules.prescriptions.service import (
    PrescriptionService,
)


# ==========================================================
# Repository
# ==========================================================

def get_prescription_repository(
    db: AsyncSession = Depends(get_db),
) -> PrescriptionRepository:
    return PrescriptionRepository(db)


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

def get_prescription_service(
    repository: PrescriptionRepository = Depends(
        get_prescription_repository,
    ),
    uow: UnitOfWork = Depends(get_uow),
) -> PrescriptionService:

    return PrescriptionService(
        repository=repository,
        uow=uow,
    )