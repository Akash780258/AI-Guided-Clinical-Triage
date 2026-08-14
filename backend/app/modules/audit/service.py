"""
Audit Service
"""

from __future__ import annotations

import uuid

from app.database.unit_of_work import UnitOfWork
from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import (
    AuditCreate,
    AuditListResponse,
)


class AuditService:
    """
    Audit business logic.
    """

    def __init__(
        self,
        repository: AuditRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Create
    # ==========================================================

    async def create_log(
        self,
        data: AuditCreate,
    ) -> AuditLog:

        audit = AuditLog(
            user_id=data.user_id,
            user_email=data.user_email,
            role=data.role,
            module=data.module,
            action=data.action,
            record_id=data.record_id,
            description=data.description,
            endpoint=data.endpoint,
            http_method=data.http_method,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
        )

        async with self.uow:
            await self.repository.create(audit)

        return audit

    # ==========================================================
    # List
    # ==========================================================

    async def list_logs(
        self,
        skip: int = 0,
        limit: int = 20,
    ) -> AuditListResponse:

        logs = await self.repository.get_paginated(
            skip,
            limit,
        )

        total = await self.repository.total_count()

        return AuditListResponse(
            total=total,
            items=logs,
        )

    # ==========================================================
    # User Logs
    # ==========================================================

    async def get_user_logs(
        self,
        user_id: uuid.UUID,
    ):
        return await self.repository.get_by_user(
            user_id,
        )

    # ==========================================================
    # Module Logs
    # ==========================================================

    async def get_module_logs(
        self,
        module: str,
    ):
        return await self.repository.get_by_module(
            module,
        )

    # ==========================================================
    # Action Logs
    # ==========================================================

    async def get_action_logs(
        self,
        action: str,
    ):
        return await self.repository.get_by_action(
            action,
        )