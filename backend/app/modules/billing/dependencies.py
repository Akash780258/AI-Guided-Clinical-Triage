"""
Billing Dependencies

Dependency injection for Billing module.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.billing.repository import BillingRepository
from app.modules.billing.service import BillingService


# ==========================================================
# Repository
# ==========================================================

def get_billing_repository(
    db: AsyncSession = Depends(get_db),
) -> BillingRepository:
    return BillingRepository(db)


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

def get_billing_service(
    repository: BillingRepository = Depends(
        get_billing_repository,
    ),
    uow: UnitOfWork = Depends(get_uow),
) -> BillingService:

    return BillingService(
        repository=repository,
        uow=uow,
    )