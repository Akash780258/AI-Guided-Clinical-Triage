"""
Appointment Dependencies

Dependency injection for Appointment module.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork

from app.modules.appointments.repository import (
    AppointmentRepository,
)
from app.modules.appointments.service import (
    AppointmentService,
)


# ==========================================================
# Repository
# ==========================================================

def get_appointment_repository(
    db: AsyncSession = Depends(get_db),
) -> AppointmentRepository:
    """
    Returns AppointmentRepository.
    """
    return AppointmentRepository(db)


# ==========================================================
# Unit Of Work
# ==========================================================

def get_appointment_uow(
    db: AsyncSession = Depends(get_db),
) -> UnitOfWork:
    """
    Returns UnitOfWork.
    """
    return UnitOfWork(db)


# ==========================================================
# Appointment Service
# ==========================================================

def get_appointment_service(
    repository: AppointmentRepository = Depends(
        get_appointment_repository,
    ),
    uow: UnitOfWork = Depends(
        get_appointment_uow,
    ),
) -> AppointmentService:
    """
    Returns AppointmentService.
    """
    return AppointmentService(
        repository=repository,
        uow=uow,
    )