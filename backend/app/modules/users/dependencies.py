"""
Users Dependencies
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.users.repository import UserManagementRepository
from app.modules.users.service import UserManagementService


def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserManagementRepository:
    return UserManagementRepository(db)


def get_uow(
    db: AsyncSession = Depends(get_db),
) -> UnitOfWork:
    return UnitOfWork(db)


def get_user_service(
    repository: UserManagementRepository = Depends(
        get_user_repository
    ),
    uow: UnitOfWork = Depends(get_uow),
) -> UserManagementService:

    return UserManagementService(
        repository=repository,
        uow=uow,
    )