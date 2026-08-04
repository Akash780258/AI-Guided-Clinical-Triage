"""
Patient Dependencies

Dependency injection for:

- Repository
- Service
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.patients.repository import PatientRepository
from app.modules.patients.service import PatientService


# ==========================================================
# Repository
# ==========================================================

def get_patient_repository(
    db: AsyncSession = Depends(get_db),
) -> PatientRepository:
    """
    Returns PatientRepository.
    """
    return PatientRepository(db)


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

def get_patient_service(
    repository: PatientRepository = Depends(
        get_patient_repository,
    ),
    uow: UnitOfWork = Depends(get_uow),
) -> PatientService:
    """
    Returns PatientService.
    """
    return PatientService(
        repository=repository,
        uow=uow,
    )