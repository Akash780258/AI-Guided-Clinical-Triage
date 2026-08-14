"""
Audit Repository
"""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog


class AuditRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    # ==========================================================
    # Create
    # ==========================================================

    async def create(
        self,
        audit: AuditLog,
    ) -> AuditLog:

        self.db.add(audit)

        await self.db.flush()
        await self.db.refresh(audit)

        return audit

    # ==========================================================
    # List
    # ==========================================================

    async def get_paginated(
        self,
        skip: int = 0,
        limit: int = 20,
    ):

        result = await self.db.execute(
            select(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .offset(skip)
            .limit(limit)
        )

        return result.scalars().all()

    async def total_count(
        self,
    ) -> int:

        return (
            await self.db.scalar(
                select(func.count(AuditLog.id))
            )
        ) or 0

    # ==========================================================
    # User Logs
    # ==========================================================

    async def get_by_user(
        self,
        user_id: uuid.UUID,
    ):

        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.user_id == user_id,
            )
            .order_by(
                desc(AuditLog.created_at),
            )
        )

        return result.scalars().all()

    # ==========================================================
    # Module Logs
    # ==========================================================

    async def get_by_module(
        self,
        module: str,
    ):

        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.module == module,
            )
            .order_by(
                desc(AuditLog.created_at),
            )
        )

        return result.scalars().all()

    # ==========================================================
    # Action Logs
    # ==========================================================

    async def get_by_action(
        self,
        action: str,
    ):

        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.action == action,
            )
            .order_by(
                desc(AuditLog.created_at),
            )
        )

        return result.scalars().all()