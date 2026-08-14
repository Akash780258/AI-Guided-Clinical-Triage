"""
User Management Schemas
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.enums import UserRole


# ==========================================================
# Create User
# ==========================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole


# ==========================================================
# Update Role
# ==========================================================

class UserRoleUpdate(BaseModel):
    role: UserRole


# ==========================================================
# User Response
# ==========================================================

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: UserRole
    is_active: bool
    is_verified: bool
    is_superuser: bool


# ==========================================================
# User List
# ==========================================================

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


# ==========================================================
# Message
# ==========================================================

class UserMessage(BaseModel):
    message: str