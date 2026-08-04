"""
User Repository

Handles all database operations related to User.

Business logic does NOT belong here.
Transactions are managed by UnitOfWork.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base_repository import BaseRepository
from app.modules.auth.models import User


class UserRepository(BaseRepository[User]):
    """
    Repository for User model.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    # ==========================================================
    # User Queries
    # ==========================================================

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        """
        Get a user by email.
        """

        stmt = (
            select(User)
            .where(User.email == email)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def email_exists(
        self,
        email: str,
    ) -> bool:
        """
        Check if an email already exists.
        """

        return await self.exists(email=email)

    async def activate(
        self,
        user: User,
    ) -> User:
        """
        Activate a user account.
        """

        user.is_active = True

        await self.flush()

        return user

    async def deactivate(
        self,
        user: User,
    ) -> User:
        """
        Deactivate a user account.
        """

        user.is_active = False

        await self.flush()

        return user

    async def verify_email(
        self,
        user: User,
    ) -> User:
        """
        Mark user email as verified.
        """

        user.is_verified = True

        await self.flush()

        return user

    async def update_last_login(
        self,
        user: User,
        timestamp,
    ) -> User:
        """
        Update last login timestamp.
        """

        user.last_login = timestamp

        await self.flush()

        return user

    async def update_password(
        self,
        user: User,
        password_hash: str,
    ) -> User:
        """
        Update password hash.
        """

        user.password_hash = password_hash

        await self.flush()

        return user

    async def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        role,
    ) -> User:
        """
        Create a new user.

        Transaction is NOT committed here.
        """

        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
        )

        await self.add(user)

        return user

    async def get_by_uuid(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        """
        Alias for get_by_id().
        """

        return await self.get_by_id(user_id)