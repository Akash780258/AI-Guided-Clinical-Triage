"""
Authentication Dependencies

Dependency injection for:

- Database Session
- User Repository
- Unit Of Work
- Auth Service
- Current User
"""

from __future__ import annotations

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.database.unit_of_work import UnitOfWork
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService

# ==========================================================
# OAuth2
# ==========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


# ==========================================================
# Repository
# ==========================================================

def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> UserRepository:
    """
    Returns UserRepository.
    """
    return UserRepository(db)


# ==========================================================
# Unit Of Work
# ==========================================================

def get_uow(
    db: AsyncSession = Depends(get_db),
) -> UnitOfWork:
    """
    Returns UnitOfWork.
    """
    return UnitOfWork(db)


# ==========================================================
# Auth Service
# ==========================================================

def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
    uow: UnitOfWork = Depends(get_uow),
) -> AuthService:
    """
    Returns AuthService.
    """
    return AuthService(
        repository=repository,
        uow=uow,
    )


# ==========================================================
# Current User
# ==========================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
):
    """
    Returns the authenticated user from the JWT access token.
    """
    return await service.get_current_user(token)