"""
Audit Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.common.enums import UserRole


class AuditCreate(BaseModel):
    user_id: uuid.UUID
    user_email: str
    role: UserRole

    module: str
    action: str

    record_id: str | None = None

    description: str

    endpoint: str | None = None
    http_method: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None


class AuditResponse(BaseModel):
    id: uuid.UUID

    user_id: uuid.UUID
    user_email: str
    role: UserRole

    module: str
    action: str

    record_id: str | None

    description: str

    endpoint: str | None
    http_method: str | None
    ip_address: str | None
    user_agent: str | None

    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class AuditListResponse(BaseModel):
    total: int
    items: list[AuditResponse]