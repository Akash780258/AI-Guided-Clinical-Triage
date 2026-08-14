"""
Billing Repository

Handles all database operations related to Billing.
"""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.billing.models import Billing


class BillingRepository(BaseRepository[Billing]):
    """
    Repository for Billing model.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(
            session,
            Billing,
        )

    # ==========================================================
    # Create
    # ==========================================================

    async def create_billing(
        self,
        billing: Billing,
    ) -> Billing:

        return await self.add(
            billing,
        )

    # ==========================================================
    # Read
    # ==========================================================

    async def get_by_uuid(
        self,
        billing_id: uuid.UUID,
    ) -> Billing | None:

        stmt = (
            select(Billing)
            .where(
                Billing.id == billing_id,
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def get_by_bill_number(
        self,
        bill_number: str,
    ) -> Billing | None:

        stmt = (
            select(Billing)
            .where(
                Billing.bill_number == bill_number,
                Billing.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def get_last_bill_number(
        self,
    ) -> str | None:

        stmt = (
            select(
                Billing.bill_number,
            )
            .order_by(
                desc(
                    Billing.bill_number,
                )
            )
            .limit(1)
        )

        result = await self.session.execute(
            stmt,
        )

        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Billing]:

        stmt = (
            select(Billing)
            .where(
                Billing.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
        )

        result = await self.session.execute(
            stmt,
        )

        return list(
            result.scalars().all()
        )

    async def get_by_patient(
        self,
        patient_id: uuid.UUID,
    ) -> list[Billing]:

        stmt = (
            select(Billing)
            .where(
                Billing.patient_id == patient_id,
                Billing.deleted_at.is_(None),
            )
            .order_by(
                Billing.created_at.desc(),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return list(
            result.scalars().all()
        )

    async def total_count(
        self,
    ) -> int:

        stmt = (
            select(func.count())
            .select_from(Billing)
            .where(
                Billing.deleted_at.is_(None),
            )
        )

        result = await self.session.execute(
            stmt,
        )

        return int(
            result.scalar_one()
        )

    # ==========================================================
    # Update
    # ==========================================================

    async def update_billing(
        self,
        billing: Billing,
        **fields,
    ) -> Billing:

        for key, value in fields.items():
            if value is not None:
                setattr(
                    billing,
                    key,
                    value,
                )

        await self.flush()
        await self.refresh(
            billing,
        )

        return billing

    # ==========================================================
    # Soft Delete
    # ==========================================================

    async def soft_delete(
        self,
        billing: Billing,
    ) -> Billing:

        from datetime import UTC, datetime

        billing.deleted_at = datetime.now(
            UTC,
        )

        await self.flush()
        await self.refresh(
            billing,
        )

        return billing