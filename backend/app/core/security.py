"""
AGCT Role-Based Access Control

Authentication and authorization dependencies.
"""

from __future__ import annotations

from fastapi import Depends

from app.common.enums import UserRole
from app.core.exceptions import InvalidCredentialsException
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User


# ==========================================================
# Current Authenticated User
# ==========================================================

async def require_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require a valid authenticated user.
    """
    if not current_user.is_active:
        raise InvalidCredentialsException()

    return current_user


# ==========================================================
# Role Checker
# ==========================================================

def require_roles(*allowed_roles: UserRole):

    async def role_checker(
        current_user: User = Depends(
            require_authenticated_user
        ),
    ) -> User:

        if current_user.role not in allowed_roles:
            raise InvalidCredentialsException()

        return current_user

    return role_checker


# ==========================================================
# Three Roles — Deadline MVP
# ==========================================================

AdminOnly = require_roles(
    UserRole.ADMIN,
)

AdminDoctorReception = require_roles(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.RECEPTIONIST,
)

DoctorOnly = require_roles(
    UserRole.DOCTOR,
)

ReceptionistOnly = require_roles(
    UserRole.RECEPTIONIST,
)

AdminDoctor = require_roles(
    UserRole.ADMIN,
    UserRole.DOCTOR,
)