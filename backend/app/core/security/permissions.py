"""
Role-Based Access Control (RBAC)

Provides reusable role-based authorization dependencies.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends

from app.common.enums import UserRole
from app.core.exceptions import AuthorizationException
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User


# ==========================================================
# Require Roles
# ==========================================================

def require_roles(
    *roles: UserRole,
) -> Callable:
    """
    Restrict endpoint access to the specified roles.
    """

    async def permission(
        current_user: User = Depends(
            get_current_user,
        ),
    ) -> User:

        if current_user.role not in roles:
            raise AuthorizationException(
                "You do not have permission to perform this action."
            )

        return current_user

    return permission


# ==========================================================
# Common Role Groups
# ==========================================================

AdminOnly = require_roles(
    UserRole.ADMIN,
)

DoctorOnly = require_roles(
    UserRole.DOCTOR,
)

ReceptionOnly = require_roles(
    UserRole.RECEPTIONIST,
)

PharmacyOnly = require_roles(
    UserRole.PHARMACIST,
)

LaboratoryOnly = require_roles(
    UserRole.LAB_TECHNICIAN,
)

ResearchOnly = require_roles(
    UserRole.RESEARCHER,
)

AdminOrDoctor = require_roles(
    UserRole.ADMIN,
    UserRole.DOCTOR,
)

AdminOrReception = require_roles(
    UserRole.ADMIN,
    UserRole.RECEPTIONIST,
)

AdminDoctorReception = require_roles(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.RECEPTIONIST,
)

AdminDoctorResearch = require_roles(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.RESEARCHER,
)

AdminResearch = require_roles(
    UserRole.ADMIN,
    UserRole.RESEARCHER,
)

AdminPharmacy = require_roles(
    UserRole.ADMIN,
    UserRole.PHARMACIST,
)

AdminLaboratory = require_roles(
    UserRole.ADMIN,
    UserRole.LAB_TECHNICIAN,
)