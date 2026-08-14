"""
Notification API
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.modules.notifications.dependencies import (
    get_notification_service,
)
from app.modules.notifications.schemas import (
    NotificationCreate,
    NotificationListResponse,
    NotificationMessage,
    NotificationResponse,
    NotificationUpdate,
)
from app.modules.notifications.service import (
    NotificationService,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    data: NotificationCreate,
    service: NotificationService = Depends(
        get_notification_service,
    ),
):
    notification = await service.create_notification(
        data=data,
    )

    return NotificationResponse.model_validate(
        notification,
    )


@router.get(
    "",
    response_model=NotificationListResponse,
)
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: NotificationService = Depends(
        get_notification_service,
    ),
):
    return await service.list_notifications(
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(
        get_notification_service,
    ),
):
    notification = await service.get_notification(
        notification_id,
    )

    return NotificationResponse.model_validate(
        notification,
    )


@router.get(
    "/user/{user_id}",
    response_model=list[NotificationResponse],
)
async def get_user_notifications(
    user_id: uuid.UUID,
    service: NotificationService = Depends(
        get_notification_service,
    ),
):
    notifications = await service.get_user_notifications(
        user_id,
    )

    return [
        NotificationResponse.model_validate(
            notification,
        )
        for notification in notifications
    ]


@router.put(
    "/{notification_id}",
    response_model=NotificationResponse,
)
async def update_notification(
    notification_id: uuid.UUID,
    data: NotificationUpdate,
    service: NotificationService = Depends(
        get_notification_service,
    ),
):
    notification = await service.update_notification(
        notification_id=notification_id,
        data=data,
    )

    return NotificationResponse.model_validate(
        notification,
    )


@router.delete(
    "/{notification_id}",
    response_model=NotificationMessage,
)
async def delete_notification(
    notification_id: uuid.UUID,
    service: NotificationService = Depends(
        get_notification_service,
    ),
):
    await service.delete_notification(
        notification_id,
    )

    return NotificationMessage(
        message="Notification deleted successfully."
    )