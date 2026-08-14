"""
Notification Dependencies
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.service import NotificationService


def get_notification_service(
    db: AsyncSession = Depends(get_db),
):
    repository = NotificationRepository(db)
    uow = UnitOfWork(db)

    return NotificationService(
        repository=repository,
        uow=uow,
    )