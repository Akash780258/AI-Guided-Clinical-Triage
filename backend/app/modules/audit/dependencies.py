"""
Audit Dependencies
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork

from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService


def get_audit_repository(
    db: AsyncSession = Depends(get_db),
):
    return AuditRepository(db)


def get_uow(
    db: AsyncSession = Depends(get_db),
):
    return UnitOfWork(db)


def get_audit_service(
    repository: AuditRepository = Depends(
        get_audit_repository,
    ),
    uow: UnitOfWork = Depends(
        get_uow,
    ),
):
    return AuditService(
        repository,
        uow,
    )