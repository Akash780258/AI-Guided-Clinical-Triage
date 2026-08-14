"""
Authentication Schemas

Pydantic models for:

- User Registration
- JWT Tokens
- User Response
- Refresh Token
- Password Change
"""

from __future__ import annotations

import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

from app.common.enums import UserRole


# ==========================================================
# Base User
# ==========================================================

class UserBase(BaseModel):
    email: EmailStr


# ==========================================================
# Register
# ==========================================================

# ==========================================================
# Register
# ==========================================================



# ==========================================================
# Refresh Token
# ==========================================================

class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ==========================================================
# Token Response
# ==========================================================

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ==========================================================
# JWT Payload
# ==========================================================

class TokenPayload(BaseModel):
    sub: str
    type: str
    exp: int
    iat: int | None = None


# ==========================================================
# User Response
# ==========================================================

class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    email: EmailStr
    role: UserRole
    is_active: bool
    is_verified: bool
    is_superuser: bool


# ==========================================================
# Public User
# ==========================================================

class UserPublic(UserResponse):
    """
    Safe user information returned to clients.
    """
    pass


# ==========================================================
# Message Response
# ==========================================================

class MessageResponse(BaseModel):
    message: str


# ==========================================================
# Change Password
# ==========================================================

class PasswordChangeRequest(BaseModel):
    current_password: str

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str):

        if not any(c.isupper() for c in value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not any(c.islower() for c in value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not any(c.isdigit() for c in value):
            raise ValueError(
                "Password must contain at least one digit."
            )

        return value