"""
User Management API
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.security import AdminOnly
from app.modules.users.dependencies import (
    get_user_service,
)
from app.modules.users.schemas import (
    UserCreate,
    UserListResponse,
    UserMessage,
    UserResponse,
    UserRoleUpdate,
)
from app.modules.users.service import (
    UserManagementService,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(AdminOnly)],
)


# ==========================================================

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    data: UserCreate,
    service: UserManagementService = Depends(
        get_user_service,
    ),
):
    user = await service.create_user(data)

    return UserResponse.model_validate(user)


# ==========================================================

@router.get(
    "",
    response_model=UserListResponse,
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(
        20,
        ge=1,
        le=100,
    ),
    service: UserManagementService = Depends(
        get_user_service,
    ),
):
    return await service.list_users(
        skip,
        limit,
    )


# ==========================================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: uuid.UUID,
    service: UserManagementService = Depends(
        get_user_service,
    ),
):
    user = await service.get_user(
        user_id,
    )

    return UserResponse.model_validate(user)


# ==========================================================

@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
async def update_role(
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    service: UserManagementService = Depends(
        get_user_service,
    ),
):
    user = await service.update_role(
        user_id,
        data,
    )

    return UserResponse.model_validate(user)


# ==========================================================

@router.patch(
    "/{user_id}/activate",
    response_model=UserMessage,
)
async def activate(
    user_id: uuid.UUID,
    service: UserManagementService = Depends(
        get_user_service,
    ),
):
    await service.activate(user_id)

    return UserMessage(
        message="User activated successfully.",
    )


# ==========================================================

@router.patch(
    "/{user_id}/deactivate",
    response_model=UserMessage,
)
async def deactivate(
    user_id: uuid.UUID,
    service: UserManagementService = Depends(
        get_user_service,
    ),
):
    await service.deactivate(user_id)

    return UserMessage(
        message="User deactivated successfully.",
    )