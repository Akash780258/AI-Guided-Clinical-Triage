"""
Notification Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationCreate(BaseModel):
    user_id: uuid.UUID
    title: str
    message: str
    notification_type: str


class NotificationUpdate(BaseModel):
    is_read: bool


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class NotificationListResponse(BaseModel):
    total: int
    items: list[NotificationResponse]


class NotificationMessage(BaseModel):
    message: str