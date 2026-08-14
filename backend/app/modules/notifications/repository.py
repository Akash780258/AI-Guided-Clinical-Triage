"""
Notification Repository
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.database.base_repository import BaseRepository
from app.modules.notifications.models import Notification


class NotificationRepository(
    BaseRepository[Notification]
):

    def __init__(self, session):
        super().__init__(
            session,
            Notification,
        )

    async def create_notification(
        self,
        notification: Notification,
    ):
        return await self.add(notification)

    async def get_by_uuid(
        self,
        notification_id: uuid.UUID,
    ):

        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id
            )
        )

        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
    ):

        result = await self.session.execute(
            select(Notification)
            .offset(skip)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def total_count(self):

        result = await self.session.execute(
            select(func.count())
            .select_from(Notification)
        )

        return int(result.scalar_one())

    async def get_by_user(
        self,
        user_id: uuid.UUID,
    ):

        result = await self.session.execute(
            select(Notification).where(
                Notification.user_id == user_id
            )
        )

        return list(result.scalars().all())

    async def update_notification(
        self,
        notification: Notification,
        **fields,
    ):

        for key, value in fields.items():
            setattr(notification, key, value)

        await self.flush()
        await self.refresh(notification)

        return notification

    async def delete_notification(
        self,
        notification: Notification,
    ):

        await self.delete(notification)