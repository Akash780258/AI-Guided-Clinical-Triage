"""
Generic Base Repository for AGCT.

Provides reusable CRUD operations for SQLAlchemy ORM models.

Notes:
- Uses SQLAlchemy 2.0 async API.
- Does NOT commit transactions.
- Transaction management belongs to UnitOfWork.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """
    Generic repository for SQLAlchemy models.
    """

    def __init__(
        self,
        session: AsyncSession,
        model: type[ModelType],
    ):
        self.session = session
        self.model = model

    # ==========================================================
    # CREATE
    # ==========================================================

    async def add(
        self,
        entity: ModelType,
    ) -> ModelType:
        """
        Add an entity to the current transaction.
        """

        self.session.add(entity)

        await self.session.flush()

        return entity

    # ==========================================================
    # READ
    # ==========================================================

    async def get_by_id(
        self,
        entity_id: uuid.UUID,
    ) -> ModelType | None:
        stmt = select(self.model).where(
            self.model.id == entity_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all(self) -> list[ModelType]:
        stmt = select(self.model)

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def first(
        self,
        **filters: Any,
    ) -> ModelType | None:
        stmt = select(self.model).filter_by(**filters)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def list(
        self,
        **filters: Any,
    ) -> list[ModelType]:
        stmt = select(self.model).filter_by(**filters)

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def exists(
        self,
        **filters: Any,
    ) -> bool:
        stmt = (
            select(func.count())
            .select_from(self.model)
            .filter_by(**filters)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one() > 0

    async def count(
        self,
        **filters: Any,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(self.model)
            .filter_by(**filters)
        )

        result = await self.session.execute(stmt)

        return int(result.scalar_one())

    # ==========================================================
    # UPDATE
    # ==========================================================

    async def flush(self):
        """
        Flush pending changes.
        """
        await self.session.flush()

    async def refresh(
        self,
        entity: ModelType,
    ):
        """
        Refresh ORM entity.
        """
        await self.session.refresh(entity)

    # ==========================================================
    # DELETE
    # ==========================================================

    async def delete(
        self,
        entity: ModelType,
    ):
        await self.session.delete(entity)

    async def delete_by_id(
        self,
        entity_id: uuid.UUID,
    ):
        stmt = delete(self.model).where(
            self.model.id == entity_id
        )

        await self.session.execute(stmt)