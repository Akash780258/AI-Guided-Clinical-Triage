"""
Role-Based Access Control (RBAC) utilities for AGCT.

Provides reusable FastAPI dependencies to enforce user roles.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from app.common.enums import UserRole
from app.core.exceptions import AuthorizationException
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User


def require_roles(
    *allowed_roles: UserRole,
) -> Callable:
    """
    Dependency factory that restricts access
    to one or more user roles.

    Example:

        Depends(require_roles(UserRole.ADMIN))

        Depends(
            require_roles(
                UserRole.ADMIN,
                UserRole.DOCTOR,
            )
        )
    """

    async def permission_checker(
        current_user: Annotated[
            User,
            Depends(get_current_active_user),
        ],
    ) -> User:

        if current_user.role not in allowed_roles:
            raise AuthorizationException(
                f"Required role(s): "
                f"{', '.join(role.value for role in allowed_roles)}"
            )

        return current_user

    return permission_checker


# ==========================================================
# Ready-to-use dependencies
# ==========================================================

RequireAdmin = Depends(
    require_roles(UserRole.ADMIN)
)

RequireDoctor = Depends(
    require_roles(UserRole.DOCTOR)
)

RequireNurse = Depends(
    require_roles(UserRole.NURSE)
)

RequireResearcher = Depends(
    require_roles(UserRole.RESEARCHER)
)

RequireMedicalStaff = Depends(
    require_roles(
        UserRole.DOCTOR,
        UserRole.NURSE,
    )
)

RequireClinicalAccess = Depends(
    require_roles(
        UserRole.ADMIN,
        UserRole.DOCTOR,
        UserRole.NURSE,
    )
)