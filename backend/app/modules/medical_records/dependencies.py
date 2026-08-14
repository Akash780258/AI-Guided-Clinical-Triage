"""
Medical Record Dependencies

Dependency injection for Medical Record module.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.medical_records.repository import (
    MedicalRecordRepository,
)
from app.modules.medical_records.service import (
    MedicalRecordService,
)


# ==========================================================
# Repository
# ==========================================================

def get_medical_record_repository(
    db: AsyncSession = Depends(get_db),
) -> MedicalRecordRepository:
    """
    Returns MedicalRecordRepository.
    """
    return MedicalRecordRepository(db)


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

def get_medical_record_service(
    repository: MedicalRecordRepository = Depends(
        get_medical_record_repository,
    ),
    uow: UnitOfWork = Depends(get_uow),
) -> MedicalRecordService:
    """
    Returns MedicalRecordService.
    """
    return MedicalRecordService(
        repository=repository,
        uow=uow,
    )