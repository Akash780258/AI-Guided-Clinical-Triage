"""
Notification Service
"""

from __future__ import annotations

import uuid

from app.core.exceptions import ResourceNotFoundException
from app.database.unit_of_work import UnitOfWork
from app.modules.notifications.models import Notification
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import (
    NotificationCreate,
    NotificationListResponse,
    NotificationUpdate,
)


class NotificationService:

    def __init__(
        self,
        repository: NotificationRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Create
    # ==========================================================

    async def create_notification(
        self,
        *,
        data: NotificationCreate,
    ) -> Notification:

        notification = Notification(
            user_id=data.user_id,
            title=data.title,
            message=data.message,
            notification_type=data.notification_type,
        )

        async with self.uow:
            await self.repository.create_notification(
                notification,
            )

        return notification

    # ==========================================================
    # List
    # ==========================================================

    async def list_notifications(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> NotificationListResponse:

        notifications = await self.repository.get_paginated(
            skip=skip,
            limit=limit,
        )

        total = await self.repository.total_count()

        return NotificationListResponse(
            total=total,
            items=notifications,
        )

    # ==========================================================
    # Get
    # ==========================================================

    async def get_notification(
        self,
        notification_id: uuid.UUID,
    ) -> Notification:

        notification = await self.repository.get_by_uuid(
            notification_id,
        )

        if notification is None:
            raise ResourceNotFoundException(
                "Notification"
            )

        return notification

    # ==========================================================
    # User Notifications
    # ==========================================================

    async def get_user_notifications(
        self,
        user_id: uuid.UUID,
    ):

        return await self.repository.get_by_user(
            user_id,
        )

    # ==========================================================
    # Update
    # ==========================================================

    async def update_notification(
        self,
        *,
        notification_id: uuid.UUID,
        data: NotificationUpdate,
    ) -> Notification:

        notification = await self.get_notification(
            notification_id,
        )

        async with self.uow:

            notification = await self.repository.update_notification(
                notification,
                **data.model_dump(
                    exclude_unset=True,
                ),
            )

        return notification

    # ==========================================================
    # Delete
    # ==========================================================

    async def delete_notification(
        self,
        notification_id: uuid.UUID,
    ):

        notification = await self.get_notification(
            notification_id,
        )

        async with self.uow:
            await self.repository.delete_notification(
                notification,
            )