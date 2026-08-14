"""
User Management Service
"""

from __future__ import annotations

import uuid

from app.core.exceptions import (
    ConflictException,
    ResourceNotFoundException,
)
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.auth.security import hash_password
from app.modules.users.repository import UserManagementRepository
from app.modules.users.schemas import (
    UserCreate,
    UserListResponse,
    UserRoleUpdate,
)


class UserManagementService:

    def __init__(
        self,
        repository: UserManagementRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================

    async def create_user(
        self,
        data: UserCreate,
    ) -> User:

        existing = await self.repository.get_by_email(
            data.email,
        )

        if existing:
            raise ConflictException(
                "Email already registered."
            )

        user = User(
            email=data.email,
            password_hash=hash_password(
                data.password,
            ),
            role=data.role,
            is_active=True,
            is_verified=False,
            is_superuser=data.role.value == "ADMIN",
        )

        async with self.uow:
            return await self.repository.create(user)

    # ==========================================================

    async def list_users(
        self,
        skip: int,
        limit: int,
    ) -> UserListResponse:

        users, total = await self.repository.list_users(
            skip,
            limit,
        )

        return UserListResponse(
            items=users,
            total=total,
        )

    # ==========================================================

    async def get_user(
        self,
        user_id: uuid.UUID,
    ) -> User:

        user = await self.repository.get_by_id(
            user_id,
        )

        if user is None:
            raise ResourceNotFoundException(
                "User"
            )

        return user

    # ==========================================================

    async def update_role(
        self,
        user_id: uuid.UUID,
        data: UserRoleUpdate,
    ) -> User:

        user = await self.get_user(
            user_id,
        )

        async with self.uow:

            user.role = data.role
            user.is_superuser = (
                data.role.value == "ADMIN"
            )

        return user

    # ==========================================================

    async def activate(
        self,
        user_id: uuid.UUID,
    ) -> User:

        user = await self.get_user(
            user_id,
        )

        async with self.uow:
            user.is_active = True

        return user

    # ==========================================================

    async def deactivate(
        self,
        user_id: uuid.UUID,
    ) -> User:

        user = await self.get_user(
            user_id,
        )

        async with self.uow:
            user.is_active = False

        return user