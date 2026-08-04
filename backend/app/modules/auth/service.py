"""
Authentication Service

Contains all authentication business logic.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from jose import JWTError

from app.common.enums import UserRole
from app.core.exceptions import (
    ConflictException,
    InvalidCredentialsException,
    InvalidTokenException,
    ResourceNotFoundException,
)
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    PasswordChangeRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserRegister,
)
from app.modules.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthService:
    """
    Handles authentication business logic.
    """

    def __init__(
        self,
        repository: UserRepository,
        uow: UnitOfWork,
    ):
        self.repository = repository
        self.uow = uow

    # ==========================================================
    # Register
    # ==========================================================

    async def register(
        self,
        data: UserRegister,
    ) -> User:

        if await self.repository.email_exists(data.email):
            raise ConflictException(
                "Email is already registered."
            )

        async with self.uow:

            user = await self.repository.create_user(
                email=data.email,
                password_hash=hash_password(data.password),
                role=UserRole.DOCTOR,
            )

        return user

    # ==========================================================
    # Login
    # ==========================================================

    async def login(
        self,
        *,
        email: str,
        password: str,
    ) -> TokenResponse:

        user = await self.repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsException()

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise InvalidCredentialsException()

        if not user.is_active:
            raise InvalidCredentialsException()

        async with self.uow:

            await self.repository.update_last_login(
                user,
                datetime.now(UTC),
            )

        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role.value,
            },
        )

        refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    # ==========================================================
    # Refresh Token
    # ==========================================================

    async def refresh_access_token(
        self,
        request: RefreshTokenRequest,
    ) -> TokenResponse:

        try:
            payload = decode_token(request.refresh_token)

        except JWTError as exc:
            raise InvalidTokenException() from exc

        if payload["type"] != "refresh":
            raise InvalidTokenException()

        user = await self.repository.get_by_id(
            uuid.UUID(payload["sub"])
        )

        if user is None:
            raise ResourceNotFoundException("User not found.")

        if not user.is_active:
            raise InvalidCredentialsException()

        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role.value,
            },
        )

        refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ==========================================================
    # Current User
    # ==========================================================

    async def get_current_user(
        self,
        token: str,
    ) -> User:

        try:
            payload = decode_token(token)

        except JWTError as exc:
            raise InvalidTokenException() from exc

        if payload["type"] != "access":
            raise InvalidTokenException()

        user = await self.repository.get_by_id(
            uuid.UUID(payload["sub"])
        )

        if user is None:
            raise ResourceNotFoundException("User not found.")

        if not user.is_active:
            raise InvalidCredentialsException()

        return user

    # ==========================================================
    # Change Password
    # ==========================================================

    async def change_password(
        self,
        *,
        user: User,
        request: PasswordChangeRequest,
    ) -> User:

        if not verify_password(
            request.current_password,
            user.password_hash,
        ):
            raise InvalidCredentialsException()

        async with self.uow:

            await self.repository.update_password(
                user,
                hash_password(request.new_password),
            )

        return user

    # ==========================================================
    # Verify Email
    # ==========================================================

    async def verify_email(
        self,
        user: User,
    ) -> User:

        async with self.uow:

            await self.repository.verify_email(user)

        return user

    # ==========================================================
    # Activate User
    # ==========================================================

    async def activate_user(
        self,
        user: User,
    ) -> User:

        async with self.uow:

            await self.repository.activate(user)

        return user

    # ==========================================================
    # Deactivate User
    # ==========================================================

    async def deactivate_user(
        self,
        user: User,
    ) -> User:

        async with self.uow:

            await self.repository.deactivate(user)

        return users