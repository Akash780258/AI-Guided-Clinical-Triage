"""
Doctor Dependencies
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.doctors.repository import DoctorRepository
from app.modules.doctors.service import DoctorService


def get_doctor_repository(
    session: AsyncSession = Depends(get_db),
) -> DoctorRepository:
    return DoctorRepository(session)


def get_doctor_service(
    repository: DoctorRepository = Depends(
        get_doctor_repository,
    ),
    session: AsyncSession = Depends(get_db),
) -> DoctorService:
    return DoctorService(
        repository=repository,
        uow=UnitOfWork(session),
    )